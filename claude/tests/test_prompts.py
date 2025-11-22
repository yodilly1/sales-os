"""
Prompt Unit Tests

Pytest-compatible test cases for validating Claude AI prompts.
Run with: pytest claude/tests/test_prompts.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.lib.prompt_manager import PromptManager, PromptNotFoundError
from claude.lib.prompt_version import PromptVersion, VersionBump
from claude.lib.template_engine import TemplateEngine, TemplateError


class TestPromptVersion:
    """Tests for PromptVersion class."""

    def test_version_creation(self):
        """Test creating a version."""
        version = PromptVersion("1.0.0")
        assert version.version == "1.0.0"
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_version_invalid_format(self):
        """Test invalid version format raises error."""
        with pytest.raises(ValueError):
            PromptVersion("1.0")

        with pytest.raises(ValueError):
            PromptVersion("invalid")

    def test_version_bump_patch(self):
        """Test patch version bump."""
        version = PromptVersion("1.0.0")
        new = version.bump(VersionBump.PATCH)
        assert new == "1.0.1"

    def test_version_bump_minor(self):
        """Test minor version bump resets patch."""
        version = PromptVersion("1.2.3")
        new = version.bump(VersionBump.MINOR)
        assert new == "1.3.0"

    def test_version_bump_major(self):
        """Test major version bump resets minor and patch."""
        version = PromptVersion("1.2.3")
        new = version.bump(VersionBump.MAJOR)
        assert new == "2.0.0"

    def test_version_comparison(self):
        """Test version comparison."""
        version = PromptVersion("2.0.0")
        assert version.compare_versions("1.0.0") == 1  # this > other
        assert version.compare_versions("2.0.0") == 0  # equal
        assert version.compare_versions("3.0.0") == -1  # this < other

    def test_version_history(self):
        """Test version history tracking."""
        version = PromptVersion("1.0.0")
        version.add_history_entry("Initial release", "content here")

        assert len(version.history) == 1
        assert version.history[0].version == "1.0.0"
        assert version.history[0].changes == "Initial release"

    def test_content_change_detection(self):
        """Test content change detection."""
        version = PromptVersion("1.0.0")
        version.add_history_entry("Initial", "original content")

        assert version.has_content_changed("different content") is True
        assert version.has_content_changed("original content") is False

    def test_serialization(self):
        """Test version serialization/deserialization."""
        version = PromptVersion("1.2.3")
        version.add_history_entry("Test change", "test content")

        data = version.to_dict()
        restored = PromptVersion.from_dict(data)

        assert restored.version == "1.2.3"
        assert len(restored.history) == 1


class TestTemplateEngine:
    """Tests for TemplateEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TemplateEngine()

    def test_basic_variable_substitution(self):
        """Test basic variable replacement."""
        template = "Hello {{name}}!"
        result = self.engine.render(template, {"name": "World"})
        assert result == "Hello World!"

    def test_multiple_variables(self):
        """Test multiple variable replacement."""
        template = "{{greeting}} {{name}}, welcome to {{place}}!"
        result = self.engine.render(template, {
            "greeting": "Hello",
            "name": "Alice",
            "place": "Sales OS"
        })
        assert result == "Hello Alice, welcome to Sales OS!"

    def test_optional_variable_present(self):
        """Test optional variable when present."""
        template = "Hello{{name?}}!"
        result = self.engine.render(template, {"name": " World"})
        assert result == "Hello World!"

    def test_optional_variable_missing(self):
        """Test optional variable when missing."""
        template = "Hello{{name?}}!"
        result = self.engine.render(template, {})
        assert result == "Hello!"

    def test_default_value(self):
        """Test default value for missing variable."""
        template = "Hello {{name|Guest}}!"
        result = self.engine.render(template, {})
        assert result == "Hello Guest!"

    def test_filter_upper(self):
        """Test upper filter."""
        template = "{{name|upper}}"
        result = self.engine.render(template, {"name": "hello"})
        assert result == "HELLO"

    def test_filter_lower(self):
        """Test lower filter."""
        template = "{{name|lower}}"
        result = self.engine.render(template, {"name": "HELLO"})
        assert result == "hello"

    def test_conditional_true(self):
        """Test conditional block when true."""
        template = "{{#if show}}Visible{{/if}}"
        result = self.engine.render(template, {"show": True})
        assert result == "Visible"

    def test_conditional_false(self):
        """Test conditional block when false."""
        template = "{{#if show}}Visible{{/if}}"
        result = self.engine.render(template, {"show": False})
        assert result == ""

    def test_each_loop(self):
        """Test each loop."""
        template = "Items: {{#each items}}{{.}}, {{/each}}"
        result = self.engine.render(template, {"items": ["a", "b", "c"]})
        assert result == "Items: a, b, c, "

    def test_each_empty(self):
        """Test each loop with empty list."""
        template = "Items: {{#each items}}{{.}}{{/each}}"
        result = self.engine.render(template, {"items": []})
        assert result == "Items: "

    def test_extract_variables(self):
        """Test variable extraction."""
        template = "{{a}} and {{b}} and {{#if c}}{{d}}{{/if}}"
        vars = self.engine.extract_variables(template)
        assert vars == {"a", "b", "c", "d"}

    def test_validate_valid_template(self):
        """Test validation of valid template."""
        template = "{{name}} {{#if show}}text{{/if}}"
        result = self.engine.validate_template(template)
        assert result["valid"] is True
        assert "name" in result["variables"]

    def test_validate_mismatched_blocks(self):
        """Test validation catches mismatched blocks."""
        template = "{{#if show}}text"
        result = self.engine.validate_template(template)
        assert result["valid"] is False
        assert any("Mismatched" in issue for issue in result["issues"])

    def test_strict_mode_error(self):
        """Test strict mode raises on missing variable."""
        template = "Hello {{name}}!"
        with pytest.raises(TemplateError):
            self.engine.render(template, {}, strict=True)

    def test_preview_generation(self):
        """Test preview with placeholder values."""
        template = "Hello {{name}}!"
        result = self.engine.preview(template)
        assert result == "Hello [name]!"


class TestPromptManager:
    """Tests for PromptManager class."""

    @pytest.fixture
    def manager(self):
        """Create a PromptManager instance."""
        return PromptManager()

    def test_list_prompts(self, manager):
        """Test listing available prompts."""
        prompts = manager.list_prompts()
        assert isinstance(prompts, list)
        assert "spiced_extraction" in prompts
        assert "spiced_coaching" in prompts

    def test_load_prompt(self, manager):
        """Test loading a prompt."""
        prompt = manager.load_prompt("spiced_extraction")
        assert "name" in prompt
        assert "version" in prompt
        assert "system_prompt" in prompt
        assert prompt["name"] == "spiced_extraction"

    def test_load_nonexistent_prompt(self, manager):
        """Test loading nonexistent prompt raises error."""
        with pytest.raises(PromptNotFoundError):
            manager.load_prompt("nonexistent_prompt")

    def test_get_prompt_with_variables(self, manager):
        """Test getting prompt with variable substitution."""
        result = manager.get_prompt("spiced_extraction", variables={
            "transcript": "Test transcript content",
            "company_name": "Test Corp",
        })
        assert "system" in result
        assert "user" in result
        assert "version" in result

    def test_validate_prompt(self, manager):
        """Test prompt validation."""
        result = manager.validate_prompt("spiced_extraction")
        assert "valid" in result
        assert "issues" in result
        assert "warnings" in result

    def test_validate_nonexistent_prompt(self, manager):
        """Test validating nonexistent prompt."""
        result = manager.validate_prompt("nonexistent")
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_get_metadata(self, manager):
        """Test getting prompt metadata."""
        metadata = manager.get_metadata("spiced_extraction")
        assert metadata.name == "spiced_extraction"
        assert metadata.version is not None
        assert metadata.category is not None

    def test_cache_behavior(self, manager):
        """Test that prompts are cached."""
        # First load
        prompt1 = manager.load_prompt("spiced_extraction")
        # Second load should use cache
        prompt2 = manager.load_prompt("spiced_extraction")
        assert prompt1 is prompt2  # Same object from cache

        # Force reload bypasses cache
        prompt3 = manager.load_prompt("spiced_extraction", force_reload=True)
        assert prompt1 is not prompt3

    def test_clear_cache(self, manager):
        """Test cache clearing."""
        manager.load_prompt("spiced_extraction")
        assert "spiced_extraction" in manager._cache

        manager.clear_cache("spiced_extraction")
        assert "spiced_extraction" not in manager._cache

    def test_export_json(self, manager):
        """Test exporting prompt as JSON."""
        exported = manager.export_prompt("spiced_extraction", format="json")
        data = json.loads(exported)
        assert "metadata" in data
        assert "system_prompt" in data


class TestPromptStructure:
    """Tests for prompt file structure and content."""

    @pytest.fixture
    def manager(self):
        return PromptManager()

    def test_spiced_extraction_structure(self, manager):
        """Test SPICED extraction prompt has required components."""
        prompt = manager.load_prompt("spiced_extraction")

        # Check system prompt contains SPICED elements
        system = prompt["system_prompt"].lower()
        assert "situation" in system
        assert "pain" in system
        assert "impact" in system
        assert "critical event" in system or "critical_event" in system
        assert "decision" in system

    def test_spiced_coaching_structure(self, manager):
        """Test SPICED coaching prompt has required components."""
        prompt = manager.load_prompt("spiced_coaching")

        system = prompt["system_prompt"].lower()
        assert "coach" in system or "coaching" in system
        assert "feedback" in system or "improvement" in system

    def test_content_generation_structure(self, manager):
        """Test content generation prompt has required components."""
        prompt = manager.load_prompt("content_generation")

        system = prompt["system_prompt"].lower()
        assert "content" in system
        assert "sales" in system or "deck" in system or "proposal" in system

    def test_prospect_enrichment_structure(self, manager):
        """Test prospect enrichment prompt has required components."""
        prompt = manager.load_prompt("prospect_enrichment")

        system = prompt["system_prompt"].lower()
        assert "research" in system or "enrich" in system
        assert "prospect" in system or "company" in system


class TestPromptIntegration:
    """Integration tests for prompt workflows."""

    @pytest.fixture
    def manager(self):
        return PromptManager()

    @pytest.fixture
    def engine(self):
        return TemplateEngine()

    def test_full_extraction_workflow(self, manager, engine):
        """Test complete SPICED extraction workflow."""
        # Get the prompt
        result = manager.get_prompt("spiced_extraction", variables={
            "transcript": """
            Hi, thanks for meeting today.
            We're a 50-person startup struggling with manual data entry.
            It's costing us about 10 hours per week.
            We need to solve this before our Series A in 3 months.
            Our CTO will make the final decision.
            """,
            "company_name": "StartupCo",
            "contact_name": "Jane Doe",
            "call_date": "2024-01-15",
            "call_type": "discovery",
        })

        assert result["user"] is not None
        assert "transcript" not in result["user"] or "{{transcript}}" not in result["user"]
        assert "StartupCo" in result["user"]

    def test_coaching_workflow(self, manager):
        """Test coaching feedback workflow."""
        result = manager.get_prompt("spiced_coaching", variables={
            "rep_name": "Mike",
            "call_type": "discovery",
            "call_date": "2024-01-15",
            "deal_stage": "qualification",
            "content": "Sample call transcript...",
        })

        assert result["system"] is not None
        assert result["user"] is not None
        assert "Mike" in result["user"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
