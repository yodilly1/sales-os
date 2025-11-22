"""
Data Models for Sales OS

Pydantic models for API validation and data transfer.
"""

from .email import (
    # Enums
    EmailStatus,
    EmailProvider,
    EmailEventType,
    BounceType,
    EmailTemplateType,
    UnsubscribeReason,
    # Base models
    EmailRecipient,
    EmailAttachment,
    TrackingPixel,
    LinkTracking,
    TemplateVariable,
    # Email message models
    EmailMessageBase,
    EmailMessageCreate,
    EmailMessage,
    # Template models
    EmailTemplateBase,
    EmailTemplateCreate,
    EmailTemplate,
    # Event models
    EmailEventBase,
    EmailEvent,
    # Unsubscribe models
    UnsubscribeBase,
    UnsubscribeCreate,
    Unsubscribe,
    # Bounce models
    BounceRecord,
    # Campaign models
    EmailCampaignBase,
    EmailCampaign,
    OutreachSequenceStep,
    OutreachSequenceBase,
    OutreachSequence,
    # Response models
    SendEmailResponse,
    EmailStatsResponse,
    WebhookPayload,
)

__all__ = [
    # Enums
    "EmailStatus",
    "EmailProvider",
    "EmailEventType",
    "BounceType",
    "EmailTemplateType",
    "UnsubscribeReason",
    # Base models
    "EmailRecipient",
    "EmailAttachment",
    "TrackingPixel",
    "LinkTracking",
    "TemplateVariable",
    # Email message models
    "EmailMessageBase",
    "EmailMessageCreate",
    "EmailMessage",
    # Template models
    "EmailTemplateBase",
    "EmailTemplateCreate",
    "EmailTemplate",
    # Event models
    "EmailEventBase",
    "EmailEvent",
    # Unsubscribe models
    "UnsubscribeBase",
    "UnsubscribeCreate",
    "Unsubscribe",
    # Bounce models
    "BounceRecord",
    # Campaign models
    "EmailCampaignBase",
    "EmailCampaign",
    "OutreachSequenceStep",
    "OutreachSequenceBase",
    "OutreachSequence",
    # Response models
    "SendEmailResponse",
    "EmailStatsResponse",
    "WebhookPayload",
]
