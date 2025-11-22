"""
Email API Endpoints for Sales OS

Provides REST API endpoints for email operations including sending,
tracking, webhooks, and management.
"""

import logging
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    BackgroundTasks,
    Depends,
    Query,
    Path,
    Header,
)
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from ..models.email import (
    EmailMessageCreate,
    EmailMessage,
    EmailTemplate,
    EmailTemplateCreate,
    EmailTemplateType,
    EmailProvider,
    EmailStatus,
    EmailEvent,
    EmailEventType,
    SendEmailResponse,
    EmailStatsResponse,
    Unsubscribe,
    UnsubscribeCreate,
    UnsubscribeReason,
    BounceRecord,
    BounceType,
    WebhookPayload,
    EmailRecipient,
)
from ..integrations.email import (
    EmailService,
    TemplateRenderer,
    TrackingService,
    BounceHandler,
    UnsubscribeManager,
)
from ..integrations.email.template_renderer import DefaultTemplates


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])


# Request/Response Models
class SendEmailRequest(BaseModel):
    """Request model for sending an email."""
    to: List[EmailStr]
    to_names: Optional[List[str]] = None
    subject: str = Field(..., min_length=1, max_length=998)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    template_id: Optional[UUID] = None
    template_variables: Optional[dict] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    track_opens: bool = True
    track_clicks: bool = True
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    send_at: Optional[datetime] = None
    campaign_id: Optional[UUID] = None


class BatchSendRequest(BaseModel):
    """Request model for sending batch emails."""
    emails: List[SendEmailRequest]
    template_id: Optional[UUID] = None


class UnsubscribeRequest(BaseModel):
    """Request model for unsubscribing."""
    email: EmailStr
    reason: Optional[str] = "user_request"
    list_id: Optional[str] = None
    feedback: Optional[str] = None


class ResubscribeRequest(BaseModel):
    """Request model for resubscribing."""
    email: EmailStr
    list_id: Optional[str] = None


# Dependency for email service
# In production, this would be properly configured via dependency injection
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the email service instance."""
    global _email_service
    if _email_service is None:
        # Default configuration - override in production
        config = {
            "provider": "sendgrid",
            "sendgrid": {
                "api_key": "your-api-key-here",
            }
        }
        _email_service = EmailService(
            provider_config=config,
            tracking_base_url="https://api.example.com",
            default_from_email="noreply@example.com",
            default_from_name="Sales OS",
        )
    return _email_service


# Email Sending Endpoints
@router.post("/send", response_model=SendEmailResponse)
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    email_service: EmailService = Depends(get_email_service),
):
    """
    Send an email.

    Supports:
    - Direct content or template-based emails
    - Multiple recipients
    - Open and click tracking
    - Scheduled sending
    """
    # Build recipients list
    recipients = []
    for i, email in enumerate(request.to):
        name = request.to_names[i] if request.to_names and i < len(request.to_names) else None
        recipients.append(EmailRecipient(email=email, name=name))

    cc_recipients = None
    if request.cc:
        cc_recipients = [EmailRecipient(email=e) for e in request.cc]

    bcc_recipients = None
    if request.bcc:
        bcc_recipients = [EmailRecipient(email=e) for e in request.bcc]

    # Create email message
    message = EmailMessageCreate(
        subject=request.subject,
        from_email=request.from_email,
        from_name=request.from_name,
        reply_to=request.reply_to,
        html_content=request.html_content,
        text_content=request.text_content,
        to_recipients=recipients,
        cc_recipients=cc_recipients,
        bcc_recipients=bcc_recipients,
        template_id=request.template_id,
        template_variables=request.template_variables,
        track_opens=request.track_opens,
        track_clicks=request.track_clicks,
        tags=request.tags,
        metadata=request.metadata,
        send_at=request.send_at,
        campaign_id=request.campaign_id,
    )

    # Get template if specified
    template = None
    if request.template_id:
        # In production, fetch template from database
        pass

    try:
        response = await email_service.send_email(message, template)
        return response
    except Exception as e:
        logger.exception("Error sending email")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/batch", response_model=List[SendEmailResponse])
async def send_batch_emails(
    request: BatchSendRequest,
    background_tasks: BackgroundTasks,
    email_service: EmailService = Depends(get_email_service),
):
    """Send multiple emails in batch."""
    messages = []
    for email_req in request.emails:
        recipients = [
            EmailRecipient(
                email=email_req.to[i],
                name=email_req.to_names[i] if email_req.to_names and i < len(email_req.to_names) else None
            )
            for i in range(len(email_req.to))
        ]

        messages.append(EmailMessageCreate(
            subject=email_req.subject,
            from_email=email_req.from_email,
            from_name=email_req.from_name,
            reply_to=email_req.reply_to,
            html_content=email_req.html_content,
            text_content=email_req.text_content,
            to_recipients=recipients,
            template_id=email_req.template_id or request.template_id,
            template_variables=email_req.template_variables,
            track_opens=email_req.track_opens,
            track_clicks=email_req.track_clicks,
            tags=email_req.tags,
            metadata=email_req.metadata,
            campaign_id=email_req.campaign_id,
        ))

    try:
        responses = await email_service.send_batch(messages)
        return responses
    except Exception as e:
        logger.exception("Error sending batch emails")
        raise HTTPException(status_code=500, detail=str(e))


# Message Status Endpoints
@router.get("/messages/{message_id}", response_model=EmailMessage)
async def get_message(
    message_id: UUID = Path(..., description="Message ID"),
    email_service: EmailService = Depends(get_email_service),
):
    """Get details of a specific email message."""
    message = await email_service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.get("/messages/{message_id}/events", response_model=List[EmailEvent])
async def get_message_events(
    message_id: UUID = Path(..., description="Message ID"),
    email_service: EmailService = Depends(get_email_service),
):
    """Get tracking events for a message."""
    events = await email_service.get_message_events(message_id)
    return events


# Statistics Endpoints
@router.get("/stats", response_model=EmailStatsResponse)
async def get_email_stats(
    campaign_id: Optional[UUID] = Query(None, description="Filter by campaign"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    email_service: EmailService = Depends(get_email_service),
):
    """Get aggregated email statistics."""
    stats = await email_service.get_message_stats(
        campaign_id=campaign_id,
        start_date=start_date,
        end_date=end_date,
    )
    return EmailStatsResponse(**stats)


# Tracking Endpoints
@router.get("/track/open/{tracking_id}")
async def track_open(
    tracking_id: str = Path(..., description="Tracking ID"),
    request: Request = None,
    email_service: EmailService = Depends(get_email_service),
):
    """
    Track email open via tracking pixel.

    Returns a 1x1 transparent GIF.
    """
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    await email_service.record_open(
        tracking_id=tracking_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Return 1x1 transparent GIF
    gif_bytes = (
        b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
        b'\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00'
        b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    )

    return Response(
        content=gif_bytes,
        media_type="image/gif",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/track/click/{tracking_id}/{link_id}")
async def track_click(
    tracking_id: str = Path(..., description="Tracking ID"),
    link_id: str = Path(..., description="Link ID"),
    url: str = Query(..., description="Destination URL"),
    request: Request = None,
    email_service: EmailService = Depends(get_email_service),
):
    """
    Track email click and redirect to destination.
    """
    import urllib.parse

    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    await email_service.record_click(
        tracking_id=tracking_id,
        link_id=link_id,
        url=url,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Decode and redirect to original URL
    decoded_url = urllib.parse.unquote(url)
    return RedirectResponse(url=decoded_url, status_code=302)


# Webhook Endpoints
@router.post("/webhooks/sendgrid")
async def handle_sendgrid_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    email_service: EmailService = Depends(get_email_service),
    x_twilio_email_event_webhook_signature: Optional[str] = Header(None),
    x_twilio_email_event_webhook_timestamp: Optional[str] = Header(None),
):
    """Handle SendGrid webhook events."""
    try:
        body = await request.body()

        # Verify signature in production
        if x_twilio_email_event_webhook_signature:
            is_valid = email_service.provider.verify_webhook_signature(
                body,
                x_twilio_email_event_webhook_signature,
                x_twilio_email_event_webhook_timestamp,
            )
            if not is_valid:
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse events (SendGrid sends an array)
        import json
        events = json.loads(body)

        for event_data in events:
            payload = WebhookPayload(
                provider=EmailProvider.SENDGRID,
                event_type=event_data.get("event", ""),
                timestamp=datetime.utcnow(),
                data=event_data,
            )

            # Process in background
            background_tasks.add_task(
                email_service.handle_webhook,
                EmailProvider.SENDGRID,
                payload,
            )

        return {"status": "ok", "events_received": len(events)}

    except Exception as e:
        logger.exception("Error processing SendGrid webhook")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/ses")
async def handle_ses_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    email_service: EmailService = Depends(get_email_service),
):
    """Handle Amazon SES webhook events via SNS."""
    try:
        body = await request.body()
        import json
        data = json.loads(body)

        # Handle SNS subscription confirmation
        if data.get("Type") == "SubscriptionConfirmation":
            # In production, confirm the subscription
            logger.info(f"SNS subscription confirmation: {data.get('SubscribeURL')}")
            return {"status": "subscription_received"}

        # Verify signature
        is_valid = email_service.provider.verify_webhook_signature(body, "", None)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid signature")

        payload = WebhookPayload(
            provider=EmailProvider.SES,
            event_type=data.get("notificationType", ""),
            timestamp=datetime.utcnow(),
            data=data,
        )

        # Process in background
        background_tasks.add_task(
            email_service.handle_webhook,
            EmailProvider.SES,
            payload,
        )

        return {"status": "ok"}

    except Exception as e:
        logger.exception("Error processing SES webhook")
        raise HTTPException(status_code=500, detail=str(e))


# Unsubscribe Endpoints
@router.get("/unsubscribe/{tracking_id}")
async def unsubscribe_page(
    tracking_id: str = Path(..., description="Tracking ID"),
    token: str = Query(..., description="Verification token"),
    list_id: Optional[str] = Query(None, description="List ID"),
    email_service: EmailService = Depends(get_email_service),
):
    """
    Display unsubscribe confirmation page.

    In production, this would render an HTML page.
    """
    # Verify token
    is_valid = email_service.unsubscribe_manager.verify_token(tracking_id, token)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid unsubscribe link")

    return {
        "message": "Unsubscribe page",
        "tracking_id": tracking_id,
        "list_id": list_id,
        "action": f"/api/email/unsubscribe/{tracking_id}",
    }


@router.post("/unsubscribe/{tracking_id}")
async def process_unsubscribe(
    tracking_id: str = Path(..., description="Tracking ID"),
    request: UnsubscribeRequest = None,
    req: Request = None,
    email_service: EmailService = Depends(get_email_service),
):
    """Process an unsubscribe request."""
    ip_address = req.client.host if req else None
    user_agent = req.headers.get("user-agent") if req else None

    reason = UnsubscribeReason.USER_REQUEST
    if request.reason == "spam":
        reason = UnsubscribeReason.SPAM_COMPLAINT

    unsub_request = UnsubscribeCreate(
        email=request.email,
        reason=reason,
        global_unsubscribe=not request.list_id,
        list_ids=[request.list_id] if request.list_id else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    unsub = await email_service.unsubscribe_manager.process_unsubscribe(unsub_request)

    return {
        "success": True,
        "message": f"Successfully unsubscribed {request.email}",
        "unsubscribe_id": str(unsub.id),
    }


@router.post("/resubscribe")
async def process_resubscribe(
    request: ResubscribeRequest,
    email_service: EmailService = Depends(get_email_service),
):
    """Process a resubscribe request."""
    success = await email_service.unsubscribe_manager.process_resubscribe(
        email=request.email,
        list_id=request.list_id,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot resubscribe this email address"
        )

    return {
        "success": True,
        "message": f"Successfully resubscribed {request.email}",
    }


@router.get("/unsubscribes")
async def list_unsubscribes(
    reason: Optional[str] = Query(None, description="Filter by reason"),
    include_resubscribed: bool = Query(False, description="Include resubscribed"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    email_service: EmailService = Depends(get_email_service),
):
    """Get list of unsubscribed emails."""
    reason_enum = None
    if reason:
        try:
            reason_enum = UnsubscribeReason(reason)
        except ValueError:
            pass

    unsubscribes = await email_service.unsubscribe_manager.get_unsubscribed_emails(
        reason=reason_enum,
        include_resubscribed=include_resubscribed,
        limit=limit,
        offset=offset,
    )

    return {
        "unsubscribes": unsubscribes,
        "count": len(unsubscribes),
    }


# Bounce Endpoints
@router.get("/bounces")
async def list_bounces(
    bounce_type: Optional[str] = Query(None, description="Filter by type (hard/soft/block)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    email_service: EmailService = Depends(get_email_service),
):
    """Get list of bounced emails."""
    type_enum = None
    if bounce_type:
        try:
            type_enum = BounceType(bounce_type)
        except ValueError:
            pass

    bounces = await email_service.bounce_handler.get_bounced_emails(
        bounce_type=type_enum,
        limit=limit,
        offset=offset,
    )

    return {
        "bounces": bounces,
        "count": len(bounces),
    }


@router.get("/bounces/stats")
async def get_bounce_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    email_service: EmailService = Depends(get_email_service),
):
    """Get bounce statistics."""
    stats = await email_service.bounce_handler.get_bounce_stats(
        start_date=start_date,
        end_date=end_date,
    )
    return stats


@router.delete("/bounces/{email}")
async def remove_bounce(
    email: str = Path(..., description="Email to remove from bounce list"),
    email_service: EmailService = Depends(get_email_service),
):
    """Remove an email from the bounce list (manual correction)."""
    success = await email_service.bounce_handler.remove_from_suppression(email)
    if not success:
        raise HTTPException(status_code=404, detail="Email not found in bounce list")

    return {"success": True, "message": f"Removed {email} from bounce list"}


# Template Endpoints
@router.get("/templates")
async def list_templates(
    template_type: Optional[str] = Query(None, description="Filter by type"),
    active_only: bool = Query(True, description="Only active templates"),
):
    """Get list of email templates."""
    # In production, fetch from database
    # For now, return default templates
    templates = [
        DefaultTemplates.follow_up_template(),
        DefaultTemplates.proposal_template(),
        DefaultTemplates.intro_template(),
        DefaultTemplates.content_delivery_template(),
        DefaultTemplates.meeting_recap_template(),
    ]

    if template_type:
        try:
            type_enum = EmailTemplateType(template_type)
            templates = [t for t in templates if t.template_type == type_enum]
        except ValueError:
            pass

    if active_only:
        templates = [t for t in templates if t.is_active]

    return {
        "templates": templates,
        "count": len(templates),
    }


@router.get("/templates/{template_id}")
async def get_template(
    template_id: UUID = Path(..., description="Template ID"),
):
    """Get a specific email template."""
    # In production, fetch from database
    raise HTTPException(status_code=404, detail="Template not found")


@router.post("/templates", response_model=EmailTemplate)
async def create_template(
    template: EmailTemplateCreate,
):
    """Create a new email template."""
    # In production, save to database
    new_template = EmailTemplate(**template.model_dump())
    return new_template


@router.post("/templates/{template_id}/preview")
async def preview_template(
    template_id: UUID = Path(..., description="Template ID"),
    variables: dict = {},
):
    """Preview a template with sample variables."""
    # In production, fetch template from database
    renderer = TemplateRenderer()
    template = DefaultTemplates.follow_up_template()  # Placeholder

    rendered = renderer.render(template, variables)

    return {
        "subject": rendered["subject"],
        "html": rendered["html"],
        "text": rendered["text"],
    }


@router.post("/templates/validate")
async def validate_template(
    template: EmailTemplateCreate,
    sample_variables: Optional[dict] = None,
):
    """Validate a template and identify required variables."""
    renderer = TemplateRenderer()
    full_template = EmailTemplate(**template.model_dump())

    result = renderer.validate_template(full_template, sample_variables)
    return result


# Health Check
@router.get("/health")
async def email_health_check():
    """Health check for email service."""
    return {
        "status": "ok",
        "service": "email",
        "timestamp": datetime.utcnow().isoformat(),
    }
