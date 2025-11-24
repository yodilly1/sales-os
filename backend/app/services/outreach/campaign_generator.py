"""Campaign generator service for creating personalized outreach sequences using Claude."""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.services.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


class EmailMessage(BaseModel):
    """Single email in a sequence."""

    email_number: int
    subject: str
    body: str
    delay_days: int = Field(description="Days to wait before sending this email")


class EmailSequence(BaseModel):
    """Complete email sequence for Instantly."""

    emails: list[EmailMessage]
    total_emails: int = 3


class LinkedInMessage(BaseModel):
    """Single LinkedIn message in a sequence."""

    message_type: str = Field(description="Type: connection_request, followup_1, followup_2")
    message: str
    delay_days: int = Field(description="Days to wait before sending this message")


class LinkedInSequence(BaseModel):
    """Complete LinkedIn sequence for HeyReach."""

    connection_request: str
    followup_1: str
    followup_2: str
    messages: list[LinkedInMessage]


class ProspectInfo(BaseModel):
    """Prospect information for campaign generation."""

    prospect_id: str
    prospect_email: Optional[str] = None
    prospect_name: str
    prospect_title: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    company_industry: Optional[str] = None
    company_size: Optional[str] = None
    linkedin_url: Optional[str] = None
    recent_news: Optional[str] = None
    pain_points: Optional[list[str]] = None


class OutreachCampaign(BaseModel):
    """Complete outreach campaign with both email and LinkedIn sequences."""

    campaign_id: str
    prospect_id: str
    prospect_name: str
    prospect_email: Optional[str] = None
    company_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    email_sequence: EmailSequence
    linkedin_sequence: LinkedInSequence
    created_at: datetime = Field(default_factory=datetime.utcnow)


# In-memory storage for campaigns (in production, use database)
_campaigns_store: dict[str, OutreachCampaign] = {}


class CampaignGenerator:
    """Service for generating personalized outreach campaigns using Claude AI."""

    # Words to avoid in messages - they sound too AI-generated
    BANNED_WORDS = [
        "leverage", "streamline", "optimize", "synergy", "paradigm",
        "disruptive", "revolutionary", "cutting-edge", "game-changer",
        "best-in-class", "world-class", "leading", "innovative",
        "transform", "empower", "unlock", "elevate", "amplify",
        "seamless", "robust", "scalable", "holistic", "proactive"
    ]

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize the campaign generator.

        Args:
            claude_client: Optional Claude client instance.
        """
        self.claude_client = claude_client or ClaudeClient()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for campaign generation."""
        return """You are an expert B2B sales copywriter who writes highly personalized, human-sounding outreach messages.

Your messages must:
1. Sound like a real person wrote them, not an AI
2. Be concise and respect the recipient's time
3. Reference specific details about the prospect and their company
4. Avoid corporate buzzwords and jargon
5. Have a clear, specific value proposition
6. Include a soft call-to-action

BANNED WORDS - Never use these:
- leverage, streamline, optimize, synergy, paradigm
- disruptive, revolutionary, cutting-edge, game-changer
- best-in-class, world-class, leading, innovative
- transform, empower, unlock, elevate, amplify
- seamless, robust, scalable, holistic, proactive

Write like you're sending a message to a colleague, not a sales pitch.
Be direct, friendly, and genuinely helpful."""

    async def generate_email_sequence(
        self,
        prospect: ProspectInfo,
        num_emails: int = 3,
    ) -> EmailSequence:
        """Generate a personalized email sequence.

        Args:
            prospect: Prospect information.
            num_emails: Number of emails in the sequence.

        Returns:
            EmailSequence with personalized emails.
        """
        first_name = prospect.first_name or prospect.prospect_name.split()[0]

        prompt = f"""Generate a {num_emails}-email sales sequence for this prospect:

PROSPECT INFO:
- Name: {prospect.prospect_name}
- First Name: {first_name}
- Title: {prospect.prospect_title or 'Unknown'}
- Email: {prospect.prospect_email or 'Unknown'}
- Company: {prospect.company_name or 'Unknown'}
- Company Description: {prospect.company_description or 'Unknown'}
- Industry: {prospect.company_industry or 'Unknown'}
- Company Size: {prospect.company_size or 'Unknown'}
{f'- Recent News: {prospect.recent_news}' if prospect.recent_news else ''}
{f'- Known Pain Points: {", ".join(prospect.pain_points)}' if prospect.pain_points else ''}

GUIDELINES:
1. Email 1: Opening - Reference something specific about them or their company. Ask a question.
2. Email 2: Value add - Share a relevant insight or resource. Don't pitch.
3. Email 3: Direct ask - Clear call to action for a brief conversation.

Keep each email under 100 words. Use their first name. Be human.

Return as JSON:
{{
  "emails": [
    {{
      "email_number": 1,
      "subject": "Subject line here",
      "body": "Email body here",
      "delay_days": 0
    }},
    {{
      "email_number": 2,
      "subject": "Subject line here",
      "body": "Email body here",
      "delay_days": 3
    }},
    {{
      "email_number": 3,
      "subject": "Subject line here",
      "body": "Email body here",
      "delay_days": 5
    }}
  ]
}}"""

        try:
            json_content, _ = await self.claude_client.generate_json(
                prompt=prompt,
                system_prompt=self._get_system_prompt(),
                max_tokens=2048,
                temperature=0.7,
            )

            emails = [
                EmailMessage(
                    email_number=e.get("email_number", i + 1),
                    subject=e.get("subject", ""),
                    body=e.get("body", ""),
                    delay_days=e.get("delay_days", i * 3),
                )
                for i, e in enumerate(json_content.get("emails", []))
            ]

            return EmailSequence(emails=emails, total_emails=len(emails))

        except Exception as e:
            logger.error(f"Failed to generate email sequence: {e}")
            # Return fallback sequence
            return self._get_fallback_email_sequence(prospect)

    async def generate_linkedin_sequence(
        self,
        prospect: ProspectInfo,
    ) -> LinkedInSequence:
        """Generate a personalized LinkedIn sequence.

        Args:
            prospect: Prospect information.

        Returns:
            LinkedInSequence with personalized messages.
        """
        first_name = prospect.first_name or prospect.prospect_name.split()[0]

        prompt = f"""Generate a LinkedIn outreach sequence for this prospect:

PROSPECT INFO:
- Name: {prospect.prospect_name}
- First Name: {first_name}
- Title: {prospect.prospect_title or 'Unknown'}
- Company: {prospect.company_name or 'Unknown'}
- Company Description: {prospect.company_description or 'Unknown'}
- Industry: {prospect.company_industry or 'Unknown'}
{f'- Recent News: {prospect.recent_news}' if prospect.recent_news else ''}

GUIDELINES:
1. Connection Request (max 300 chars): Brief, personal reason to connect. No pitch.
2. Follow-up 1 (after accepted): Thank them, share something valuable related to their work.
3. Follow-up 2: Soft ask for a quick conversation if they're open to it.

Be conversational and genuine. No corporate speak.

Return as JSON:
{{
  "connection_request": "Connection request message here (max 300 chars)",
  "followup_1": "First follow-up message here",
  "followup_2": "Second follow-up message here"
}}"""

        try:
            json_content, _ = await self.claude_client.generate_json(
                prompt=prompt,
                system_prompt=self._get_system_prompt(),
                max_tokens=1024,
                temperature=0.7,
            )

            connection_request = json_content.get("connection_request", "")
            followup_1 = json_content.get("followup_1", "")
            followup_2 = json_content.get("followup_2", "")

            messages = [
                LinkedInMessage(
                    message_type="connection_request",
                    message=connection_request,
                    delay_days=0,
                ),
                LinkedInMessage(
                    message_type="followup_1",
                    message=followup_1,
                    delay_days=2,
                ),
                LinkedInMessage(
                    message_type="followup_2",
                    message=followup_2,
                    delay_days=5,
                ),
            ]

            return LinkedInSequence(
                connection_request=connection_request,
                followup_1=followup_1,
                followup_2=followup_2,
                messages=messages,
            )

        except Exception as e:
            logger.error(f"Failed to generate LinkedIn sequence: {e}")
            return self._get_fallback_linkedin_sequence(prospect)

    async def generate_campaign(
        self,
        prospect: ProspectInfo,
    ) -> OutreachCampaign:
        """Generate a complete outreach campaign with email and LinkedIn sequences.

        Args:
            prospect: Prospect information.

        Returns:
            OutreachCampaign with both sequences.
        """
        # Parse first/last name if not provided
        if not prospect.first_name:
            name_parts = prospect.prospect_name.split()
            prospect.first_name = name_parts[0] if name_parts else ""
            prospect.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Generate both sequences
        email_sequence = await self.generate_email_sequence(prospect)
        linkedin_sequence = await self.generate_linkedin_sequence(prospect)

        campaign_id = str(uuid.uuid4())

        campaign = OutreachCampaign(
            campaign_id=campaign_id,
            prospect_id=prospect.prospect_id,
            prospect_name=prospect.prospect_name,
            prospect_email=prospect.prospect_email,
            company_name=prospect.company_name,
            linkedin_url=prospect.linkedin_url,
            email_sequence=email_sequence,
            linkedin_sequence=linkedin_sequence,
        )

        # Store campaign
        _campaigns_store[campaign_id] = campaign

        return campaign

    def _get_fallback_email_sequence(self, prospect: ProspectInfo) -> EmailSequence:
        """Generate a fallback email sequence if Claude fails."""
        first_name = prospect.first_name or prospect.prospect_name.split()[0]
        company = prospect.company_name or "your company"

        return EmailSequence(
            emails=[
                EmailMessage(
                    email_number=1,
                    subject=f"Quick question about {company}",
                    body=f"Hi {first_name},\n\nI came across {company} and was curious about how you're currently handling [relevant challenge].\n\nWould love to learn more about what's working for you.\n\nBest,\n[Your name]",
                    delay_days=0,
                ),
                EmailMessage(
                    email_number=2,
                    subject=f"Thought you might find this useful",
                    body=f"Hi {first_name},\n\nI wanted to share a quick resource that might be helpful given what {company} is working on.\n\n[Resource link]\n\nNo strings attached - just thought it was relevant.\n\nBest,\n[Your name]",
                    delay_days=3,
                ),
                EmailMessage(
                    email_number=3,
                    subject=f"Worth a quick chat?",
                    body=f"Hi {first_name},\n\nI know you're busy, so I'll keep this brief.\n\nWould you be open to a 15-minute call this week to discuss [specific topic]?\n\nIf not, no worries at all.\n\nBest,\n[Your name]",
                    delay_days=5,
                ),
            ],
            total_emails=3,
        )

    def _get_fallback_linkedin_sequence(self, prospect: ProspectInfo) -> LinkedInSequence:
        """Generate a fallback LinkedIn sequence if Claude fails."""
        first_name = prospect.first_name or prospect.prospect_name.split()[0]
        company = prospect.company_name or "your company"
        title = prospect.prospect_title or "your role"

        connection_request = f"Hi {first_name}, I've been following {company}'s work and would love to connect. Always great to meet others in the space."
        followup_1 = f"Thanks for connecting, {first_name}! I noticed you're working on some interesting things at {company}. Would love to hear more about your work as {title}."
        followup_2 = f"Hi {first_name}, I hope things are going well. Would you be open to a quick chat sometime? I think we might have some interesting things to discuss."

        return LinkedInSequence(
            connection_request=connection_request,
            followup_1=followup_1,
            followup_2=followup_2,
            messages=[
                LinkedInMessage(
                    message_type="connection_request",
                    message=connection_request,
                    delay_days=0,
                ),
                LinkedInMessage(
                    message_type="followup_1",
                    message=followup_1,
                    delay_days=2,
                ),
                LinkedInMessage(
                    message_type="followup_2",
                    message=followup_2,
                    delay_days=5,
                ),
            ],
        )


def get_campaign(campaign_id: str) -> Optional[OutreachCampaign]:
    """Get a campaign by ID from storage."""
    return _campaigns_store.get(campaign_id)


def get_campaign_generator() -> CampaignGenerator:
    """Get campaign generator instance."""
    return CampaignGenerator()


async def generate_campaign(prospect: ProspectInfo) -> OutreachCampaign:
    """Convenience function to generate a campaign.

    Args:
        prospect: Prospect information.

    Returns:
        OutreachCampaign with email and LinkedIn sequences.
    """
    generator = CampaignGenerator()
    return await generator.generate_campaign(prospect)
