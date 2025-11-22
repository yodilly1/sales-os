# Prompt Engineering Guidelines

This document provides guidelines for creating, maintaining, and testing Claude AI prompts for the Sales OS platform.

## Table of Contents

1. [Prompt Structure](#prompt-structure)
2. [Writing Effective Prompts](#writing-effective-prompts)
3. [SPICED Methodology Integration](#spiced-methodology-integration)
4. [Template Variables](#template-variables)
5. [Versioning](#versioning)
6. [Testing](#testing)
7. [Best Practices](#best-practices)

---

## Prompt Structure

All prompts follow a standard markdown structure:

```markdown
# Prompt Name

**Version:** X.Y.Z
**Last Updated:** YYYY-MM-DD
**Category:** Category Name

## Purpose

Brief description of what this prompt does.

---

## System Prompt

\```
System prompt content here
\```

---

## User Prompt Template

\```
User prompt with {{variables}}
\```

---

## Example Input

Example input data

---

## Example Output

Expected output format

---

## Testing Criteria

List of validation requirements

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | YYYY-MM-DD | Initial release |
```

---

## Writing Effective Prompts

### 1. Be Specific and Clear

Bad:
```
Analyze this call and tell me what you find.
```

Good:
```
Analyze this sales call transcript and extract the following SPICED elements:
- Situation: Current state and context of the prospect
- Pain: Problems and challenges they are experiencing
- Impact: Business consequences of the pain
...
```

### 2. Structure Output Expectations

Always define the expected output format explicitly:

```
Return a structured JSON object with the following schema:

{
  "situation": {
    "current_state": "string",
    "confidence": "high|medium|low"
  },
  ...
}
```

### 3. Provide Examples

Include concrete examples that demonstrate:
- Input format and content
- Expected output structure
- Edge cases and how to handle them

### 4. Set Boundaries and Guidelines

```
## Guidelines

1. Only extract information explicitly stated or clearly implied
2. Mark inferences with "Inferred:" prefix
3. If information is not available, set field to null
4. Never fabricate data points
```

### 5. Define Confidence Levels

For analysis tasks, include confidence scoring:

```
Confidence Levels:
- high: Explicitly stated in transcript
- medium: Strongly implied or inferable
- low: Possible interpretation, needs verification
```

---

## SPICED Methodology Integration

All Sales OS prompts should align with the Winning by Design SPICED methodology:

### S - Situation
- Current state of the prospect/company
- Context and background
- Size, stage, industry

### P - Pain
- Problems they're experiencing
- Challenges and frustrations
- Root causes

### I - Impact
- Business consequences of pain
- Quantified costs (time, money, resources)
- Affected teams and metrics

### C - Critical Event
- Urgency triggers
- Deadlines and timelines
- What happens if they don't act

### E - Decision (Event)
- Decision-making process
- Timeline for decision
- Key stakeholders

### D - Decision Criteria
- Must-have requirements
- Nice-to-have preferences
- Concerns and objections

---

## Template Variables

### Syntax

Use Mustache-style double braces for variables:

```
{{variable_name}}
```

### Supported Features

| Syntax | Description | Example |
|--------|-------------|---------|
| `{{var}}` | Basic variable | `{{transcript}}` |
| `{{var?}}` | Optional (empty if missing) | `{{notes?}}` |
| `{{var\|default}}` | Default value | `{{name\|Unknown}}` |
| `{{var\|upper}}` | Filter (uppercase) | `{{company\|upper}}` |
| `{{#if var}}...{{/if}}` | Conditional | `{{#if context}}With context{{/if}}` |
| `{{#each items}}{{.}}{{/each}}` | Iteration | List items |

### Available Filters

- `upper` - Convert to uppercase
- `lower` - Convert to lowercase
- `trim` - Remove whitespace
- `capitalize` - Capitalize first letter
- `title` - Title case
- `json` - Convert to JSON string

### Variable Naming Conventions

- Use `snake_case` for all variables
- Be descriptive: `company_name` not `cn`
- Group related variables with prefixes: `call_date`, `call_type`, `call_stage`

---

## Versioning

### Semantic Versioning

Prompts use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes to output structure
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, minor improvements

### When to Bump Versions

| Change | Version Bump |
|--------|--------------|
| New output fields | MINOR |
| Changed field names | MAJOR |
| Fixed typos | PATCH |
| Added examples | PATCH |
| Changed output structure | MAJOR |
| Added validation rules | MINOR |

### Version History

Maintain a version history table at the end of each prompt:

```markdown
## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2024-02-01 | Added stakeholder mapping |
| 1.0.1 | 2024-01-20 | Fixed JSON schema |
| 1.0.0 | 2024-01-15 | Initial release |
```

---

## Testing

### Structural Tests

Every prompt must pass structural validation:

1. Has valid version number
2. Contains system prompt
3. Contains user template (if applicable)
4. Template syntax is valid
5. No unclosed blocks

### Functional Tests

Test prompts with representative inputs:

```python
from claude.tests import PromptTester, TestCase

tester = PromptTester()
tester.add_test_case(TestCase(
    name="test_spiced_extraction",
    prompt_name="spiced_extraction",
    variables={
        "transcript": "...",
        "company_name": "Test Corp"
    },
    expected_fields=["situation", "pain", "impact"]
))

results = tester.run_all()
```

### Output Validation

Define expected output fields and validators:

```python
TestCase(
    name="test_coaching",
    prompt_name="spiced_coaching",
    variables={...},
    expected_fields=["overall_score", "strengths", "improvements"],
    validators=[
        lambda x: 0 <= x.get("overall_score", -1) <= 100,
        lambda x: len(x.get("strengths", [])) > 0
    ]
)
```

### Running Tests

```bash
# Run all prompt tests
pytest claude/tests/test_prompts.py -v

# Run specific test
pytest claude/tests/test_prompts.py::TestPromptStructure -v

# Generate test report
python -c "from claude.tests.prompt_tester import run_default_tests; print(run_default_tests())"
```

---

## Best Practices

### Do's

1. **Be explicit** - State exactly what you want
2. **Provide structure** - Define output format clearly
3. **Include examples** - Show input/output pairs
4. **Set boundaries** - Define what to do and what NOT to do
5. **Test thoroughly** - Cover edge cases
6. **Document changes** - Update version history
7. **Use consistent terminology** - Align with SPICED methodology

### Don'ts

1. **Don't be vague** - Avoid ambiguous instructions
2. **Don't assume** - Explain context explicitly
3. **Don't over-engineer** - Keep prompts focused
4. **Don't skip testing** - Validate before deployment
5. **Don't ignore edge cases** - Handle missing data
6. **Don't break compatibility** - Version appropriately

### Prompt Review Checklist

- [ ] Clear purpose statement
- [ ] Explicit output format defined
- [ ] Input variables documented
- [ ] Examples provided
- [ ] Edge cases handled
- [ ] Confidence levels defined (if applicable)
- [ ] SPICED alignment verified
- [ ] Tests written and passing
- [ ] Version history updated

---

## Quick Reference

### Creating a New Prompt

1. Copy the template structure
2. Define purpose and category
3. Write system prompt with clear instructions
4. Create user template with variables
5. Add input/output examples
6. Define testing criteria
7. Add test cases
8. Run tests to validate

### Modifying Existing Prompts

1. Document the change needed
2. Determine version bump type
3. Make changes
4. Update examples if needed
5. Run existing tests
6. Add new tests if needed
7. Update version and history

### Deploying Prompts

1. All tests must pass
2. Version must be bumped
3. Changes documented
4. Review completed (for major changes)

---

## Support

For questions about prompt engineering:
- Check existing prompts for patterns
- Review test cases for examples
- Consult the Winning by Design SPICED documentation
