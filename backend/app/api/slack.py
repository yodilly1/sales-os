"""
Slack API routes for Sales OS.

This module provides FastAPI routes for:
- OAuth2 workspace installation flow
- Slash command handling
- Interactive message actions
- Event subscriptions
"""

import json
import logging
from typing import Any, Optional
from urllib.parse import parse_qs

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.integrations.slack.client import SlackClient, create_client
from app.integrations.slack.config import get_slack_settings, SlackSettings
from app.integrations.slack.handlers import (
    create_event_handler,
    create_interactive_handler,
    create_slash_handler,
    EventHandler,
    InteractiveHandler,
    SlashCommandHandler,
)
from app.models.slack import (
    InteractionPayload,
    InteractionType,
    SlackEventChallenge,
    SlackEventWrapper,
    SlackOAuthCallback,
    SlashCommandRequest,
    SlashCommandResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack", tags=["slack"])


# === Dependency Injection ===


def get_settings_dependency() -> SlackSettings:
    """Get Slack settings."""
    return get_slack_settings()


def get_client(settings: SlackSettings = Depends(get_settings_dependency)) -> SlackClient:
    """Get Slack client instance."""
    return create_client(settings=settings)


def get_slash_handler(client: SlackClient = Depends(get_client)) -> SlashCommandHandler:
    """Get slash command handler instance."""
    return create_slash_handler(client)


def get_interactive_handler(
    client: SlackClient = Depends(get_client),
) -> InteractiveHandler:
    """Get interactive handler instance."""
    return create_interactive_handler(client)


def get_event_handler(client: SlackClient = Depends(get_client)) -> EventHandler:
    """Get event handler instance."""
    return create_event_handler(client)


# === Request Verification ===


async def verify_slack_request(
    request: Request,
    x_slack_signature: Optional[str] = Header(None),
    x_slack_request_timestamp: Optional[str] = Header(None),
    client: SlackClient = Depends(get_client),
) -> bytes:
    """
    Verify that the request comes from Slack.

    Args:
        request: The incoming request.
        x_slack_signature: Slack signature header.
        x_slack_request_timestamp: Slack timestamp header.
        client: Slack client for verification.

    Returns:
        The raw request body.

    Raises:
        HTTPException: If verification fails.
    """
    if not x_slack_signature or not x_slack_request_timestamp:
        logger.warning("Missing Slack signature headers")
        raise HTTPException(status_code=401, detail="Missing signature headers")

    body = await request.body()

    if not client.verify_signature(x_slack_signature, x_slack_request_timestamp, body):
        logger.warning("Invalid Slack signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    return body


# === OAuth Routes ===


@router.get("/oauth/install")
async def oauth_install(
    settings: SlackSettings = Depends(get_settings_dependency),
    state: Optional[str] = None,
) -> RedirectResponse:
    """
    Redirect to Slack OAuth installation page.

    This initiates the OAuth2 flow for installing the app to a workspace.
    """
    if not settings.is_configured:
        raise HTTPException(
            status_code=500,
            detail="Slack integration not configured",
        )

    install_url = settings.get_oauth_install_url(state)
    return RedirectResponse(url=install_url)


@router.get("/oauth/callback")
async def oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    client: SlackClient = Depends(get_client),
) -> JSONResponse:
    """
    Handle OAuth callback from Slack.

    Exchanges the authorization code for access tokens and stores
    the workspace connection.
    """
    if error:
        logger.error(f"OAuth error from Slack: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    try:
        # Exchange code for tokens
        token_response = await client.exchange_oauth_code(code)

        # Create workspace connection
        workspace = client.create_workspace_connection(token_response)

        # TODO: Store workspace connection in database
        # For now, log the successful connection
        logger.info(
            f"Successfully connected Slack workspace: {workspace.team_name} "
            f"({workspace.team_id})"
        )

        return JSONResponse(
            content={
                "ok": True,
                "team_id": workspace.team_id,
                "team_name": workspace.team_name,
                "message": f"Successfully connected to {workspace.team_name}!",
            }
        )

    except Exception as e:
        logger.exception("OAuth callback failed")
        raise HTTPException(status_code=500, detail=str(e))


# === Slash Command Route ===


@router.post("/commands")
async def handle_slash_command(
    request: Request,
    background_tasks: BackgroundTasks,
    body: bytes = Depends(verify_slack_request),
    handler: SlashCommandHandler = Depends(get_slash_handler),
) -> JSONResponse:
    """
    Handle incoming slash commands from Slack.

    Slack requires a response within 3 seconds, so we acknowledge
    immediately and process in the background if needed.
    """
    # Parse form-encoded body
    form_data = parse_qs(body.decode("utf-8"))

    # Convert to dict with single values
    data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}

    try:
        command_request = SlashCommandRequest(**data)
    except Exception as e:
        logger.error(f"Failed to parse slash command: {e}")
        return JSONResponse(
            content={"response_type": "ephemeral", "text": "Invalid command format"},
            status_code=200,
        )

    # Handle the command
    response = await handler.handle(command_request)

    return JSONResponse(content=response.model_dump(exclude_none=True))


# === Interactive Components Route ===


@router.post("/interactive")
async def handle_interactive(
    request: Request,
    background_tasks: BackgroundTasks,
    body: bytes = Depends(verify_slack_request),
    handler: InteractiveHandler = Depends(get_interactive_handler),
) -> JSONResponse:
    """
    Handle interactive component actions from Slack.

    Processes button clicks, menu selections, and modal submissions.
    """
    # Parse form-encoded body with 'payload' field containing JSON
    form_data = parse_qs(body.decode("utf-8"))
    payload_str = form_data.get("payload", ["{}"])[0]

    try:
        payload_data = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("Failed to parse interactive payload")
        return JSONResponse(
            content={"text": "Invalid payload"},
            status_code=200,
        )

    try:
        # Convert type string to enum
        payload_data["type"] = InteractionType(payload_data.get("type", "block_actions"))
        payload = InteractionPayload(**payload_data)
    except Exception as e:
        logger.error(f"Failed to parse interaction payload: {e}")
        return JSONResponse(content={}, status_code=200)

    # Handle the interaction
    result = await handler.handle(payload)

    # Return appropriate response
    if result:
        return JSONResponse(content=result)
    return JSONResponse(content={})


# === Events Route ===


@router.post("/events")
async def handle_events(
    request: Request,
    background_tasks: BackgroundTasks,
    body: bytes = Depends(verify_slack_request),
    handler: EventHandler = Depends(get_event_handler),
) -> JSONResponse:
    """
    Handle Slack Events API callbacks.

    Handles URL verification challenges and event callbacks.
    """
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Failed to parse event payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = data.get("type")

    # Handle URL verification challenge
    if event_type == "url_verification":
        challenge = SlackEventChallenge(**data)
        return JSONResponse(content={"challenge": challenge.challenge})

    # Handle event callbacks
    if event_type == "event_callback":
        try:
            wrapper = SlackEventWrapper(**data)
        except Exception as e:
            logger.error(f"Failed to parse event wrapper: {e}")
            return JSONResponse(content={"ok": True})

        # Process event in background to respond quickly
        event = wrapper.event
        event_inner_type = event.get("type", "")

        background_tasks.add_task(handler.handle, event_inner_type, event)

        return JSONResponse(content={"ok": True})

    logger.warning(f"Unknown event type: {event_type}")
    return JSONResponse(content={"ok": True})


# === Notification Endpoints ===


@router.post("/notify/channel")
async def send_channel_notification(
    channel_id: str,
    message: str,
    blocks: Optional[list[dict]] = None,
    thread_ts: Optional[str] = None,
    client: SlackClient = Depends(get_client),
) -> JSONResponse:
    """
    Send a notification to a Slack channel.

    This is an internal API for other services to send notifications.
    """
    result = await client.send_message(
        channel=channel_id,
        text=message,
        blocks=blocks,
        thread_ts=thread_ts,
    )

    return JSONResponse(
        content={
            "ok": result.ok,
            "channel": result.channel,
            "ts": result.ts,
            "error": result.error,
        }
    )


@router.post("/notify/dm")
async def send_dm_notification(
    user_id: str,
    message: str,
    blocks: Optional[list[dict]] = None,
    client: SlackClient = Depends(get_client),
) -> JSONResponse:
    """
    Send a direct message notification to a user.

    This is an internal API for other services to send DM notifications.
    """
    result = await client.send_dm(
        user_id=user_id,
        text=message,
        blocks=blocks,
    )

    return JSONResponse(
        content={
            "ok": result.ok,
            "channel": result.channel,
            "ts": result.ts,
            "error": result.error,
        }
    )


# === Configuration Endpoints ===


@router.get("/config/channels")
async def list_channels(
    client: SlackClient = Depends(get_client),
) -> JSONResponse:
    """
    List available Slack channels for notification configuration.
    """
    channels = await client.list_channels()

    return JSONResponse(
        content={
            "ok": True,
            "channels": [
                {"id": c["id"], "name": c["name"]}
                for c in channels
            ],
        }
    )


@router.get("/health")
async def health_check(
    settings: SlackSettings = Depends(get_settings_dependency),
) -> JSONResponse:
    """
    Check Slack integration health status.
    """
    return JSONResponse(
        content={
            "status": "ok" if settings.is_configured else "not_configured",
            "configured": settings.is_configured,
            "features": {
                "slash_commands": settings.enable_slash_commands,
                "interactive_messages": settings.enable_interactive_messages,
                "dm_notifications": settings.enable_dm_notifications,
            },
        }
    )
