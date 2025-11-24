"""Outreach campaign generation service."""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from app.services.claude_client import ClaudeClient, create_claude_client
from .models import (
    OutreachCampaign,
    OutreachSequence,
    OutreachStep,
    OutreachFormat,
    ExportFormat,
    CampaignGenerateRequest,
    CampaignGenerateResponse,
    InstantlyCSVRow,
    HeyReachCSVRow,
)

logger = logging.getLogger(__name__)


class OutreachService:
    """Service for generating outreach campaigns."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize outreach service."""
        self.claude_client = claude_client or create_claude_client()
        self._campaigns: dict[str, OutreachCampaign] = {}  # In-memory storage

    async def generate_campaign(
        self,
        request: CampaignGenerateRequest,
    ) -> CampaignGenerateResponse:
        """
        Generate a personalized outreach campaign for a prospect.

        Args:
            request: Campaign generation request with prospect/company info

        Returns:
            Generated campaign with email and LinkedIn sequences
        """
        try:
            # Build context for campaign generation
            context = self._build_context(request)

            # Generate email sequence
            email_sequence = None
            if request.format in [OutreachFormat.EMAIL, OutreachFormat.MULTI_CHANNEL]:
                email_sequence = await self._generate_email_sequence(
                    request, context, request.num_email_steps
                )

            # Generate LinkedIn sequence
            linkedin_sequence = None
            if request.format in [OutreachFormat.LINKEDIN, OutreachFormat.MULTI_CHANNEL]:
                linkedin_sequence = await self._generate_linkedin_sequence(
                    request, context, request.num_linkedin_steps
                )

            # Create campaign
            campaign = OutreachCampaign(
                prospect_email=request.prospect_email,
                prospect_name=request.prospect_name,
                prospect_first_name=request.prospect_first_name,
                prospect_last_name=request.prospect_last_name,
                prospect_title=request.prospect_title,
                company_name=request.company_name,
                company_domain=request.company_domain,
                email_sequence=email_sequence,
                linkedin_sequence=linkedin_sequence,
                company_insights=request.company_data,
                prospect_insights=request.prospect_data,
            )

            # Store campaign
            self._campaigns[campaign.id] = campaign

            return CampaignGenerateResponse(
                success=True,
                campaign=campaign,
            )

        except Exception as e:
            logger.error(f"Error generating campaign: {e}")
            return CampaignGenerateResponse(
                success=False,
                error=str(e),
            )

    def _build_context(self, request: CampaignGenerateRequest) -> str:
        """Build context string for AI generation."""
        context_parts = []

        # Prospect info
        context_parts.append(f"Prospect: {request.prospect_name}")
        if request.prospect_title:
            context_parts.append(f"Title: {request.prospect_title}")
        context_parts.append(f"Company: {request.company_name}")
        if request.company_domain:
            context_parts.append(f"Domain: {request.company_domain}")

        # Company data
        if request.company_data:
            context_parts.append("\nCompany Information:")
            if request.company_data.get("description"):
                context_parts.append(f"Description: {request.company_data['description']}")
            if request.company_data.get("industry"):
                context_parts.append(f"Industry: {request.company_data['industry']}")
            if request.company_data.get("employee_count"):
                context_parts.append(f"Size: {request.company_data['employee_count']} employees")

        # Web research
        if request.web_research:
            context_parts.append("\nWeb Research:")
            if request.web_research.get("news_results"):
                context_parts.append("Recent News:")
                for news in request.web_research.get("news_results", [])[:3]:
                    if news.get("title"):
                        context_parts.append(f"- {news['title']}")

        # AI insights
        if request.ai_insights:
            context_parts.append("\nAI Insights:")
            if request.ai_insights.get("key_findings"):
                for finding in request.ai_insights.get("key_findings", [])[:3]:
                    context_parts.append(f"- {finding}")
            if request.ai_insights.get("pain_points"):
                context_parts.append("Potential Pain Points:")
                for pain in request.ai_insights.get("pain_points", [])[:3]:
                    context_parts.append(f"- {pain}")

        # Product/sender info
        if request.product_info:
            context_parts.append("\nOur Product/Service:")
            if request.product_info.get("name"):
                context_parts.append(f"Name: {request.product_info['name']}")
            if request.product_info.get("description"):
                context_parts.append(f"Description: {request.product_info['description']}")
            if request.product_info.get("value_props"):
                context_parts.append("Value Propositions:")
                for vp in request.product_info.get("value_props", []):
                    context_parts.append(f"- {vp}")

        if request.sender_info:
            context_parts.append("\nSender:")
            if request.sender_info.get("name"):
                context_parts.append(f"Name: {request.sender_info['name']}")
            if request.sender_info.get("title"):
                context_parts.append(f"Title: {request.sender_info['title']}")

        return "\n".join(context_parts)

    async def _generate_email_sequence(
        self,
        request: CampaignGenerateRequest,
        context: str,
        num_steps: int,
    ) -> OutreachSequence:
        """Generate an email outreach sequence."""
        first_name = request.prospect_first_name or request.prospect_name.split()[0]

        prompt = f"""Generate a {num_steps}-step cold email sequence for outreach to a prospect.

Context:
{context}

Requirements:
1. Create {num_steps} emails with appropriate delays between them
2. First email should be personalized and reference something specific about their company
3. Follow-up emails should add value, not just "checking in"
4. Tone should be {request.tone}
5. Keep emails concise (under 150 words each)
6. Include clear but subtle call-to-action

Return the sequence as JSON in this exact format:
{{
    "steps": [
        {{
            "step_number": 1,
            "delay_days": 0,
            "subject": "Email subject line",
            "body": "Email body with {{{{first_name}}}} personalization tokens"
        }},
        {{
            "step_number": 2,
            "delay_days": 3,
            "subject": "Follow up subject",
            "body": "Follow up body"
        }}
    ]
}}

Use {{{{first_name}}}}, {{{{company_name}}}}, and {{{{title}}}} as personalization tokens.
Return only valid JSON, no additional text."""

        try:
            response = await self.claude_client.generate_text(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
            )

            if response:
                # Clean up response
                response_text = response.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                data = json.loads(response_text.strip())
                steps = [
                    OutreachStep(
                        step_number=step["step_number"],
                        channel="email",
                        delay_days=step.get("delay_days", 0),
                        subject=step.get("subject"),
                        body=step["body"],
                        personalization_fields=["first_name", "company_name", "title"],
                    )
                    for step in data.get("steps", [])
                ]

                return OutreachSequence(
                    name=f"Email Sequence for {request.prospect_name}",
                    format=OutreachFormat.EMAIL,
                    steps=steps,
                )

        except Exception as e:
            logger.error(f"Error generating email sequence: {e}")

        # Return default sequence on failure
        return OutreachSequence(
            name=f"Email Sequence for {request.prospect_name}",
            format=OutreachFormat.EMAIL,
            steps=[
                OutreachStep(
                    step_number=1,
                    channel="email",
                    delay_days=0,
                    subject=f"Quick question about {request.company_name}",
                    body=f"Hi {{{{first_name}}}},\n\nI noticed {{{{company_name}}}} is doing interesting work in the industry. I'd love to learn more about your current priorities and see if there's a way we can help.\n\nWould you be open to a brief chat this week?\n\nBest regards",
                    personalization_fields=["first_name", "company_name"],
                ),
            ],
        )

    async def _generate_linkedin_sequence(
        self,
        request: CampaignGenerateRequest,
        context: str,
        num_steps: int,
    ) -> OutreachSequence:
        """Generate a LinkedIn outreach sequence."""
        first_name = request.prospect_first_name or request.prospect_name.split()[0]

        prompt = f"""Generate a {num_steps}-step LinkedIn outreach sequence for connecting with and messaging a prospect.

Context:
{context}

Requirements:
1. First step should be a connection request with a personalized note (under 300 characters)
2. Follow-up steps should be LinkedIn messages sent after connection is accepted
3. Messages should be conversational and appropriate for LinkedIn
4. Tone should be {request.tone}
5. Keep messages concise (under 100 words each)

Return the sequence as JSON in this exact format:
{{
    "steps": [
        {{
            "step_number": 1,
            "channel": "linkedin_connection",
            "delay_days": 0,
            "body": "Connection request note"
        }},
        {{
            "step_number": 2,
            "channel": "linkedin_message",
            "delay_days": 2,
            "body": "Follow up message after connection"
        }}
    ]
}}

Use {{{{first_name}}}}, {{{{company_name}}}}, and {{{{title}}}} as personalization tokens.
Return only valid JSON, no additional text."""

        try:
            response = await self.claude_client.generate_text(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.7,
            )

            if response:
                response_text = response.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                data = json.loads(response_text.strip())
                steps = [
                    OutreachStep(
                        step_number=step["step_number"],
                        channel=step.get("channel", "linkedin_message"),
                        delay_days=step.get("delay_days", 0),
                        body=step["body"],
                        personalization_fields=["first_name", "company_name", "title"],
                    )
                    for step in data.get("steps", [])
                ]

                return OutreachSequence(
                    name=f"LinkedIn Sequence for {request.prospect_name}",
                    format=OutreachFormat.LINKEDIN,
                    steps=steps,
                )

        except Exception as e:
            logger.error(f"Error generating LinkedIn sequence: {e}")

        # Return default sequence on failure
        return OutreachSequence(
            name=f"LinkedIn Sequence for {request.prospect_name}",
            format=OutreachFormat.LINKEDIN,
            steps=[
                OutreachStep(
                    step_number=1,
                    channel="linkedin_connection",
                    delay_days=0,
                    body=f"Hi {{{{first_name}}}}, I came across your profile and was impressed by your work at {{{{company_name}}}}. Would love to connect!",
                    personalization_fields=["first_name", "company_name"],
                ),
            ],
        )

    def get_campaign(self, campaign_id: str) -> Optional[OutreachCampaign]:
        """Get a campaign by ID."""
        return self._campaigns.get(campaign_id)

    def list_campaigns(self) -> list[OutreachCampaign]:
        """List all campaigns."""
        return list(self._campaigns.values())

    def export_to_instantly(self, campaign: OutreachCampaign) -> str:
        """
        Export campaign to Instantly CSV format.

        Returns CSV string for Instantly import.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Instantly CSV headers
        headers = [
            "email",
            "first_name",
            "last_name",
            "company_name",
            "personalization1",
            "personalization2",
            "personalization3",
            "personalization4",
            "personalization5",
        ]
        writer.writerow(headers)

        # Build personalization fields
        personalizations = []
        if campaign.email_sequence and campaign.email_sequence.steps:
            for i, step in enumerate(campaign.email_sequence.steps[:5]):
                # Store the email body as personalization
                personalizations.append(step.body)

        # Pad to 5 personalizations
        while len(personalizations) < 5:
            personalizations.append("")

        # Write row
        row = InstantlyCSVRow(
            email=campaign.prospect_email,
            first_name=campaign.prospect_first_name,
            last_name=campaign.prospect_last_name,
            company_name=campaign.company_name,
            personalization1=personalizations[0] if personalizations else None,
            personalization2=personalizations[1] if len(personalizations) > 1 else None,
            personalization3=personalizations[2] if len(personalizations) > 2 else None,
            personalization4=personalizations[3] if len(personalizations) > 3 else None,
            personalization5=personalizations[4] if len(personalizations) > 4 else None,
        )

        writer.writerow([
            row.email,
            row.first_name or "",
            row.last_name or "",
            row.company_name or "",
            row.personalization1 or "",
            row.personalization2 or "",
            row.personalization3 or "",
            row.personalization4 or "",
            row.personalization5 or "",
        ])

        return output.getvalue()

    def export_to_heyreach(self, campaign: OutreachCampaign) -> str:
        """
        Export campaign to HeyReach CSV format.

        Returns CSV string for HeyReach import.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # HeyReach CSV headers
        headers = [
            "linkedin_url",
            "first_name",
            "last_name",
            "email",
            "company",
            "title",
            "personalization_snippet",
            "custom_message",
        ]
        writer.writerow(headers)

        # Get first LinkedIn message for personalization
        custom_message = ""
        personalization = ""
        if campaign.linkedin_sequence and campaign.linkedin_sequence.steps:
            first_step = campaign.linkedin_sequence.steps[0]
            custom_message = first_step.body
            # Extract key insight for personalization snippet
            if campaign.company_insights:
                if campaign.company_insights.get("description"):
                    personalization = campaign.company_insights["description"][:100]

        row = HeyReachCSVRow(
            linkedin_url=None,  # Would need to be enriched
            first_name=campaign.prospect_first_name,
            last_name=campaign.prospect_last_name,
            email=campaign.prospect_email,
            company=campaign.company_name,
            title=campaign.prospect_title,
            personalization_snippet=personalization,
            custom_message=custom_message,
        )

        writer.writerow([
            row.linkedin_url or "",
            row.first_name or "",
            row.last_name or "",
            row.email or "",
            row.company or "",
            row.title or "",
            row.personalization_snippet or "",
            row.custom_message or "",
        ])

        return output.getvalue()

    def export_campaign(
        self,
        campaign: OutreachCampaign,
        format: ExportFormat,
    ) -> str:
        """Export campaign to specified format."""
        if format == ExportFormat.INSTANTLY:
            return self.export_to_instantly(campaign)
        elif format == ExportFormat.HEYREACH:
            return self.export_to_heyreach(campaign)
        else:
            # Generic CSV
            return self.export_to_instantly(campaign)


# Singleton instance
_outreach_service: Optional[OutreachService] = None


def get_outreach_service() -> OutreachService:
    """Get or create outreach service instance."""
    global _outreach_service
    if _outreach_service is None:
        _outreach_service = OutreachService()
    return _outreach_service
