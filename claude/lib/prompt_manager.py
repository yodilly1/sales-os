"""
Prompt Manager

Central management system for Claude AI prompts. Handles loading, caching,
versioning, and template rendering for all prompt templates.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from claude.lib.prompt_version import PromptMetadata, PromptVersion, VersionBump
from claude.lib.template_engine import TemplateEngine


class PromptLoadError(Exception):
    """Raised when a prompt cannot be loaded."""
    pass


class PromptNotFoundError(Exception):
    """Raised when a requested prompt doesn't exist."""
    pass


class PromptManager:
    """
    Manages Claude AI prompt templates for the Sales OS platform.

    Features:
    - Load prompts from markdown files
    - Template variable substitution
    - Version tracking and management
    - Prompt caching for performance
    - Metadata extraction and validation

    Usage:
        manager = PromptManager("/path/to/prompts")
        prompt = manager.get_prompt("spiced_extraction", variables={"transcript": "..."})
    """

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
    VERSIONS_FILE = "prompt_versions.json"

    # Regex patterns for parsing prompt files
    METADATA_PATTERN = re.compile(
        r"^\*\*Version:\*\*\s*(.+)$",
        re.MULTILINE
    )
    SYSTEM_PROMPT_PATTERN = re.compile(
        r"## System Prompt\s*```\s*(.*?)```",
        re.DOTALL
    )
    USER_PROMPT_PATTERN = re.compile(
        r"## User Prompt Template\s*```\s*(.*?)```",
        re.DOTALL
    )

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt manager.

        Args:
            prompts_dir: Directory containing prompt markdown files.
                        Defaults to /claude/prompts/
        """
        self.prompts_dir = prompts_dir or self.PROMPTS_DIR
        self._cache: dict[str, dict] = {}
        self._versions: dict[str, PromptVersion] = {}
        self._template_engine = TemplateEngine()
        self._load_versions()

    def _load_versions(self) -> None:
        """Load version information from disk."""
        versions_path = self.prompts_dir / self.VERSIONS_FILE
        if versions_path.exists():
            with open(versions_path, "r") as f:
                data = json.load(f)
                for name, version_data in data.items():
                    self._versions[name] = PromptVersion.from_dict(version_data)

    def _save_versions(self) -> None:
        """Persist version information to disk."""
        versions_path = self.prompts_dir / self.VERSIONS_FILE
        data = {
            name: version.to_dict()
            for name, version in self._versions.items()
        }
        with open(versions_path, "w") as f:
            json.dump(data, f, indent=2)

    def list_prompts(self) -> list[str]:
        """
        List all available prompt names.

        Returns:
            List of prompt names (without .md extension)
        """
        prompts = []
        for path in self.prompts_dir.glob("*.md"):
            if path.stem != "README":
                prompts.append(path.stem)
        return sorted(prompts)

    def get_prompt_path(self, name: str) -> Path:
        """
        Get the file path for a prompt.

        Args:
            name: Prompt name (without .md extension)

        Returns:
            Path to the prompt file

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        path = self.prompts_dir / f"{name}.md"
        if not path.exists():
            raise PromptNotFoundError(
                f"Prompt '{name}' not found at {path}"
            )
        return path

    def load_prompt(self, name: str, force_reload: bool = False) -> dict:
        """
        Load a prompt from disk.

        Args:
            name: Prompt name
            force_reload: Bypass cache and reload from disk

        Returns:
            Dictionary containing prompt components
        """
        if not force_reload and name in self._cache:
            return self._cache[name]

        path = self.get_prompt_path(name)
        content = path.read_text()

        prompt_data = self._parse_prompt_file(name, content)
        self._cache[name] = prompt_data

        return prompt_data

    def _parse_prompt_file(self, name: str, content: str) -> dict:
        """
        Parse a prompt markdown file into components.

        Args:
            name: Prompt name
            content: File content

        Returns:
            Parsed prompt data
        """
        # Extract version
        version_match = self.METADATA_PATTERN.search(content)
        version = version_match.group(1).strip() if version_match else "1.0.0"

        # Extract system prompt
        system_match = self.SYSTEM_PROMPT_PATTERN.search(content)
        system_prompt = system_match.group(1).strip() if system_match else ""

        # Extract user prompt template
        user_match = self.USER_PROMPT_PATTERN.search(content)
        user_template = user_match.group(1).strip() if user_match else ""

        # Extract category from content
        category_match = re.search(r"\*\*Category:\*\*\s*(.+)$", content, re.MULTILINE)
        category = category_match.group(1).strip() if category_match else "general"

        # Initialize version tracking if needed
        if name not in self._versions:
            self._versions[name] = PromptVersion(version)

        return {
            "name": name,
            "version": version,
            "category": category,
            "system_prompt": system_prompt,
            "user_template": user_template,
            "raw_content": content,
        }

    def get_prompt(
        self,
        name: str,
        variables: Optional[dict[str, Any]] = None,
        include_system: bool = True,
    ) -> dict[str, str]:
        """
        Get a prompt with variables substituted.

        Args:
            name: Prompt name
            variables: Variables to substitute in templates
            include_system: Include system prompt in response

        Returns:
            Dictionary with 'system' and 'user' prompt strings
        """
        prompt_data = self.load_prompt(name)
        variables = variables or {}

        result = {}

        if include_system:
            result["system"] = self._template_engine.render(
                prompt_data["system_prompt"],
                variables
            )

        result["user"] = self._template_engine.render(
            prompt_data["user_template"],
            variables
        )

        result["version"] = prompt_data["version"]
        result["name"] = name

        return result

    def get_system_prompt(self, name: str) -> str:
        """
        Get only the system prompt for a template.

        Args:
            name: Prompt name

        Returns:
            System prompt string
        """
        prompt_data = self.load_prompt(name)
        return prompt_data["system_prompt"]

    def get_user_template(
        self,
        name: str,
        variables: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Get the user prompt with variables substituted.

        Args:
            name: Prompt name
            variables: Variables to substitute

        Returns:
            Rendered user prompt string
        """
        prompt_data = self.load_prompt(name)
        return self._template_engine.render(
            prompt_data["user_template"],
            variables or {}
        )

    def get_version(self, name: str) -> PromptVersion:
        """
        Get version info for a prompt.

        Args:
            name: Prompt name

        Returns:
            PromptVersion instance
        """
        self.load_prompt(name)  # Ensure prompt is loaded
        return self._versions.get(name, PromptVersion("1.0.0"))

    def bump_version(
        self,
        name: str,
        bump_type: VersionBump,
        changes: str,
        author: str = "system"
    ) -> str:
        """
        Increment the version of a prompt.

        Args:
            name: Prompt name
            bump_type: Type of version bump
            changes: Description of changes
            author: Author of changes

        Returns:
            New version string
        """
        prompt_data = self.load_prompt(name, force_reload=True)
        version = self._versions.get(name, PromptVersion("1.0.0"))

        new_version = version.bump(bump_type)
        version.add_history_entry(changes, prompt_data["raw_content"], author)

        self._versions[name] = version
        self._save_versions()

        return new_version

    def get_metadata(self, name: str) -> PromptMetadata:
        """
        Get metadata for a prompt.

        Args:
            name: Prompt name

        Returns:
            PromptMetadata instance
        """
        prompt_data = self.load_prompt(name)
        version = self.get_version(name)

        path = self.get_prompt_path(name)
        stat = path.stat()

        return PromptMetadata(
            name=name,
            version=version.version,
            category=prompt_data["category"],
            description=f"Prompt template for {name}",
            created_at=datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime),
        )

    def validate_prompt(self, name: str) -> dict[str, Any]:
        """
        Validate a prompt template.

        Args:
            name: Prompt name

        Returns:
            Validation results with any issues found
        """
        issues = []
        warnings = []

        try:
            prompt_data = self.load_prompt(name, force_reload=True)
        except PromptNotFoundError:
            return {
                "valid": False,
                "issues": [f"Prompt '{name}' not found"],
                "warnings": [],
            }
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Failed to load prompt: {str(e)}"],
                "warnings": [],
            }

        # Check for required components
        if not prompt_data.get("system_prompt"):
            issues.append("Missing system prompt")

        if not prompt_data.get("user_template"):
            warnings.append("No user template defined")

        # Check for template variables
        system_vars = self._template_engine.extract_variables(
            prompt_data.get("system_prompt", "")
        )
        user_vars = self._template_engine.extract_variables(
            prompt_data.get("user_template", "")
        )

        all_vars = system_vars | user_vars
        if all_vars:
            warnings.append(f"Template requires variables: {', '.join(sorted(all_vars))}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "variables_required": sorted(all_vars),
            "version": prompt_data.get("version", "1.0.0"),
        }

    def clear_cache(self, name: Optional[str] = None) -> None:
        """
        Clear cached prompts.

        Args:
            name: Specific prompt to clear, or None for all
        """
        if name:
            self._cache.pop(name, None)
        else:
            self._cache.clear()

    def export_prompt(self, name: str, format: str = "json") -> str:
        """
        Export a prompt in specified format.

        Args:
            name: Prompt name
            format: Export format ('json' or 'markdown')

        Returns:
            Exported content string
        """
        prompt_data = self.load_prompt(name)
        metadata = self.get_metadata(name)

        if format == "json":
            export_data = {
                "metadata": metadata.to_dict(),
                "system_prompt": prompt_data["system_prompt"],
                "user_template": prompt_data["user_template"],
            }
            return json.dumps(export_data, indent=2)
        else:
            return prompt_data["raw_content"]
