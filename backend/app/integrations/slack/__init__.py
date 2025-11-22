"""
Slack integration for Sales OS.

This module provides:
- OAuth2 workspace connection
- Channel and DM notifications
- Slash commands (/salesos prep, /salesos coach)
- Interactive messages (approve follow-up, view summary)
"""

from app.integrations.slack.client import (
    SlackAPIError,
    SlackClient,
    create_client,
    create_client_for_workspace,
)
from app.integrations.slack.config import (
    SlackSettings,
    get_settings,
    get_slack_settings,
)
from app.integrations.slack.handlers import (
    EventHandler,
    InteractiveHandler,
    SlashCommandHandler,
    create_event_handler,
    create_interactive_handler,
    create_slash_handler,
)
from app.integrations.slack.messages import (
    build_call_processed_notification,
    build_coach_response,
    build_coaching_feedback_notification,
    build_content_ready_notification,
    build_error_response,
    build_help_response,
    build_notification_blocks,
    build_prep_response,
    build_prospect_enriched_notification,
    build_summary_modal,
)

__all__ = [
    # Client
    "SlackClient",
    "SlackAPIError",
    "create_client",
    "create_client_for_workspace",
    # Config
    "SlackSettings",
    "get_settings",
    "get_slack_settings",
    # Handlers
    "SlashCommandHandler",
    "InteractiveHandler",
    "EventHandler",
    "create_slash_handler",
    "create_interactive_handler",
    "create_event_handler",
    # Messages
    "build_call_processed_notification",
    "build_content_ready_notification",
    "build_coaching_feedback_notification",
    "build_prospect_enriched_notification",
    "build_help_response",
    "build_prep_response",
    "build_coach_response",
    "build_error_response",
    "build_summary_modal",
    "build_notification_blocks",
]
