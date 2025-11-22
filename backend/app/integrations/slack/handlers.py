"""
Slack event and interaction handlers for Sales OS.

This module contains handlers for:
- Slash commands (/salesos prep, /salesos coach)
- Interactive message actions (approve follow-up, view summary)
- App mentions and events
"""

import logging
from typing import Any, Optional

from app.integrations.slack.client import SlackClient, create_client
from app.integrations.slack.messages import (
    build_coach_response,
    build_error_response,
    build_help_response,
    build_prep_response,
    build_summary_modal,
)
from app.models.slack import (
    CoachCommandRequest,
    CoachCommandResponse,
    InteractionAction,
    InteractionPayload,
    PrepCommandRequest,
    PrepCommandResponse,
    SlashCommandRequest,
    SlashCommandResponse,
)

logger = logging.getLogger(__name__)


class SlashCommandHandler:
    """
    Handler for /salesos slash commands.

    Supported commands:
    - /salesos help - Show help information
    - /salesos prep [company/contact] - Get meeting prep info
    - /salesos coach [call_id] - Get coaching feedback
    """

    def __init__(self, client: Optional[SlackClient] = None):
        """
        Initialize the handler.

        Args:
            client: Slack client instance. Creates default if None.
        """
        self.client = client or create_client()

    async def handle(self, request: SlashCommandRequest) -> SlashCommandResponse:
        """
        Route and handle a slash command.

        Args:
            request: The incoming slash command request.

        Returns:
            SlashCommandResponse to send back to Slack.
        """
        # Parse the command text
        text = request.text.strip()
        parts = text.split(maxsplit=1)
        subcommand = parts[0].lower() if parts else "help"
        args = parts[1] if len(parts) > 1 else ""

        logger.info(
            f"Handling slash command: /salesos {subcommand} "
            f"from user {request.user_id} in channel {request.channel_id}"
        )

        # Route to appropriate handler
        handlers = {
            "help": self._handle_help,
            "prep": self._handle_prep,
            "coach": self._handle_coach,
        }

        handler = handlers.get(subcommand, self._handle_unknown)
        return await handler(request, args)

    async def _handle_help(
        self, request: SlashCommandRequest, args: str
    ) -> SlashCommandResponse:
        """Handle /salesos help command."""
        blocks = build_help_response()
        return SlashCommandResponse(
            response_type="ephemeral",
            blocks=blocks,
        )

    async def _handle_prep(
        self, request: SlashCommandRequest, args: str
    ) -> SlashCommandResponse:
        """
        Handle /salesos prep command.

        Provides meeting preparation information for a company or contact.
        """
        if not args:
            return SlashCommandResponse(
                response_type="ephemeral",
                text="Please specify a company or contact name. Example: `/salesos prep Acme Corp`",
            )

        prep_request = PrepCommandRequest(company_name=args)

        # TODO: Integrate with actual prospect enrichment service (AGENT-007)
        # For now, return a placeholder response
        prep_response = PrepCommandResponse(
            company_info={"name": args, "status": "Lookup pending"},
            suggested_topics=[
                "Review recent product updates",
                "Discuss Q4 goals",
                "Address any open support tickets",
            ],
            warnings=["No recent interactions found - consider warm-up outreach"],
        )

        blocks = build_prep_response(prep_response)
        return SlashCommandResponse(
            response_type="ephemeral",
            blocks=blocks,
        )

    async def _handle_coach(
        self, request: SlashCommandRequest, args: str
    ) -> SlashCommandResponse:
        """
        Handle /salesos coach command.

        Provides coaching feedback for a specific call or general tips.
        """
        coach_request = CoachCommandRequest(
            call_id=args if args else None,
            topic=None,
        )

        # TODO: Integrate with actual coaching service (AGENT-010)
        # For now, return a placeholder response
        if coach_request.call_id:
            coach_response = CoachCommandResponse(
                call_id=coach_request.call_id,
                spiced_scores={
                    "Situation": 7,
                    "Pain": 6,
                    "Impact": 8,
                    "Critical Event": 5,
                    "Decision": 7,
                },
                strengths=["Strong discovery questions", "Good rapport building"],
                improvements=[
                    "Dig deeper on pain points",
                    "Establish clearer next steps",
                ],
                tips=[
                    "Try the 'Tell me more about that' technique",
                    "Summarize pain before moving to solution",
                ],
            )
        else:
            coach_response = CoachCommandResponse(
                strengths=[],
                improvements=[],
                tips=[
                    "Use SPICED methodology for structured discovery",
                    "Always confirm the critical event timeline",
                    "Practice active listening - pause before responding",
                ],
                resources=[
                    {"title": "SPICED Framework Guide", "url": "/resources/spiced"},
                    {"title": "Objection Handling 101", "url": "/resources/objections"},
                ],
            )

        blocks = build_coach_response(coach_response)
        return SlashCommandResponse(
            response_type="ephemeral",
            blocks=blocks,
        )

    async def _handle_unknown(
        self, request: SlashCommandRequest, args: str
    ) -> SlashCommandResponse:
        """Handle unknown subcommands."""
        return SlashCommandResponse(
            response_type="ephemeral",
            text=f"Unknown command. Try `/salesos help` to see available commands.",
        )


class InteractiveHandler:
    """
    Handler for interactive Slack components.

    Handles button clicks, menu selections, and modal submissions.
    """

    def __init__(self, client: Optional[SlackClient] = None):
        """
        Initialize the handler.

        Args:
            client: Slack client instance. Creates default if None.
        """
        self.client = client or create_client()

    async def handle(self, payload: InteractionPayload) -> Optional[dict]:
        """
        Handle an interactive component action.

        Args:
            payload: The interaction payload from Slack.

        Returns:
            Response dict to send back, or None for no immediate response.
        """
        logger.info(
            f"Handling interaction: {payload.type} "
            f"from user {payload.user.id}"
        )

        if payload.type.value == "block_actions":
            return await self._handle_block_actions(payload)
        elif payload.type.value == "view_submission":
            return await self._handle_view_submission(payload)
        else:
            logger.warning(f"Unhandled interaction type: {payload.type}")
            return None

    async def _handle_block_actions(
        self, payload: InteractionPayload
    ) -> Optional[dict]:
        """Handle block action interactions (buttons, menus, etc.)."""
        for action in payload.actions:
            result = await self._route_action(action, payload)
            if result:
                return result
        return None

    async def _route_action(
        self, action: InteractionAction, payload: InteractionPayload
    ) -> Optional[dict]:
        """Route an action to its handler."""
        action_handlers = {
            "approve_followup": self._handle_approve_followup,
            "view_summary": self._handle_view_summary,
            "dismiss_notification": self._handle_dismiss,
            "share_to_channel": self._handle_share,
        }

        # Extract action type from action_id (format: type_identifier)
        action_type = action.action_id.split("_")[0]
        if action.action_id in action_handlers:
            return await action_handlers[action.action_id](action, payload)

        # Try prefix matching for dynamic action IDs
        for prefix, handler in action_handlers.items():
            if action.action_id.startswith(prefix):
                return await handler(action, payload)

        logger.warning(f"Unhandled action: {action.action_id}")
        return None

    async def _handle_approve_followup(
        self, action: InteractionAction, payload: InteractionPayload
    ) -> dict:
        """
        Handle follow-up approval action.

        When a user approves a suggested follow-up (email, task, etc.),
        trigger the appropriate workflow.
        """
        # Extract call_id from action value
        call_id = action.value

        logger.info(
            f"User {payload.user.id} approved follow-up for call {call_id}"
        )

        # TODO: Integrate with follow-up service to actually create the follow-up
        # For now, acknowledge the action

        # Send response via response_url to update the message
        await self.client.respond_to_url(
            payload.response_url,
            text=f"Follow-up approved for call {call_id}. Creating task...",
            replace_original=True,
        )

        return {"ok": True}

    async def _handle_view_summary(
        self, action: InteractionAction, payload: InteractionPayload
    ) -> dict:
        """
        Handle view summary action.

        Opens a modal with the full call summary.
        """
        call_id = action.value

        logger.info(f"User {payload.user.id} viewing summary for call {call_id}")

        # TODO: Fetch actual call summary from transcript service (AGENT-005)
        # For now, use placeholder data
        summary_data = {
            "call_id": call_id,
            "title": "Call with Acme Corp",
            "date": "2024-01-15",
            "duration": "45 minutes",
            "spiced": {
                "situation": "Enterprise company looking to modernize sales stack",
                "pain": "Current CRM is slow and lacks AI capabilities",
                "impact": "Sales team spending 30% time on admin vs selling",
                "critical_event": "Contract renewal in Q2",
                "decision": "Evaluation committee meets monthly",
            },
            "next_steps": [
                "Send ROI calculator",
                "Schedule demo with full team",
                "Connect with IT for security review",
            ],
        }

        modal = build_summary_modal(summary_data)

        # Open modal using trigger_id
        # Note: This would require the views.open API call
        # For simplicity, we'll respond with formatted text
        await self.client.respond_to_url(
            payload.response_url,
            blocks=modal["blocks"],
            response_type="ephemeral",
        )

        return {"ok": True}

    async def _handle_dismiss(
        self, action: InteractionAction, payload: InteractionPayload
    ) -> dict:
        """Handle dismiss/close action."""
        await self.client.respond_to_url(
            payload.response_url,
            delete_original=True,
        )
        return {"ok": True}

    async def _handle_share(
        self, action: InteractionAction, payload: InteractionPayload
    ) -> dict:
        """Handle share to channel action."""
        # Re-post the message content to the channel publicly
        if payload.message:
            await self.client.send_message(
                channel=payload.channel.id if payload.channel else "",
                text=payload.message.get("text", "Shared from Sales OS"),
                blocks=payload.message.get("blocks"),
            )
            await self.client.respond_to_url(
                payload.response_url,
                text="Shared to channel!",
                replace_original=False,
            )
        return {"ok": True}

    async def _handle_view_submission(
        self, payload: InteractionPayload
    ) -> Optional[dict]:
        """Handle modal view submissions."""
        if not payload.view:
            return None

        callback_id = payload.view.get("callback_id", "")
        logger.info(f"Handling view submission: {callback_id}")

        # Route based on callback_id
        if callback_id == "prep_form":
            return await self._handle_prep_form_submission(payload)
        elif callback_id == "feedback_form":
            return await self._handle_feedback_form_submission(payload)

        return None

    async def _handle_prep_form_submission(
        self, payload: InteractionPayload
    ) -> dict:
        """Handle prep form modal submission."""
        # Extract form values from view state
        # TODO: Implement form processing
        return {"response_action": "clear"}

    async def _handle_feedback_form_submission(
        self, payload: InteractionPayload
    ) -> dict:
        """Handle feedback form modal submission."""
        # TODO: Implement feedback processing
        return {"response_action": "clear"}


class EventHandler:
    """
    Handler for Slack Events API callbacks.

    Handles app mentions, messages, and other event types.
    """

    def __init__(self, client: Optional[SlackClient] = None):
        """
        Initialize the handler.

        Args:
            client: Slack client instance. Creates default if None.
        """
        self.client = client or create_client()

    async def handle(self, event_type: str, event: dict) -> None:
        """
        Route and handle a Slack event.

        Args:
            event_type: Type of the event.
            event: The event payload.
        """
        logger.info(f"Handling event: {event_type}")

        handlers = {
            "app_mention": self._handle_app_mention,
            "message": self._handle_message,
            "app_home_opened": self._handle_app_home_opened,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(event)
        else:
            logger.debug(f"No handler for event type: {event_type}")

    async def _handle_app_mention(self, event: dict) -> None:
        """
        Handle when the app is mentioned in a channel.

        Responds with helpful information or triggers actions based on context.
        """
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "").lower()
        thread_ts = event.get("thread_ts") or event.get("ts")

        logger.info(f"App mentioned by {user} in {channel}: {text}")

        # Simple keyword-based routing
        if "help" in text:
            blocks = build_help_response()
            await self.client.send_message(
                channel=channel,
                blocks=blocks,
                thread_ts=thread_ts,
            )
        elif "prep" in text:
            await self.client.send_message(
                channel=channel,
                text="Use `/salesos prep [company name]` to get meeting preparation info.",
                thread_ts=thread_ts,
            )
        elif "coach" in text:
            await self.client.send_message(
                channel=channel,
                text="Use `/salesos coach [call_id]` to get coaching feedback, or `/salesos coach` for general tips.",
                thread_ts=thread_ts,
            )
        else:
            # Default response
            await self.client.send_message(
                channel=channel,
                text="Hi! I'm Sales OS. Try `/salesos help` to see what I can do.",
                thread_ts=thread_ts,
            )

    async def _handle_message(self, event: dict) -> None:
        """
        Handle direct messages to the bot.

        Only processes DMs (im channel type), not channel messages.
        """
        # Ignore bot messages to prevent loops
        if event.get("bot_id"):
            return

        channel_type = event.get("channel_type")
        if channel_type != "im":
            return

        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "")

        logger.info(f"DM from {user}: {text}")

        # Respond to DMs with help info
        await self.client.send_message(
            channel=channel,
            text=(
                "Hi! I'm Sales OS. Here's what I can do:\n\n"
                "- `/salesos prep [company]` - Get meeting prep\n"
                "- `/salesos coach [call_id]` - Get coaching feedback\n"
                "- `/salesos help` - See all commands"
            ),
        )

    async def _handle_app_home_opened(self, event: dict) -> None:
        """
        Handle when a user opens the App Home tab.

        Publishes a home view with useful information and quick actions.
        """
        user = event.get("user")

        logger.info(f"App Home opened by {user}")

        # TODO: Publish home view with user-specific content
        # This requires the views.publish API call
        pass


# === Factory Functions ===


def create_slash_handler(client: Optional[SlackClient] = None) -> SlashCommandHandler:
    """Create a slash command handler instance."""
    return SlashCommandHandler(client)


def create_interactive_handler(
    client: Optional[SlackClient] = None,
) -> InteractiveHandler:
    """Create an interactive handler instance."""
    return InteractiveHandler(client)


def create_event_handler(client: Optional[SlackClient] = None) -> EventHandler:
    """Create an event handler instance."""
    return EventHandler(client)
