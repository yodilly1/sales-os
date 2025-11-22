"""
Prompt Testing Framework

Utilities for testing and validating Claude AI prompts before deployment.
Supports both structural validation and output quality assessment.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# Import from parent package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.lib.prompt_manager import PromptManager
from claude.lib.template_engine import TemplateEngine


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """
    Definition of a prompt test case.

    Attributes:
        name: Test case name
        prompt_name: Name of prompt to test
        variables: Input variables for the prompt
        expected_fields: Fields expected in output JSON
        validators: Custom validation functions
        description: Test case description
        tags: Tags for filtering tests
    """
    name: str
    prompt_name: str
    variables: dict[str, Any]
    expected_fields: list[str] = field(default_factory=list)
    validators: list[Callable[[Any], bool]] = field(default_factory=list)
    description: str = ""
    tags: list[str] = field(default_factory=list)
    timeout_seconds: float = 30.0


@dataclass
class TestResult:
    """
    Result of a test case execution.

    Attributes:
        test_name: Name of the test
        status: Execution status
        duration_ms: Execution time in milliseconds
        output: Output from prompt (if any)
        errors: List of error messages
        warnings: List of warning messages
        timestamp: When test was run
    """
    test_name: str
    status: TestStatus
    duration_ms: float
    output: Optional[str] = None
    parsed_output: Optional[dict] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "output_length": len(self.output) if self.output else 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat(),
        }


class PromptTester:
    """
    Testing framework for Claude AI prompts.

    Features:
    - Structural validation (syntax, required fields)
    - Template rendering verification
    - Output schema validation
    - Custom validator support
    - Performance benchmarking
    - Test report generation

    Usage:
        tester = PromptTester()
        tester.add_test_case(TestCase(
            name="test_spiced_extraction",
            prompt_name="spiced_extraction",
            variables={"transcript": "..."},
            expected_fields=["situation", "pain", "impact"]
        ))
        results = tester.run_all()
        tester.generate_report(results)
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt tester.

        Args:
            prompts_dir: Directory containing prompts
        """
        self._prompt_manager = PromptManager(prompts_dir)
        self._template_engine = TemplateEngine()
        self._test_cases: list[TestCase] = []
        self._claude_client: Optional[Any] = None

    def set_claude_client(self, client: Any) -> None:
        """
        Set Claude API client for live testing.

        Args:
            client: Claude API client instance
        """
        self._claude_client = client

    def add_test_case(self, test_case: TestCase) -> None:
        """
        Add a test case to the suite.

        Args:
            test_case: Test case definition
        """
        self._test_cases.append(test_case)

    def add_test_cases(self, test_cases: list[TestCase]) -> None:
        """
        Add multiple test cases.

        Args:
            test_cases: List of test case definitions
        """
        self._test_cases.extend(test_cases)

    def clear_test_cases(self) -> None:
        """Remove all test cases."""
        self._test_cases.clear()

    def run_structural_test(self, prompt_name: str) -> TestResult:
        """
        Run structural validation on a prompt.

        Tests:
        - File exists and can be loaded
        - Has valid version
        - Has system prompt
        - Has user template
        - Template syntax is valid

        Args:
            prompt_name: Name of prompt to test

        Returns:
            TestResult with validation findings
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            # Validate prompt through manager
            validation = self._prompt_manager.validate_prompt(prompt_name)

            errors.extend(validation.get("issues", []))
            warnings.extend(validation.get("warnings", []))

            # Load and check components
            prompt_data = self._prompt_manager.load_prompt(prompt_name)

            if not prompt_data.get("system_prompt"):
                errors.append("System prompt is empty")

            if not prompt_data.get("user_template"):
                warnings.append("User template is empty")

            # Validate template syntax
            if prompt_data.get("user_template"):
                template_validation = self._template_engine.validate_template(
                    prompt_data["user_template"]
                )
                if not template_validation["valid"]:
                    errors.extend(template_validation["issues"])

        except Exception as e:
            errors.append(f"Failed to load prompt: {str(e)}")

        duration_ms = (time.time() - start_time) * 1000
        status = TestStatus.PASSED if not errors else TestStatus.FAILED

        return TestResult(
            test_name=f"structural_{prompt_name}",
            status=status,
            duration_ms=duration_ms,
            errors=errors,
            warnings=warnings,
        )

    def run_render_test(self, test_case: TestCase) -> TestResult:
        """
        Test that a prompt renders correctly with given variables.

        Args:
            test_case: Test case with variables

        Returns:
            TestResult with rendered output
        """
        start_time = time.time()
        errors = []
        warnings = []
        output = None

        try:
            result = self._prompt_manager.get_prompt(
                test_case.prompt_name,
                variables=test_case.variables
            )

            output = result.get("user", "")

            # Check for unresolved variables
            unresolved = self._template_engine.extract_variables(output)
            if unresolved:
                warnings.append(
                    f"Unresolved variables in output: {', '.join(unresolved)}"
                )

            # Check output is not empty
            if not output.strip():
                errors.append("Rendered output is empty")

        except Exception as e:
            errors.append(f"Render failed: {str(e)}")

        duration_ms = (time.time() - start_time) * 1000
        status = TestStatus.PASSED if not errors else TestStatus.FAILED

        return TestResult(
            test_name=test_case.name,
            status=status,
            duration_ms=duration_ms,
            output=output,
            errors=errors,
            warnings=warnings,
        )

    def run_output_validation(
        self,
        test_case: TestCase,
        output: str
    ) -> TestResult:
        """
        Validate that output matches expected structure.

        Args:
            test_case: Test case with expectations
            output: Output to validate

        Returns:
            TestResult with validation findings
        """
        start_time = time.time()
        errors = []
        warnings = []
        parsed_output = None

        # Try to parse as JSON
        try:
            # Find JSON in output (may be wrapped in markdown code blocks)
            json_match = self._extract_json(output)
            if json_match:
                parsed_output = json.loads(json_match)
            else:
                warnings.append("Output does not contain valid JSON")
        except json.JSONDecodeError as e:
            warnings.append(f"JSON parse warning: {str(e)}")

        # Check expected fields
        if parsed_output and test_case.expected_fields:
            for field in test_case.expected_fields:
                if field not in parsed_output:
                    errors.append(f"Missing expected field: {field}")

        # Run custom validators
        for validator in test_case.validators:
            try:
                if not validator(parsed_output or output):
                    errors.append(f"Custom validator failed: {validator.__name__}")
            except Exception as e:
                errors.append(f"Validator error: {str(e)}")

        duration_ms = (time.time() - start_time) * 1000
        status = TestStatus.PASSED if not errors else TestStatus.FAILED

        return TestResult(
            test_name=f"{test_case.name}_validation",
            status=status,
            duration_ms=duration_ms,
            parsed_output=parsed_output,
            errors=errors,
            warnings=warnings,
        )

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from text, handling markdown code blocks."""
        import re

        # Try to find JSON in code blocks
        code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if code_block:
            return code_block.group(1).strip()

        # Try to find raw JSON object/array
        json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if json_match:
            return json_match.group(1)

        return None

    def run_test_case(self, test_case: TestCase) -> list[TestResult]:
        """
        Run all tests for a single test case.

        Args:
            test_case: Test case to run

        Returns:
            List of test results
        """
        results = []

        # Run structural test
        structural = self.run_structural_test(test_case.prompt_name)
        results.append(structural)

        # Run render test
        render = self.run_render_test(test_case)
        results.append(render)

        # If render succeeded and we have expected fields, validate output
        if render.status == TestStatus.PASSED and render.output:
            if test_case.expected_fields or test_case.validators:
                validation = self.run_output_validation(test_case, render.output)
                results.append(validation)

        return results

    def run_all(self, tags: Optional[list[str]] = None) -> list[TestResult]:
        """
        Run all registered test cases.

        Args:
            tags: Only run tests with these tags (None = all)

        Returns:
            List of all test results
        """
        results = []

        for test_case in self._test_cases:
            # Filter by tags if specified
            if tags:
                if not any(tag in test_case.tags for tag in tags):
                    continue

            case_results = self.run_test_case(test_case)
            results.extend(case_results)

        return results

    def run_all_structural(self) -> list[TestResult]:
        """
        Run structural tests on all available prompts.

        Returns:
            List of structural test results
        """
        results = []
        for prompt_name in self._prompt_manager.list_prompts():
            result = self.run_structural_test(prompt_name)
            results.append(result)
        return results

    def generate_report(
        self,
        results: list[TestResult],
        format: str = "text"
    ) -> str:
        """
        Generate a test report.

        Args:
            results: Test results to report
            format: Output format ('text', 'json', 'markdown')

        Returns:
            Formatted report string
        """
        if format == "json":
            return self._generate_json_report(results)
        elif format == "markdown":
            return self._generate_markdown_report(results)
        else:
            return self._generate_text_report(results)

    def _generate_text_report(self, results: list[TestResult]) -> str:
        """Generate plain text report."""
        lines = [
            "=" * 60,
            "PROMPT TEST REPORT",
            "=" * 60,
            f"Generated: {datetime.now().isoformat()}",
            f"Total Tests: {len(results)}",
            "",
        ]

        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)

        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")
        lines.append(f"Errors: {errors}")
        lines.append("")
        lines.append("-" * 60)
        lines.append("RESULTS")
        lines.append("-" * 60)

        for result in results:
            status_icon = {
                TestStatus.PASSED: "[PASS]",
                TestStatus.FAILED: "[FAIL]",
                TestStatus.ERROR: "[ERR ]",
                TestStatus.SKIPPED: "[SKIP]",
            }[result.status]

            lines.append(f"{status_icon} {result.test_name} ({result.duration_ms:.1f}ms)")

            if result.errors:
                for error in result.errors:
                    lines.append(f"       ERROR: {error}")

            if result.warnings:
                for warning in result.warnings:
                    lines.append(f"       WARN: {warning}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_markdown_report(self, results: list[TestResult]) -> str:
        """Generate markdown report."""
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        total = len(results)

        lines = [
            "# Prompt Test Report",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "## Summary",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total | {total} |",
            f"| Passed | {passed} |",
            f"| Failed | {failed} |",
            f"| Pass Rate | {(passed/total*100) if total else 0:.1f}% |",
            "",
            "## Results",
            "",
        ]

        for result in results:
            icon = "✅" if result.status == TestStatus.PASSED else "❌"
            lines.append(f"### {icon} {result.test_name}")
            lines.append("")
            lines.append(f"- **Status:** {result.status.value}")
            lines.append(f"- **Duration:** {result.duration_ms:.1f}ms")

            if result.errors:
                lines.append("- **Errors:**")
                for error in result.errors:
                    lines.append(f"  - {error}")

            if result.warnings:
                lines.append("- **Warnings:**")
                for warning in result.warnings:
                    lines.append(f"  - {warning}")

            lines.append("")

        return "\n".join(lines)

    def _generate_json_report(self, results: list[TestResult]) -> str:
        """Generate JSON report."""
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "pass_rate": (passed / len(results) * 100) if results else 0,
            },
            "results": [r.to_dict() for r in results],
        }

        return json.dumps(report, indent=2)


# Built-in test cases for Sales OS prompts
DEFAULT_TEST_CASES = [
    TestCase(
        name="spiced_extraction_basic",
        prompt_name="spiced_extraction",
        variables={
            "transcript": "Sample transcript text for testing",
            "company_name": "Test Corp",
            "contact_name": "John Doe",
            "call_date": "2024-01-15",
            "call_type": "discovery",
        },
        expected_fields=["situation", "pain", "impact", "critical_event", "decision"],
        description="Basic SPICED extraction test",
        tags=["spiced", "extraction", "core"],
    ),
    TestCase(
        name="spiced_coaching_basic",
        prompt_name="spiced_coaching",
        variables={
            "rep_name": "Test Rep",
            "call_type": "discovery",
            "call_date": "2024-01-15",
            "deal_stage": "qualification",
            "content": "Sample call content for coaching",
        },
        expected_fields=["overall_score", "strengths", "improvements"],
        description="Basic SPICED coaching test",
        tags=["spiced", "coaching", "core"],
    ),
    TestCase(
        name="content_generation_deck",
        prompt_name="content_generation",
        variables={
            "deck_type": "proposal",
            "company_name": "Test Corp",
            "industry": "Technology",
            "situation": "Growing startup",
            "pain_points": "Manual processes",
        },
        expected_fields=[],
        description="Content generation deck test",
        tags=["content", "generation", "core"],
    ),
    TestCase(
        name="prospect_enrichment_basic",
        prompt_name="prospect_enrichment",
        variables={
            "name": "Jane Smith",
            "email": "jane@testcorp.com",
            "company": "Test Corp",
            "product_description": "Sales automation platform",
        },
        expected_fields=["person", "company"],
        description="Basic prospect enrichment test",
        tags=["enrichment", "research", "core"],
    ),
]


def run_default_tests() -> str:
    """
    Run the default test suite for Sales OS prompts.

    Returns:
        Test report string
    """
    tester = PromptTester()
    tester.add_test_cases(DEFAULT_TEST_CASES)

    # Run structural tests on all prompts
    structural_results = tester.run_all_structural()

    # Run functional tests
    functional_results = tester.run_all()

    all_results = structural_results + functional_results

    return tester.generate_report(all_results, format="markdown")
