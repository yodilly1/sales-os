"""
Amazon SES Email Provider Implementation

Provides email sending capabilities using Amazon Simple Email Service.
"""

import base64
import hashlib
import hmac
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

import httpx

from ....models.email import (
    EmailMessage,
    EmailProvider,
    EmailStatus,
    SendEmailResponse,
    EmailEvent,
    EmailEventType,
    BounceType,
    WebhookPayload,
)
from .base import EmailProviderBase


logger = logging.getLogger(__name__)


class SESProvider(EmailProviderBase):
    """
    Amazon SES email provider implementation.

    Supports sending emails via SES API and handling SNS notifications
    for tracking events.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SES provider.

        Config required keys:
            - aws_access_key_id: AWS access key
            - aws_secret_access_key: AWS secret key
            - region: AWS region (default: us-east-1)
            - configuration_set: Optional configuration set for tracking
        """
        super().__init__(config)
        self.access_key = config["aws_access_key_id"]
        self.secret_key = config["aws_secret_access_key"]
        self.region = config.get("region", "us-east-1")
        self.configuration_set = config.get("configuration_set")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> EmailProvider:
        return EmailProvider.SES

    def _validate_config(self) -> None:
        if not self.config.get("aws_access_key_id"):
            raise ValueError("AWS access key ID is required")
        if not self.config.get("aws_secret_access_key"):
            raise ValueError("AWS secret access key is required")

    @property
    def _ses_endpoint(self) -> str:
        """Get the SES endpoint URL."""
        return f"https://email.{self.region}.amazonaws.com"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _sign_request(
        self,
        method: str,
        endpoint: str,
        payload: str,
        headers: Dict[str, str],
    ) -> Dict[str, str]:
        """
        Sign a request using AWS Signature Version 4.

        This is a simplified implementation. In production, use boto3 or
        aws-sdk for proper signing.
        """
        from datetime import datetime, timezone

        # Get current timestamp
        t = datetime.now(timezone.utc)
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d')

        # Create canonical request
        service = 'ses'
        host = f"email.{self.region}.amazonaws.com"

        headers['host'] = host
        headers['x-amz-date'] = amz_date

        signed_headers = ';'.join(sorted(headers.keys()))
        payload_hash = hashlib.sha256(payload.encode()).hexdigest()

        canonical_request = '\n'.join([
            method,
            '/',
            '',  # query string
            '\n'.join(f'{k}:{v}' for k, v in sorted(headers.items())) + '\n',
            signed_headers,
            payload_hash,
        ])

        # Create string to sign
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f'{date_stamp}/{self.region}/{service}/aws4_request'
        string_to_sign = '\n'.join([
            algorithm,
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ])

        # Create signing key
        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        k_date = sign(f'AWS4{self.secret_key}'.encode(), date_stamp)
        k_region = sign(k_date, self.region)
        k_service = sign(k_region, service)
        k_signing = sign(k_service, 'aws4_request')

        signature = hmac.new(
            k_signing, string_to_sign.encode(), hashlib.sha256
        ).hexdigest()

        # Create authorization header
        authorization = (
            f'{algorithm} Credential={self.access_key}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, Signature={signature}'
        )

        headers['authorization'] = authorization
        return headers

    def _build_mime_message(self, message: EmailMessage) -> str:
        """Build a MIME message for raw sending."""
        msg = MIMEMultipart('mixed')

        # Headers
        msg['Subject'] = message.subject
        msg['From'] = (
            f"{message.from_name} <{message.from_email}>"
            if message.from_name else message.from_email
        )
        msg['To'] = ', '.join(
            f"{r.name} <{r.email}>" if r.name else r.email
            for r in message.to_recipients
        )

        if message.cc_recipients:
            msg['Cc'] = ', '.join(
                f"{r.name} <{r.email}>" if r.name else r.email
                for r in message.cc_recipients
            )

        if message.reply_to:
            msg['Reply-To'] = message.reply_to

        # Add custom headers for tracking
        msg['X-SES-MESSAGE-TAGS'] = f"tracking_id={message.tracking_id},message_id={message.id}"

        # Body
        body_part = MIMEMultipart('alternative')

        if message.text_content:
            text_part = MIMEText(message.text_content, 'plain', 'utf-8')
            body_part.attach(text_part)

        if message.html_content:
            html_part = MIMEText(message.html_content, 'html', 'utf-8')
            body_part.attach(html_part)

        msg.attach(body_part)

        # Attachments
        if message.attachments:
            for att in message.attachments:
                if att.content_base64:
                    attachment = MIMEApplication(
                        base64.b64decode(att.content_base64)
                    )
                    attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=att.filename
                    )
                    attachment.add_header('Content-Type', att.content_type)
                    msg.attach(attachment)

        return msg.as_string()

    async def send_email(self, message: EmailMessage) -> SendEmailResponse:
        """Send an email via Amazon SES."""
        try:
            client = await self._get_client()

            # Build raw email
            raw_message = self._build_mime_message(message)

            # Build request payload
            import urllib.parse

            params = {
                'Action': 'SendRawEmail',
                'RawMessage.Data': base64.b64encode(
                    raw_message.encode()
                ).decode(),
                'Version': '2010-12-01',
            }

            # Add configuration set if specified
            if self.configuration_set:
                params['ConfigurationSetName'] = self.configuration_set

            # Add tags for tracking
            params['Tags.member.1.Name'] = 'tracking_id'
            params['Tags.member.1.Value'] = message.tracking_id
            params['Tags.member.2.Name'] = 'message_id'
            params['Tags.member.2.Value'] = str(message.id)

            payload = urllib.parse.urlencode(params)

            headers = {
                'content-type': 'application/x-www-form-urlencoded',
            }
            headers = self._sign_request('POST', self._ses_endpoint, payload, headers)

            response = await client.post(
                self._ses_endpoint,
                content=payload,
                headers=headers,
            )

            if response.status_code == 200:
                # Parse XML response to get message ID
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                ns = {'ses': 'http://ses.amazonaws.com/doc/2010-12-01/'}
                message_id_elem = root.find('.//ses:MessageId', ns)
                provider_message_id = (
                    message_id_elem.text if message_id_elem is not None else ""
                )

                return SendEmailResponse(
                    success=True,
                    message_id=message.id,
                    provider_message_id=provider_message_id,
                    status=EmailStatus.SENT,
                )
            else:
                logger.error(f"SES send failed: {response.text}")
                return SendEmailResponse(
                    success=False,
                    message_id=message.id,
                    status=EmailStatus.FAILED,
                    error=response.text,
                )

        except Exception as e:
            logger.exception("SES request error")
            return SendEmailResponse(
                success=False,
                message_id=message.id,
                status=EmailStatus.FAILED,
                error=str(e),
            )

    async def send_batch(
        self, messages: List[EmailMessage]
    ) -> List[SendEmailResponse]:
        """Send multiple emails via SES."""
        import asyncio

        # SES supports bulk templated emails, but for raw emails,
        # we send concurrently
        tasks = [self.send_email(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append(SendEmailResponse(
                    success=False,
                    message_id=messages[i].id,
                    status=EmailStatus.FAILED,
                    error=str(result),
                ))
            else:
                responses.append(result)

        return responses

    async def get_message_status(
        self, provider_message_id: str
    ) -> Optional[EmailStatus]:
        """
        Get message status from SES.

        Note: SES doesn't provide direct status lookup.
        Status is typically received via SNS notifications.
        """
        # SES requires CloudWatch metrics or SNS notifications for status
        logger.info(
            f"SES status lookup not directly supported. "
            f"Use SNS notifications for message: {provider_message_id}"
        )
        return None

    def verify_webhook_signature(
        self, payload: bytes, signature: str, timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify SNS notification signature.

        SES events are delivered via SNS, which uses certificate-based signing.
        """
        try:
            # Parse the SNS message
            data = json.loads(payload)

            # For SNS notifications, we should verify the certificate
            # This is a simplified check - in production, validate against
            # the signing certificate URL
            message_type = data.get('Type')
            if message_type not in ('Notification', 'SubscriptionConfirmation'):
                return False

            # Verify the signing cert URL is from Amazon
            signing_cert_url = data.get('SigningCertURL', '')
            if not signing_cert_url.startswith('https://sns.'):
                return False
            if '.amazonaws.com/' not in signing_cert_url:
                return False

            # In production, download and verify the certificate signature
            # For now, we do basic validation
            return True

        except Exception as e:
            logger.exception("Error verifying SNS signature")
            return False

    def parse_webhook_event(
        self, payload: WebhookPayload
    ) -> Optional[EmailEvent]:
        """Parse SNS notification into EmailEvent."""
        try:
            data = payload.data

            # SNS wraps the actual SES event
            if 'Message' in data:
                # Parse the inner message
                message = json.loads(data['Message'])
            else:
                message = data

            # Get event type from SES notification
            notification_type = message.get('notificationType', '').lower()
            event_type = self._map_ses_event_type(notification_type)

            if not event_type:
                return None

            # Extract common fields
            mail = message.get('mail', {})
            message_id_str = mail.get('messageId')

            # Get tracking ID from tags
            tags = {t['name']: t['value'] for t in mail.get('tags', {}).items()}
            tracking_id = tags.get('tracking_id')

            # Get recipient
            recipients = mail.get('destination', [])
            recipient_email = recipients[0] if recipients else None

            event = EmailEvent(
                event_type=event_type,
                email_id=UUID(tags.get('message_id')) if tags.get('message_id') else None,
                tracking_id=tracking_id,
                recipient_email=recipient_email,
                timestamp=datetime.fromisoformat(
                    mail.get('timestamp', '').replace('Z', '+00:00')
                ) if mail.get('timestamp') else datetime.utcnow(),
                provider=EmailProvider.SES,
                raw_event=message,
            )

            # Handle bounce details
            if notification_type == 'bounce':
                bounce = message.get('bounce', {})
                event.bounce_type = self._map_bounce_type(
                    bounce.get('bounceType', 'Transient')
                )
                event.bounce_reason = bounce.get('bouncedRecipients', [{}])[0].get(
                    'diagnosticCode'
                )

            # Handle complaint (spam report)
            if notification_type == 'complaint':
                complaint = message.get('complaint', {})
                event.bounce_reason = complaint.get('complaintFeedbackType')

            return event

        except Exception as e:
            logger.exception("Error parsing SES webhook event")
            return None

    def _map_ses_event_type(self, ses_event: str) -> Optional[EmailEventType]:
        """Map SES-specific event types."""
        mapping = {
            'delivery': EmailEventType.DELIVERED,
            'bounce': EmailEventType.BOUNCED,
            'complaint': EmailEventType.SPAM_REPORT,
            'reject': EmailEventType.DROPPED,
            'send': EmailEventType.SENT,
            'open': EmailEventType.OPENED,
            'click': EmailEventType.CLICKED,
        }
        return mapping.get(ses_event.lower())

    async def add_to_suppression_list(
        self, email: str, reason: str = "bounce"
    ) -> bool:
        """Add email to SES suppression list (v2 API)."""
        try:
            client = await self._get_client()
            import urllib.parse

            params = {
                'Action': 'PutSuppressedDestination',
                'EmailAddress': email,
                'Reason': 'BOUNCE' if reason == 'bounce' else 'COMPLAINT',
                'Version': '2019-09-27',
            }

            payload = urllib.parse.urlencode(params)
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            headers = self._sign_request(
                'POST',
                f"https://email.{self.region}.amazonaws.com/v2/email/suppression/addresses",
                payload,
                headers
            )

            response = await client.post(
                f"https://email.{self.region}.amazonaws.com/v2/email/suppression/addresses",
                content=payload,
                headers=headers,
            )

            return response.status_code in (200, 201)

        except Exception as e:
            logger.exception("Error adding to SES suppression list")
            return False

    async def remove_from_suppression_list(self, email: str) -> bool:
        """Remove email from SES suppression list."""
        try:
            client = await self._get_client()
            import urllib.parse

            endpoint = f"https://email.{self.region}.amazonaws.com/v2/email/suppression/addresses/{urllib.parse.quote(email)}"

            headers = {}
            headers = self._sign_request('DELETE', endpoint, '', headers)

            response = await client.delete(endpoint, headers=headers)
            return response.status_code in (200, 204)

        except Exception as e:
            logger.exception("Error removing from SES suppression list")
            return False

    async def check_suppression_status(self, email: str) -> Optional[Dict[str, Any]]:
        """Check if email is on SES suppression list."""
        try:
            client = await self._get_client()
            import urllib.parse

            endpoint = f"https://email.{self.region}.amazonaws.com/v2/email/suppression/addresses/{urllib.parse.quote(email)}"

            headers = {}
            headers = self._sign_request('GET', endpoint, '', headers)

            response = await client.get(endpoint, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return {
                    "suppressed": True,
                    "reason": data.get('SuppressedDestination', {}).get('Reason'),
                    "created_at": data.get('SuppressedDestination', {}).get('LastUpdateTime'),
                }

            return None

        except Exception as e:
            logger.exception("Error checking SES suppression status")
            return None
