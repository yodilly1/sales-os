"""
Email Template Renderer

Handles rendering of email templates with variable substitution.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...models.email import EmailTemplate, EmailTemplateType


logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Renders email templates with variable substitution.

    Supports:
    - Simple variable substitution ({{variable}})
    - Conditional blocks ({{#if condition}}...{{/if}})
    - Loops ({{#each items}}...{{/each}})
    - Default values ({{variable|default:"value"}})
    - Formatting filters ({{date|format:"YYYY-MM-DD"}})
    """

    # Variable pattern: {{variable_name}}
    VAR_PATTERN = re.compile(r'\{\{([^}#/|]+?)(?:\|([^}]+))?\}\}')

    # Conditional pattern: {{#if condition}}...{{/if}}
    IF_PATTERN = re.compile(
        r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}',
        re.DOTALL
    )

    # Else pattern within if blocks
    IF_ELSE_PATTERN = re.compile(
        r'\{\{#if\s+(\w+)\}\}(.*?)\{\{#else\}\}(.*?)\{\{/if\}\}',
        re.DOTALL
    )

    # Each loop pattern: {{#each items}}...{{/each}}
    EACH_PATTERN = re.compile(
        r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}',
        re.DOTALL
    )

    def __init__(self):
        """Initialize the template renderer."""
        self._template_cache: Dict[str, EmailTemplate] = {}

    def render(
        self,
        template: EmailTemplate,
        variables: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Render an email template with variables.

        Args:
            template: The email template to render
            variables: Dictionary of variables for substitution

        Returns:
            Dictionary with 'html', 'text', and 'subject' keys
        """
        # Add common variables
        enhanced_vars = self._add_common_variables(variables)

        # Render each part
        rendered_subject = self._render_content(template.subject, enhanced_vars)
        rendered_html = self._render_content(template.html_content, enhanced_vars)
        rendered_text = None

        if template.text_content:
            rendered_text = self._render_content(template.text_content, enhanced_vars)
        else:
            # Generate plain text from HTML
            rendered_text = self._html_to_text(rendered_html)

        return {
            "subject": rendered_subject,
            "html": rendered_html,
            "text": rendered_text,
        }

    def _add_common_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Add common/default variables."""
        enhanced = dict(variables)

        # Add date/time variables
        now = datetime.utcnow()
        enhanced.setdefault('current_year', now.year)
        enhanced.setdefault('current_date', now.strftime('%B %d, %Y'))
        enhanced.setdefault('current_month', now.strftime('%B'))

        # Add company defaults if not provided
        enhanced.setdefault('company_name', 'Our Company')
        enhanced.setdefault('company_address', '')

        return enhanced

    def _render_content(self, content: str, variables: Dict[str, Any]) -> str:
        """Render a content string with all template features."""
        # Process conditionals with else first
        content = self._process_if_else_blocks(content, variables)

        # Process simple conditionals
        content = self._process_if_blocks(content, variables)

        # Process each loops
        content = self._process_each_loops(content, variables)

        # Process variables
        content = self._process_variables(content, variables)

        return content

    def _process_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """Replace {{variable}} patterns with values."""
        def replace_var(match):
            var_name = match.group(1).strip()
            filter_expr = match.group(2)

            # Get value with dot notation support
            value = self._get_nested_value(variables, var_name)

            # Apply default if value is None
            if value is None and filter_expr:
                default_match = re.match(r'default:\s*["\']([^"\']*)["\']', filter_expr)
                if default_match:
                    return default_match.group(1)

            if value is None:
                return ''

            # Apply filters
            if filter_expr:
                value = self._apply_filter(value, filter_expr)

            return str(value)

        return self.VAR_PATTERN.sub(replace_var, content)

    def _process_if_else_blocks(
        self, content: str, variables: Dict[str, Any]
    ) -> str:
        """Process {{#if}}...{{#else}}...{{/if}} blocks."""
        def replace_if_else(match):
            condition_var = match.group(1)
            if_content = match.group(2)
            else_content = match.group(3)

            value = self._get_nested_value(variables, condition_var)

            if self._is_truthy(value):
                return if_content
            else:
                return else_content

        return self.IF_ELSE_PATTERN.sub(replace_if_else, content)

    def _process_if_blocks(self, content: str, variables: Dict[str, Any]) -> str:
        """Process {{#if condition}}...{{/if}} blocks."""
        def replace_if(match):
            condition_var = match.group(1)
            block_content = match.group(2)

            value = self._get_nested_value(variables, condition_var)

            if self._is_truthy(value):
                return block_content
            return ''

        return self.IF_PATTERN.sub(replace_if, content)

    def _process_each_loops(self, content: str, variables: Dict[str, Any]) -> str:
        """Process {{#each items}}...{{/each}} blocks."""
        def replace_each(match):
            list_var = match.group(1)
            block_content = match.group(2)

            items = self._get_nested_value(variables, list_var)

            if not items or not isinstance(items, (list, tuple)):
                return ''

            result = []
            for i, item in enumerate(items):
                # Create context for this iteration
                item_vars = dict(variables)
                if isinstance(item, dict):
                    item_vars.update(item)
                else:
                    item_vars['this'] = item
                item_vars['@index'] = i
                item_vars['@first'] = i == 0
                item_vars['@last'] = i == len(items) - 1

                # Render block with item context
                rendered = self._render_content(block_content, item_vars)
                result.append(rendered)

            return ''.join(result)

        return self.EACH_PATTERN.sub(replace_each, content)

    def _get_nested_value(self, variables: Dict[str, Any], key: str) -> Any:
        """Get a nested value using dot notation (e.g., 'user.name')."""
        parts = key.split('.')
        value = variables

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value

    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy for template conditions."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (list, tuple, dict, str)):
            return len(value) > 0
        if isinstance(value, (int, float)):
            return value != 0
        return True

    def _apply_filter(self, value: Any, filter_expr: str) -> str:
        """Apply a filter to a value."""
        # Format filter for dates
        format_match = re.match(r'format:\s*["\']([^"\']*)["\']', filter_expr)
        if format_match and isinstance(value, datetime):
            return value.strftime(format_match.group(1))

        # Uppercase filter
        if filter_expr.strip() == 'upper':
            return str(value).upper()

        # Lowercase filter
        if filter_expr.strip() == 'lower':
            return str(value).lower()

        # Title case filter
        if filter_expr.strip() == 'title':
            return str(value).title()

        # Truncate filter
        truncate_match = re.match(r'truncate:\s*(\d+)', filter_expr)
        if truncate_match:
            length = int(truncate_match.group(1))
            text = str(value)
            if len(text) > length:
                return text[:length - 3] + '...'
            return text

        return str(value)

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        # Remove style and script tags
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)

        # Convert line breaks
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'</p>', '\n\n', text)
        text = re.sub(r'</div>', '\n', text)
        text = re.sub(r'</li>', '\n', text)

        # Convert links to text with URL
        text = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', r'\2 (\1)', text)

        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Clean up whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = text.strip()

        # Decode HTML entities
        import html
        text = html.unescape(text)

        return text

    def validate_template(
        self,
        template: EmailTemplate,
        sample_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a template and identify required variables.

        Args:
            template: Template to validate
            sample_variables: Optional sample variables for test render

        Returns:
            Validation result with required variables and any errors
        """
        result = {
            "valid": True,
            "required_variables": [],
            "optional_variables": [],
            "errors": [],
        }

        # Extract all variables from template
        all_content = template.subject + template.html_content
        if template.text_content:
            all_content += template.text_content

        # Find all variable references
        var_matches = self.VAR_PATTERN.findall(all_content)
        if_matches = self.IF_PATTERN.findall(all_content)
        each_matches = self.EACH_PATTERN.findall(all_content)

        variables_found = set()
        for var, _ in var_matches:
            variables_found.add(var.strip().split('.')[0])

        for condition, _ in if_matches:
            variables_found.add(condition)

        for list_var, _ in each_matches:
            variables_found.add(list_var)

        # Check against template's declared variables
        if template.variables:
            declared = {v.name for v in template.variables}
            required = {v.name for v in template.variables if v.required}

            result["required_variables"] = list(required)
            result["optional_variables"] = list(declared - required)

            # Check for undeclared variables
            undeclared = variables_found - declared
            if undeclared:
                result["errors"].append(
                    f"Undeclared variables used: {', '.join(undeclared)}"
                )
                result["valid"] = False
        else:
            result["required_variables"] = list(variables_found)

        # Try test render if sample variables provided
        if sample_variables:
            try:
                self.render(template, sample_variables)
            except Exception as e:
                result["errors"].append(f"Render error: {str(e)}")
                result["valid"] = False

        return result


# Pre-built template generators
class DefaultTemplates:
    """Factory for creating default email templates."""

    @staticmethod
    def follow_up_template() -> EmailTemplate:
        """Create a follow-up email template."""
        return EmailTemplate(
            name="Post-Call Follow Up",
            subject="Following up on our conversation{{#if topic}} about {{topic}}{{/if}}",
            template_type=EmailTemplateType.FOLLOW_UP,
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { margin-bottom: 20px; }
        .content { margin-bottom: 20px; }
        .action-items { background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .action-items h3 { margin-top: 0; }
        .action-items ul { margin-bottom: 0; }
        .signature { margin-top: 30px; color: #666; }
        .cta-button { display: inline-block; padding: 10px 20px; background: #007bff; color: #fff; text-decoration: none; border-radius: 5px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <p>Hi {{recipient_name|default:"there"}},</p>
        </div>
        <div class="content">
            <p>Thank you for taking the time to meet with me{{#if meeting_date}} on {{meeting_date}}{{/if}}. I really enjoyed our conversation{{#if topic}} about {{topic}}{{/if}}.</p>

            {{#if key_points}}
            <p>Here are the key points we discussed:</p>
            <ul>
                {{#each key_points}}
                <li>{{this}}</li>
                {{/each}}
            </ul>
            {{/if}}

            {{#if action_items}}
            <div class="action-items">
                <h3>Next Steps</h3>
                <ul>
                    {{#each action_items}}
                    <li>{{this}}</li>
                    {{/each}}
                </ul>
            </div>
            {{/if}}

            {{#if cta_text}}
            <p><a href="{{cta_url}}" class="cta-button">{{cta_text}}</a></p>
            {{/if}}

            <p>{{#if custom_message}}{{custom_message}}{{#else}}Please don't hesitate to reach out if you have any questions.{{/if}}</p>
        </div>
        <div class="signature">
            <p>Best regards,<br>
            {{sender_name}}<br>
            {{#if sender_title}}{{sender_title}}<br>{{/if}}
            {{#if sender_phone}}{{sender_phone}}<br>{{/if}}
            {{sender_email}}</p>
        </div>
    </div>
</body>
</html>
""",
            description="Follow-up email after a sales call or meeting",
            category="Sales",
            tags=["follow-up", "post-call", "sales"],
        )

    @staticmethod
    def proposal_template() -> EmailTemplate:
        """Create a proposal delivery email template."""
        return EmailTemplate(
            name="Proposal Delivery",
            subject="{{company_name}} Proposal for {{recipient_company}}",
            template_type=EmailTemplateType.PROPOSAL,
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { margin-bottom: 20px; }
        .highlight-box { background: #f0f7ff; padding: 20px; border-left: 4px solid #007bff; margin: 20px 0; }
        .benefits { margin: 20px 0; }
        .benefits li { margin: 10px 0; }
        .cta-button { display: inline-block; padding: 12px 24px; background: #28a745; color: #fff; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 15px 0; }
        .signature { margin-top: 30px; color: #666; }
        .ps { font-style: italic; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <p>Hi {{recipient_name}},</p>
        </div>

        <p>As promised, I'm pleased to share the proposal we discussed for {{recipient_company}}.</p>

        <div class="highlight-box">
            <strong>{{proposal_title|default:"Our Proposal"}}</strong><br>
            {{#if proposal_summary}}{{proposal_summary}}{{/if}}
        </div>

        {{#if key_benefits}}
        <div class="benefits">
            <p><strong>Key Benefits for {{recipient_company}}:</strong></p>
            <ul>
                {{#each key_benefits}}
                <li>{{this}}</li>
                {{/each}}
            </ul>
        </div>
        {{/if}}

        <p><a href="{{proposal_url}}" class="cta-button">View Full Proposal</a></p>

        {{#if investment}}
        <p><strong>Investment:</strong> {{investment}}</p>
        {{/if}}

        {{#if valid_until}}
        <p>This proposal is valid until {{valid_until}}.</p>
        {{/if}}

        <p>I'd love to schedule a call to walk through the proposal in detail and answer any questions. Would {{#if suggested_time}}{{suggested_time}}{{#else}}sometime this week{{/if}} work for you?</p>

        <div class="signature">
            <p>Best regards,<br>
            {{sender_name}}<br>
            {{#if sender_title}}{{sender_title}}<br>{{/if}}
            {{sender_email}}<br>
            {{#if sender_phone}}{{sender_phone}}{{/if}}</p>
        </div>

        {{#if ps_message}}
        <p class="ps">P.S. {{ps_message}}</p>
        {{/if}}
    </div>
</body>
</html>
""",
            description="Email template for delivering proposals to prospects",
            category="Sales",
            tags=["proposal", "sales", "deal"],
        )

    @staticmethod
    def intro_template() -> EmailTemplate:
        """Create an introduction/outreach email template."""
        return EmailTemplate(
            name="Introduction Outreach",
            subject="{{#if personalized_subject}}{{personalized_subject}}{{#else}}Quick question about {{recipient_company}}{{/if}}",
            template_type=EmailTemplateType.INTRO,
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .content p { margin: 15px 0; }
        .value-prop { background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .cta-link { color: #007bff; font-weight: bold; }
        .signature { margin-top: 30px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <p>Hi {{recipient_name|default:"there"}},</p>

            {{#if personalized_opener}}
            <p>{{personalized_opener}}</p>
            {{#else}}
            <p>I hope this email finds you well. I came across {{recipient_company}} and was impressed by {{#if company_highlight}}{{company_highlight}}{{#else}}your work{{/if}}.</p>
            {{/if}}

            {{#if pain_point}}
            <p>Many {{#if industry}}{{industry}}{{#else}}companies{{/if}} leaders I speak with are dealing with {{pain_point}}. Does this resonate with you?</p>
            {{/if}}

            <div class="value-prop">
                <p>{{#if value_proposition}}{{value_proposition}}{{#else}}We help companies like {{recipient_company}} achieve better results through our proven approach.{{/if}}</p>
            </div>

            {{#if social_proof}}
            <p>{{social_proof}}</p>
            {{/if}}

            <p>{{#if cta_question}}{{cta_question}}{{#else}}Would you be open to a brief call to explore if there's a fit?{{/if}}</p>

            {{#if calendar_link}}
            <p><a href="{{calendar_link}}" class="cta-link">Book a time that works for you →</a></p>
            {{/if}}
        </div>

        <div class="signature">
            <p>Best,<br>
            {{sender_name}}<br>
            {{#if sender_title}}{{sender_title}}<br>{{/if}}
            {{company_name}}</p>
        </div>
    </div>
</body>
</html>
""",
            description="Cold outreach introduction email template",
            category="Outreach",
            tags=["intro", "outreach", "prospecting", "cold-email"],
        )

    @staticmethod
    def content_delivery_template() -> EmailTemplate:
        """Create a content delivery email template."""
        return EmailTemplate(
            name="Content Delivery",
            subject="{{content_title}} - As Requested",
            template_type=EmailTemplateType.CONTENT_DELIVERY,
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .content-card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .content-card h2 { margin-top: 0; color: #333; }
        .content-type { display: inline-block; background: #007bff; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-bottom: 10px; }
        .download-button { display: inline-block; padding: 12px 24px; background: #007bff; color: #fff; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 10px 0; }
        .related-content { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        .related-content h3 { color: #666; }
        .related-item { margin: 10px 0; }
        .related-item a { color: #007bff; }
        .signature { margin-top: 30px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <p>Hi {{recipient_name|default:"there"}},</p>

        <p>{{#if custom_intro}}{{custom_intro}}{{#else}}As requested, here's the content we discussed.{{/if}}</p>

        <div class="content-card">
            <span class="content-type">{{content_type|default:"Resource"}}</span>
            <h2>{{content_title}}</h2>
            {{#if content_description}}
            <p>{{content_description}}</p>
            {{/if}}
            <p><a href="{{content_url}}" class="download-button">{{#if download_text}}{{download_text}}{{#else}}Access Content{{/if}}</a></p>
        </div>

        {{#if key_takeaways}}
        <p><strong>Key Takeaways:</strong></p>
        <ul>
            {{#each key_takeaways}}
            <li>{{this}}</li>
            {{/each}}
        </ul>
        {{/if}}

        {{#if related_content}}
        <div class="related-content">
            <h3>You might also find these helpful:</h3>
            {{#each related_content}}
            <div class="related-item">
                <a href="{{url}}">{{title}}</a>
                {{#if description}} - {{description}}{{/if}}
            </div>
            {{/each}}
        </div>
        {{/if}}

        <p>{{#if cta_message}}{{cta_message}}{{#else}}Let me know if you have any questions or would like to discuss further.{{/if}}</p>

        <div class="signature">
            <p>Best regards,<br>
            {{sender_name}}<br>
            {{#if sender_title}}{{sender_title}}<br>{{/if}}
            {{sender_email}}</p>
        </div>
    </div>
</body>
</html>
""",
            description="Template for delivering content (decks, proposals, resources) to prospects",
            category="Content",
            tags=["content", "delivery", "resources"],
        )

    @staticmethod
    def meeting_recap_template() -> EmailTemplate:
        """Create a meeting recap email template."""
        return EmailTemplate(
            name="Meeting Recap",
            subject="Recap: {{meeting_title|default:'Our Meeting'}} - {{meeting_date}}",
            template_type=EmailTemplateType.MEETING_RECAP,
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .meeting-header { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .meeting-header h3 { margin: 0 0 10px 0; }
        .section { margin: 25px 0; }
        .section h3 { color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        .action-item { display: flex; margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px; }
        .action-owner { background: #e9ecef; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin-left: auto; }
        .next-steps { background: #d4edda; padding: 15px; border-radius: 5px; }
        .signature { margin-top: 30px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <p>Hi {{recipient_name|default:'everyone'}},</p>

        <p>Thank you for your time today. Here's a quick recap of our discussion.</p>

        <div class="meeting-header">
            <h3>{{meeting_title|default:'Meeting Summary'}}</h3>
            <p><strong>Date:</strong> {{meeting_date}}<br>
            {{#if attendees}}<strong>Attendees:</strong> {{attendees}}{{/if}}</p>
        </div>

        {{#if discussion_points}}
        <div class="section">
            <h3>Discussion Summary</h3>
            <ul>
                {{#each discussion_points}}
                <li>{{this}}</li>
                {{/each}}
            </ul>
        </div>
        {{/if}}

        {{#if decisions}}
        <div class="section">
            <h3>Decisions Made</h3>
            <ul>
                {{#each decisions}}
                <li>{{this}}</li>
                {{/each}}
            </ul>
        </div>
        {{/if}}

        {{#if action_items}}
        <div class="section">
            <h3>Action Items</h3>
            {{#each action_items}}
            <div class="action-item">
                <span>{{task}}</span>
                {{#if owner}}<span class="action-owner">{{owner}}</span>{{/if}}
            </div>
            {{/each}}
        </div>
        {{/if}}

        {{#if next_meeting}}
        <div class="next-steps">
            <strong>Next Meeting:</strong> {{next_meeting}}
        </div>
        {{/if}}

        <p>Please let me know if I missed anything or if you have any questions.</p>

        <div class="signature">
            <p>Best regards,<br>
            {{sender_name}}<br>
            {{#if sender_title}}{{sender_title}}{{/if}}</p>
        </div>
    </div>
</body>
</html>
""",
            description="Template for sending meeting recap emails",
            category="Sales",
            tags=["meeting", "recap", "summary", "follow-up"],
        )
