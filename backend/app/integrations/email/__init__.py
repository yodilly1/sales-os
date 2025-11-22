"""
Email Integration for Sales OS

This module provides email sending, tracking, and management capabilities
using SendGrid or Amazon SES as the underlying email service provider.
"""

from .service import EmailService
from .providers.base import EmailProviderBase
from .providers.sendgrid import SendGridProvider
from .providers.ses import SESProvider
from .tracking import TrackingService
from .bounce_handler import BounceHandler
from .unsubscribe_manager import UnsubscribeManager
from .template_renderer import TemplateRenderer, DefaultTemplates
from .workflows import (
    PostCallFollowUpWorkflow,
    ContentDeliveryWorkflow,
    OutreachSequenceWorkflow,
    FollowUpRequest,
    ContentDeliveryRequest,
    ProspectForSequence,
    create_email_workflows,
)

__all__ = [
    # Core services
    "EmailService",
    "EmailProviderBase",
    "SendGridProvider",
    "SESProvider",
    "TrackingService",
    "BounceHandler",
    "UnsubscribeManager",
    "TemplateRenderer",
    "DefaultTemplates",
    # Workflows
    "PostCallFollowUpWorkflow",
    "ContentDeliveryWorkflow",
    "OutreachSequenceWorkflow",
    "FollowUpRequest",
    "ContentDeliveryRequest",
    "ProspectForSequence",
    "create_email_workflows",
]
