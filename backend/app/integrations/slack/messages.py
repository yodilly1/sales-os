"""
Slack message builders for Sales OS.

This module provides Block Kit message builders for:
- Notification messages (call processed, content ready, etc.)
- Slash command responses
- Interactive message components
- Modal views
"""

from typing import Any, Optional

from app.models.slack import (
    CoachCommandResponse,
    PrepCommandResponse,
    SlackNotification,
    SlackNotificationType,
)


# === Block Building Helpers ===


def section(text: str, accessory: Optional[dict] = None) -> dict:
    """Create a section block."""
    block: dict[str, Any] = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text},
    }
    if accessory:
        block["accessory"] = accessory
    return block


def divider() -> dict:
    """Create a divider block."""
    return {"type": "divider"}


def header(text: str) -> dict:
    """Create a header block."""
    return {
        "type": "header",
        "text": {"type": "plain_text", "text": text, "emoji": True},
    }


def context(elements: list[str]) -> dict:
    """Create a context block with markdown elements."""
    return {
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": el} for el in elements],
    }


def actions(elements: list[dict], block_id: Optional[str] = None) -> dict:
    """Create an actions block."""
    block: dict[str, Any] = {"type": "actions", "elements": elements}
    if block_id:
        block["block_id"] = block_id
    return block


def button(
    text: str,
    action_id: str,
    value: Optional[str] = None,
    style: Optional[str] = None,
    url: Optional[str] = None,
) -> dict:
    """
    Create a button element.

    Args:
        text: Button label.
        action_id: Unique action identifier.
        value: Value to send with the action.
        style: 'primary' or 'danger' for colored buttons.
        url: URL to open (makes it a link button).
    """
    btn: dict[str, Any] = {
        "type": "button",
        "text": {"type": "plain_text", "text": text, "emoji": True},
        "action_id": action_id,
    }
    if value:
        btn["value"] = value
    if style:
        btn["style"] = style
    if url:
        btn["url"] = url
    return btn


def fields(items: list[tuple[str, str]]) -> dict:
    """Create a section with multiple fields."""
    return {
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": f"*{label}*\n{value}"}
            for label, value in items
        ],
    }


# === Notification Message Builders ===


def build_call_processed_notification(
    call_id: str,
    title: str,
    summary: str,
    spiced_scores: Optional[dict] = None,
    next_steps: Optional[list[str]] = None,
) -> list[dict]:
    """
    Build notification blocks for a processed call.

    Args:
        call_id: The call identifier.
        title: Call title (e.g., "Call with Acme Corp").
        summary: Brief call summary.
        spiced_scores: SPICED methodology scores.
        next_steps: List of identified next steps.

    Returns:
        List of Block Kit blocks.
    """
    blocks = [
        header("Call Processed"),
        section(f"*{title}*\n{summary}"),
    ]

    # Add SPICED scores if available
    if spiced_scores:
        score_text = " | ".join(
            f"*{k}:* {v}/10" for k, v in spiced_scores.items()
        )
        blocks.append(context([f"SPICED Scores: {score_text}"]))

    # Add next steps
    if next_steps:
        steps_text = "\n".join(f"• {step}" for step in next_steps[:5])
        blocks.append(section(f"*Next Steps*\n{steps_text}"))

    blocks.append(divider())

    # Add action buttons
    blocks.append(
        actions([
            button(
                "View Summary",
                f"view_summary_{call_id}",
                value=call_id,
                style="primary",
            ),
            button(
                "Approve Follow-up",
                f"approve_followup_{call_id}",
                value=call_id,
            ),
            button(
                "Dismiss",
                f"dismiss_notification_{call_id}",
                value=call_id,
            ),
        ])
    )

    return blocks


def build_content_ready_notification(
    content_id: str,
    content_type: str,
    title: str,
    preview_url: Optional[str] = None,
) -> list[dict]:
    """
    Build notification blocks for ready content.

    Args:
        content_id: The content identifier.
        content_type: Type of content (deck, proposal, one-pager).
        title: Content title.
        preview_url: URL to preview the content.

    Returns:
        List of Block Kit blocks.
    """
    type_emoji = {
        "deck": "presentation",
        "proposal": "page_facing_up",
        "one-pager": "memo",
    }.get(content_type.lower(), "page_facing_up")

    blocks = [
        header("Content Ready"),
        section(
            f":{type_emoji}: *{content_type.title()}*: {title}\n\n"
            f"Your content has been generated and is ready for review."
        ),
        divider(),
    ]

    action_buttons = [
        button(
            "View Content",
            f"view_content_{content_id}",
            value=content_id,
            style="primary",
        ),
        button(
            "Share to Channel",
            f"share_to_channel_{content_id}",
            value=content_id,
        ),
    ]

    if preview_url:
        action_buttons.insert(
            1,
            button(
                "Preview",
                f"preview_content_{content_id}",
                value=content_id,
                url=preview_url,
            ),
        )

    blocks.append(actions(action_buttons))

    return blocks


def build_coaching_feedback_notification(
    call_id: str,
    overall_score: int,
    top_strength: str,
    top_improvement: str,
) -> list[dict]:
    """
    Build notification blocks for coaching feedback.

    Args:
        call_id: The call identifier.
        overall_score: Overall performance score (1-10).
        top_strength: Primary area of strength.
        top_improvement: Primary area for improvement.

    Returns:
        List of Block Kit blocks.
    """
    # Score indicator
    score_indicator = "+" * overall_score + "-" * (10 - overall_score)

    blocks = [
        header("Coaching Feedback Available"),
        section(
            f"*Performance Score:* {overall_score}/10\n"
            f"`[{score_indicator}]`"
        ),
        fields([
            ("Top Strength", top_strength),
            ("Focus Area", top_improvement),
        ]),
        divider(),
        actions([
            button(
                "View Full Feedback",
                f"view_coaching_{call_id}",
                value=call_id,
                style="primary",
            ),
            button(
                "Dismiss",
                f"dismiss_notification_{call_id}",
                value=call_id,
            ),
        ]),
    ]

    return blocks


def build_prospect_enriched_notification(
    prospect_name: str,
    company_name: str,
    key_insights: list[str],
) -> list[dict]:
    """
    Build notification blocks for enriched prospect data.

    Args:
        prospect_name: Name of the prospect.
        company_name: Company name.
        key_insights: List of key insights from enrichment.

    Returns:
        List of Block Kit blocks.
    """
    insights_text = "\n".join(f"• {insight}" for insight in key_insights[:5])

    blocks = [
        header("Prospect Enriched"),
        section(f"*{prospect_name}* at *{company_name}*"),
        section(f"*Key Insights*\n{insights_text}"),
        divider(),
        actions([
            button(
                "View Full Profile",
                "view_prospect",
                style="primary",
            ),
            button(
                "Add to Sequence",
                "add_to_sequence",
            ),
        ]),
    ]

    return blocks


# === Slash Command Response Builders ===


def build_help_response() -> list[dict]:
    """Build help message blocks."""
    return [
        header("Sales OS Help"),
        section(
            "Here are the available commands:\n\n"
            "*`/salesos help`*\n"
            "Show this help message\n\n"
            "*`/salesos prep [company or contact]`*\n"
            "Get meeting preparation info including company research, "
            "recent interactions, and suggested topics\n\n"
            "*`/salesos coach [call_id]`*\n"
            "Get coaching feedback for a specific call, or general coaching tips"
        ),
        divider(),
        context([
            "Need more help? Visit our documentation or contact support."
        ]),
    ]


def build_prep_response(prep: PrepCommandResponse) -> list[dict]:
    """
    Build prep command response blocks.

    Args:
        prep: PrepCommandResponse with preparation data.

    Returns:
        List of Block Kit blocks.
    """
    blocks = [header("Meeting Prep")]

    # Company info
    if prep.company_info:
        company_name = prep.company_info.get("name", "Unknown")
        blocks.append(section(f"*Company:* {company_name}"))

    # Contact info
    if prep.contact_info:
        contact_name = prep.contact_info.get("name", "Unknown")
        contact_title = prep.contact_info.get("title", "")
        blocks.append(
            section(f"*Contact:* {contact_name}" + (f" ({contact_title})" if contact_title else ""))
        )

    blocks.append(divider())

    # Suggested topics
    if prep.suggested_topics:
        topics_text = "\n".join(f"• {topic}" for topic in prep.suggested_topics)
        blocks.append(section(f"*Suggested Discussion Topics*\n{topics_text}"))

    # Recent interactions
    if prep.recent_interactions:
        interactions_text = "\n".join(
            f"• {i.get('date', 'N/A')}: {i.get('summary', 'No summary')}"
            for i in prep.recent_interactions[:3]
        )
        blocks.append(section(f"*Recent Interactions*\n{interactions_text}"))

    # Warnings
    if prep.warnings:
        warnings_text = "\n".join(f"⚠️ {w}" for w in prep.warnings)
        blocks.append(section(f"*Alerts*\n{warnings_text}"))

    return blocks


def build_coach_response(coach: CoachCommandResponse) -> list[dict]:
    """
    Build coach command response blocks.

    Args:
        coach: CoachCommandResponse with coaching data.

    Returns:
        List of Block Kit blocks.
    """
    blocks = [header("Coaching Feedback")]

    # Call-specific feedback
    if coach.call_id:
        blocks.append(context([f"Call ID: `{coach.call_id}`"]))

        # SPICED scores
        if coach.spiced_scores:
            score_items = [
                (k, f"{v}/10") for k, v in coach.spiced_scores.items()
            ]
            blocks.append(fields(score_items[:6]))  # Max 2 rows of 3

        blocks.append(divider())

    # Strengths
    if coach.strengths:
        strengths_text = "\n".join(f"✓ {s}" for s in coach.strengths)
        blocks.append(section(f"*Strengths*\n{strengths_text}"))

    # Areas for improvement
    if coach.improvements:
        improvements_text = "\n".join(f"→ {i}" for i in coach.improvements)
        blocks.append(section(f"*Areas for Improvement*\n{improvements_text}"))

    # Tips
    if coach.tips:
        tips_text = "\n".join(f"💡 {t}" for t in coach.tips)
        blocks.append(section(f"*Coaching Tips*\n{tips_text}"))

    # Resources
    if coach.resources:
        resources_text = "\n".join(
            f"• <{r.get('url', '#')}|{r.get('title', 'Resource')}>"
            for r in coach.resources
        )
        blocks.append(section(f"*Resources*\n{resources_text}"))

    return blocks


def build_error_response(error_message: str) -> list[dict]:
    """Build error message blocks."""
    return [
        section(f"❌ *Error*\n{error_message}"),
        context(["If this issue persists, please contact support."]),
    ]


# === Modal View Builders ===


def build_summary_modal(summary_data: dict) -> dict:
    """
    Build a modal view for displaying call summary.

    Args:
        summary_data: Dictionary containing call summary information.

    Returns:
        Modal view definition.
    """
    blocks = [
        header(summary_data.get("title", "Call Summary")),
        context([
            f"Date: {summary_data.get('date', 'N/A')} | "
            f"Duration: {summary_data.get('duration', 'N/A')}"
        ]),
        divider(),
    ]

    # SPICED Analysis
    spiced = summary_data.get("spiced", {})
    if spiced:
        blocks.append(section("*SPICED Analysis*"))
        for category in ["situation", "pain", "impact", "critical_event", "decision"]:
            if category in spiced:
                label = category.replace("_", " ").title()
                blocks.append(
                    section(f"*{label}*\n{spiced[category]}")
                )
        blocks.append(divider())

    # Next steps
    next_steps = summary_data.get("next_steps", [])
    if next_steps:
        steps_text = "\n".join(f"• {step}" for step in next_steps)
        blocks.append(section(f"*Next Steps*\n{steps_text}"))

    return {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Call Summary"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": blocks,
    }


def build_prep_modal() -> dict:
    """Build a modal for entering prep request details."""
    return {
        "type": "modal",
        "callback_id": "prep_form",
        "title": {"type": "plain_text", "text": "Meeting Prep"},
        "submit": {"type": "plain_text", "text": "Get Prep"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "company_input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "company_name",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter company name",
                    },
                },
                "label": {"type": "plain_text", "text": "Company Name"},
            },
            {
                "type": "input",
                "block_id": "contact_input",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "contact_name",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter contact name",
                    },
                },
                "label": {"type": "plain_text", "text": "Contact Name"},
            },
        ],
    }


# === Notification Factory ===


def build_notification_blocks(notification: SlackNotification) -> list[dict]:
    """
    Build blocks for a notification based on its type.

    Args:
        notification: The notification to build blocks for.

    Returns:
        List of Block Kit blocks.
    """
    notification_type = notification.notification_type
    metadata = notification.metadata

    if notification_type == SlackNotificationType.CALL_PROCESSED:
        return build_call_processed_notification(
            call_id=metadata.get("call_id", ""),
            title=notification.title,
            summary=notification.message,
            spiced_scores=metadata.get("spiced_scores"),
            next_steps=metadata.get("next_steps"),
        )
    elif notification_type == SlackNotificationType.CONTENT_READY:
        return build_content_ready_notification(
            content_id=metadata.get("content_id", ""),
            content_type=metadata.get("content_type", "document"),
            title=notification.title,
            preview_url=metadata.get("preview_url"),
        )
    elif notification_type == SlackNotificationType.COACHING_FEEDBACK:
        return build_coaching_feedback_notification(
            call_id=metadata.get("call_id", ""),
            overall_score=metadata.get("overall_score", 5),
            top_strength=metadata.get("top_strength", ""),
            top_improvement=metadata.get("top_improvement", ""),
        )
    elif notification_type == SlackNotificationType.PROSPECT_ENRICHED:
        return build_prospect_enriched_notification(
            prospect_name=metadata.get("prospect_name", ""),
            company_name=metadata.get("company_name", ""),
            key_insights=metadata.get("key_insights", []),
        )
    else:
        # Default simple notification
        return [
            header(notification.title),
            section(notification.message),
        ]
