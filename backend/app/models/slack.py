"""
Slack integration models for Sales OS.

This module contains Pydantic models for:
- Slack OAuth2 workspace connections
- Channel and DM notifications
- Slash command requests/responses
- Interactive message payloads
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# === Enums ===


class SlackNotificationType(str, Enum):
    """Types of notifications that can be sent to Slack."""

    CALL_PROCESSED = "call_processed"
    CONTENT_READY = "content_ready"
    COACHING_FEEDBACK = "coaching_feedback"
    PROSPECT_ENRICHED = "prospect_enriched"
    FOLLOW_UP_REMINDER = "follow_up_reminder"


class SlackEventType(str, Enum):
    """Slack event types we handle."""

    URL_VERIFICATION = "url_verification"
    EVENT_CALLBACK = "event_callback"
    APP_MENTION = "app_mention"
    MESSAGE = "message"
    APP_HOME_OPENED = "app_home_opened"


class InteractionType(str, Enum):
    """Types of interactive Slack components."""

    BLOCK_ACTIONS = "block_actions"
    VIEW_SUBMISSION = "view_submission"
    SHORTCUT = "shortcut"
    MESSAGE_ACTION = "message_action"


# === OAuth2 Models ===


class SlackOAuthRequest(BaseModel):
    """Request model for initiating Slack OAuth2 flow."""

    redirect_uri: str = Field(..., description="URI to redirect after authorization")
    state: Optional[str] = Field(None, description="CSRF protection state parameter")


class SlackOAuthCallback(BaseModel):
    """Callback data from Slack OAuth2 authorization."""

    code: str = Field(..., description="Authorization code from Slack")
    state: Optional[str] = Field(None, description="State parameter for verification")


class SlackOAuthTokenResponse(BaseModel):
    """Response from Slack token exchange."""

    ok: bool
    access_token: str
    token_type: str = "bot"
    scope: str
    bot_user_id: str
    app_id: str
    team: dict
    authed_user: dict
    enterprise: Optional[dict] = None
    is_enterprise_install: bool = False


class SlackWorkspaceConnection(BaseModel):
    """Represents a connected Slack workspace."""

    id: Optional[str] = Field(None, description="Internal connection ID")
    team_id: str = Field(..., description="Slack workspace/team ID")
    team_name: str = Field(..., description="Workspace name")
    bot_user_id: str = Field(..., description="Bot user ID in the workspace")
    bot_access_token: str = Field(..., description="Bot OAuth access token")
    app_id: str = Field(..., description="Slack app ID")
    scopes: list[str] = Field(default_factory=list, description="Granted OAuth scopes")
    installing_user_id: str = Field(..., description="User who installed the app")
    organization_id: Optional[str] = Field(
        None, description="Sales OS organization ID"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


# === User Models ===


class SlackUserProfile(BaseModel):
    """Slack user profile information."""

    user_id: str = Field(..., description="Slack user ID")
    team_id: str = Field(..., description="Slack workspace ID")
    email: Optional[str] = Field(None, description="User's email")
    name: str = Field(..., description="Display name")
    real_name: Optional[str] = Field(None, description="Real name")


class SlackUserMapping(BaseModel):
    """Maps a Slack user to a Sales OS user."""

    id: Optional[str] = Field(None, description="Internal mapping ID")
    slack_user_id: str = Field(..., description="Slack user ID")
    slack_team_id: str = Field(..., description="Slack workspace ID")
    sales_os_user_id: str = Field(..., description="Sales OS user ID")
    notification_preferences: dict = Field(
        default_factory=lambda: {
            "call_processed": True,
            "content_ready": True,
            "coaching_feedback": True,
            "dm_enabled": True,
        }
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# === Notification Models ===


class SlackNotificationTarget(BaseModel):
    """Target for a Slack notification."""

    channel_id: Optional[str] = Field(None, description="Channel ID for notifications")
    user_id: Optional[str] = Field(None, description="User ID for DM notifications")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp for replies")


class SlackNotification(BaseModel):
    """A notification to be sent to Slack."""

    notification_type: SlackNotificationType
    target: SlackNotificationTarget
    title: str = Field(..., description="Notification title/header")
    message: str = Field(..., description="Main notification message")
    metadata: dict = Field(default_factory=dict, description="Additional data")
    blocks: Optional[list[dict]] = Field(
        None, description="Slack Block Kit blocks for rich formatting"
    )
    attachments: Optional[list[dict]] = Field(None, description="Legacy attachments")


class SlackNotificationResult(BaseModel):
    """Result of sending a Slack notification."""

    ok: bool
    channel: Optional[str] = None
    ts: Optional[str] = Field(None, description="Message timestamp")
    message: Optional[dict] = None
    error: Optional[str] = None


# === Channel Models ===


class SlackChannelConfig(BaseModel):
    """Configuration for a Slack channel's notification settings."""

    id: Optional[str] = Field(None, description="Internal config ID")
    channel_id: str = Field(..., description="Slack channel ID")
    channel_name: str = Field(..., description="Channel name")
    team_id: str = Field(..., description="Slack workspace ID")
    organization_id: str = Field(..., description="Sales OS organization ID")
    notification_types: list[SlackNotificationType] = Field(
        default_factory=list, description="Types of notifications enabled"
    )
    is_default: bool = Field(
        False, description="Whether this is the default notification channel"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# === Slash Command Models ===


class SlashCommandRequest(BaseModel):
    """Incoming slash command from Slack."""

    token: str = Field(..., description="Verification token (deprecated)")
    team_id: str = Field(..., description="Workspace ID")
    team_domain: str = Field(..., description="Workspace domain")
    channel_id: str = Field(..., description="Channel where command was invoked")
    channel_name: str = Field(..., description="Channel name")
    user_id: str = Field(..., description="User who invoked the command")
    user_name: str = Field(..., description="Username")
    command: str = Field(..., description="The slash command (e.g., /salesos)")
    text: str = Field("", description="Text after the command")
    response_url: str = Field(..., description="URL for delayed responses")
    trigger_id: str = Field(..., description="Trigger ID for modals")
    api_app_id: str = Field(..., description="App ID")


class SlashCommandResponse(BaseModel):
    """Response to a slash command."""

    response_type: str = Field(
        "ephemeral", description="ephemeral (private) or in_channel (public)"
    )
    text: Optional[str] = Field(None, description="Simple text response")
    blocks: Optional[list[dict]] = Field(None, description="Block Kit blocks")
    attachments: Optional[list[dict]] = Field(None, description="Attachments")


# === Interactive Message Models ===


class InteractionUser(BaseModel):
    """User who triggered an interaction."""

    id: str
    username: str
    name: str
    team_id: str


class InteractionChannel(BaseModel):
    """Channel where interaction occurred."""

    id: str
    name: str


class InteractionAction(BaseModel):
    """An action from an interactive component."""

    action_id: str = Field(..., description="Unique action identifier")
    block_id: Optional[str] = Field(None, description="Block containing the action")
    type: str = Field(..., description="Action type (button, select, etc.)")
    value: Optional[str] = Field(None, description="Action value")
    selected_option: Optional[dict] = Field(None, description="For select menus")
    action_ts: str = Field(..., description="Action timestamp")


class InteractionPayload(BaseModel):
    """Payload from an interactive Slack component."""

    type: InteractionType
    user: InteractionUser
    channel: Optional[InteractionChannel] = None
    trigger_id: str
    response_url: str
    actions: list[InteractionAction] = Field(default_factory=list)
    message: Optional[dict] = Field(None, description="Original message")
    view: Optional[dict] = Field(None, description="Modal view data")
    container: Optional[dict] = None
    api_app_id: str
    token: str
    team: dict


# === Event Models ===


class SlackEventChallenge(BaseModel):
    """URL verification challenge from Slack."""

    token: str
    challenge: str
    type: str = "url_verification"


class SlackEventWrapper(BaseModel):
    """Wrapper for Slack event callbacks."""

    token: str
    team_id: str
    api_app_id: str
    event: dict = Field(..., description="The actual event payload")
    type: str = Field(..., description="Event type")
    event_id: str
    event_time: int
    authorizations: Optional[list[dict]] = None
    is_ext_shared_channel: bool = False


class AppMentionEvent(BaseModel):
    """Event when the app is mentioned in a channel."""

    type: str = "app_mention"
    user: str = Field(..., description="User who mentioned the app")
    text: str = Field(..., description="Full message text")
    ts: str = Field(..., description="Message timestamp")
    channel: str = Field(..., description="Channel ID")
    event_ts: str
    thread_ts: Optional[str] = Field(None, description="Thread timestamp if in thread")


# === Action-specific Models ===


class ApproveFollowUpAction(BaseModel):
    """Action data for approving a follow-up."""

    call_id: str = Field(..., description="The call ID to approve follow-up for")
    follow_up_type: str = Field(..., description="Type of follow-up (email, task)")
    approved_by: str = Field(..., description="Slack user ID who approved")


class ViewSummaryAction(BaseModel):
    """Action data for viewing a call summary."""

    call_id: str = Field(..., description="The call ID to view")
    summary_type: str = Field(
        "brief", description="Summary detail level (brief, full)"
    )


# === Prep/Coach Command Models ===


class PrepCommandRequest(BaseModel):
    """Request for /salesos prep command."""

    company_name: Optional[str] = Field(None, description="Company to prep for")
    contact_name: Optional[str] = Field(None, description="Contact to prep for")
    meeting_id: Optional[str] = Field(None, description="Meeting ID if available")


class PrepCommandResponse(BaseModel):
    """Response for /salesos prep command."""

    company_info: Optional[dict] = Field(None, description="Company research data")
    contact_info: Optional[dict] = Field(None, description="Contact details")
    recent_interactions: list[dict] = Field(
        default_factory=list, description="Recent call summaries"
    )
    suggested_topics: list[str] = Field(
        default_factory=list, description="Suggested discussion topics"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Important alerts/warnings"
    )


class CoachCommandRequest(BaseModel):
    """Request for /salesos coach command."""

    call_id: Optional[str] = Field(None, description="Specific call to coach on")
    topic: Optional[str] = Field(
        None, description="Coaching topic (objections, discovery, closing)"
    )


class CoachCommandResponse(BaseModel):
    """Response for /salesos coach command."""

    call_id: Optional[str] = Field(None, description="Call being coached on")
    spiced_scores: Optional[dict] = Field(None, description="SPICED methodology scores")
    strengths: list[str] = Field(
        default_factory=list, description="Areas of strength"
    )
    improvements: list[str] = Field(
        default_factory=list, description="Areas for improvement"
    )
    tips: list[str] = Field(default_factory=list, description="Actionable coaching tips")
    resources: list[dict] = Field(
        default_factory=list, description="Relevant training resources"
    )
