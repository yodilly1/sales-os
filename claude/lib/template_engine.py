"""
Template Engine

Simple but powerful template engine for prompt variable substitution.
Supports Mustache-style {{variable}} syntax with optional filters.
"""

import re
from typing import Any, Callable, Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""
    pass


class TemplateEngine:
    """
    Template engine for prompt variable substitution.

    Supports:
    - Basic variable substitution: {{variable}}
    - Optional variables: {{variable?}}
    - Default values: {{variable|default}}
    - Filters: {{variable|upper}}, {{variable|lower}}, {{variable|trim}}
    - Conditional blocks: {{#if variable}}...{{/if}}
    - List iteration: {{#each items}}{{.}}{{/each}}

    Usage:
        engine = TemplateEngine()
        result = engine.render("Hello {{name}}!", {"name": "World"})
    """

    # Regex patterns
    VARIABLE_PATTERN = re.compile(
        r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)([\?\|][^\}]*)?\}\}"
    )
    CONDITIONAL_PATTERN = re.compile(
        r"\{\{#if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}(.*?)\{\{/if\}\}",
        re.DOTALL
    )
    EACH_PATTERN = re.compile(
        r"\{\{#each\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}(.*?)\{\{/each\}\}",
        re.DOTALL
    )
    ITEM_PATTERN = re.compile(r"\{\{\.\}\}")

    def __init__(self):
        """Initialize the template engine."""
        self._filters: dict[str, Callable[[Any], str]] = {
            "upper": lambda x: str(x).upper(),
            "lower": lambda x: str(x).lower(),
            "trim": lambda x: str(x).strip(),
            "capitalize": lambda x: str(x).capitalize(),
            "title": lambda x: str(x).title(),
            "json": self._json_filter,
            "length": lambda x: str(len(x)) if hasattr(x, "__len__") else "0",
        }

    def _json_filter(self, value: Any) -> str:
        """Convert value to JSON string."""
        import json
        return json.dumps(value, indent=2)

    def register_filter(self, name: str, func: Callable[[Any], str]) -> None:
        """
        Register a custom filter function.

        Args:
            name: Filter name to use in templates
            func: Function that takes a value and returns a string
        """
        self._filters[name] = func

    def render(
        self,
        template: str,
        variables: dict[str, Any],
        strict: bool = False
    ) -> str:
        """
        Render a template with variable substitution.

        Args:
            template: Template string
            variables: Dictionary of variable values
            strict: If True, raise error for missing required variables

        Returns:
            Rendered string

        Raises:
            TemplateError: If strict=True and required variable is missing
        """
        if not template:
            return ""

        result = template

        # Process conditionals first
        result = self._process_conditionals(result, variables)

        # Process each loops
        result = self._process_each(result, variables)

        # Process variables
        result = self._process_variables(result, variables, strict)

        return result

    def _process_conditionals(
        self,
        template: str,
        variables: dict[str, Any]
    ) -> str:
        """Process {{#if variable}}...{{/if}} blocks."""
        def replace_conditional(match: re.Match) -> str:
            var_name = match.group(1)
            content = match.group(2)

            value = variables.get(var_name)
            if value:  # Truthy check
                return content
            return ""

        return self.CONDITIONAL_PATTERN.sub(replace_conditional, template)

    def _process_each(
        self,
        template: str,
        variables: dict[str, Any]
    ) -> str:
        """Process {{#each items}}...{{/each}} blocks."""
        def replace_each(match: re.Match) -> str:
            var_name = match.group(1)
            content = match.group(2)

            items = variables.get(var_name, [])
            if not items:
                return ""

            results = []
            for item in items:
                # Replace {{.}} with current item
                item_content = self.ITEM_PATTERN.sub(str(item), content)
                results.append(item_content)

            return "".join(results)

        return self.EACH_PATTERN.sub(replace_each, template)

    def _process_variables(
        self,
        template: str,
        variables: dict[str, Any],
        strict: bool
    ) -> str:
        """Process {{variable}} substitutions."""
        def replace_variable(match: re.Match) -> str:
            var_name = match.group(1)
            modifier = match.group(2) or ""

            is_optional = modifier.startswith("?")
            has_default = "|" in modifier

            value = variables.get(var_name)

            if value is None:
                if is_optional:
                    return ""
                elif has_default:
                    # Extract default value
                    default = modifier.split("|", 1)[-1].rstrip("}")
                    return default
                elif strict:
                    raise TemplateError(
                        f"Required variable '{var_name}' not provided"
                    )
                else:
                    return match.group(0)  # Leave placeholder

            # Apply filter if specified
            if "|" in modifier:
                filter_name = modifier.split("|")[-1].rstrip("}")
                if filter_name in self._filters:
                    value = self._filters[filter_name](value)

            return str(value)

        return self.VARIABLE_PATTERN.sub(replace_variable, template)

    def extract_variables(self, template: str) -> set[str]:
        """
        Extract all variable names from a template.

        Args:
            template: Template string

        Returns:
            Set of variable names found
        """
        if not template:
            return set()

        variables = set()

        # Extract from basic variables
        for match in self.VARIABLE_PATTERN.finditer(template):
            variables.add(match.group(1))

        # Extract from conditionals
        for match in self.CONDITIONAL_PATTERN.finditer(template):
            variables.add(match.group(1))

        # Extract from each loops
        for match in self.EACH_PATTERN.finditer(template):
            variables.add(match.group(1))

        return variables

    def validate_template(self, template: str) -> dict[str, Any]:
        """
        Validate a template for syntax errors.

        Args:
            template: Template string

        Returns:
            Validation result with variables and any issues
        """
        issues = []

        # Check for unclosed blocks
        if_opens = len(re.findall(r"\{\{#if\s+", template))
        if_closes = len(re.findall(r"\{\{/if\}\}", template))
        if if_opens != if_closes:
            issues.append(
                f"Mismatched if blocks: {if_opens} opens, {if_closes} closes"
            )

        each_opens = len(re.findall(r"\{\{#each\s+", template))
        each_closes = len(re.findall(r"\{\{/each\}\}", template))
        if each_opens != each_closes:
            issues.append(
                f"Mismatched each blocks: {each_opens} opens, {each_closes} closes"
            )

        # Check for malformed variables
        malformed = re.findall(r"\{\{[^}]*[^a-zA-Z0-9_\?\|\.\}][^}]*\}\}", template)
        if malformed:
            issues.append(f"Malformed variables: {malformed}")

        variables = self.extract_variables(template)

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "variables": sorted(variables),
        }

    def preview(
        self,
        template: str,
        variables: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Generate a preview with sample values for missing variables.

        Args:
            template: Template string
            variables: Partial variables dict

        Returns:
            Rendered preview string
        """
        variables = variables or {}
        required = self.extract_variables(template)

        # Generate sample values for missing variables
        sample_vars = {}
        for var in required:
            if var not in variables:
                sample_vars[var] = f"[{var}]"
            else:
                sample_vars[var] = variables[var]

        return self.render(template, sample_vars)
