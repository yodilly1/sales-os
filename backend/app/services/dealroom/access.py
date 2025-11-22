"""
Deal Room Access Service

Handles access control, authentication, and invitations for deal rooms.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.app.models.dealroom import (
    DealRoom, DealRoomInvitation, DealRoomStatus, AccessLevel,
    AccessVerificationRequest, AccessVerificationResponse,
    InvitationCreateRequest, InvitationResponse,
)
from backend.app.services.dealroom.utils import (
    verify_password, generate_access_token, generate_invitation_token,
    is_expired, get_expiry_date,
)

logger = logging.getLogger(__name__)


class DealRoomAccessService:
    """
    Service for managing deal room access control and invitations.
    """

    def __init__(self, db: Session):
        """
        Initialize the access service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # =========================================================================
    # ACCESS VERIFICATION
    # =========================================================================

    def verify_access(
        self,
        deal_room_id: UUID,
        request: AccessVerificationRequest,
    ) -> AccessVerificationResponse:
        """
        Verify if a viewer has access to a deal room.

        Args:
            deal_room_id: UUID of the deal room
            request: Access verification request

        Returns:
            Access verification response
        """
        deal_room = self.db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()

        if not deal_room:
            return AccessVerificationResponse(
                granted=False,
                message="Deal room not found",
            )

        # Check if room is active
        if deal_room.status != DealRoomStatus.ACTIVE:
            return AccessVerificationResponse(
                granted=False,
                message="This deal room is not currently available",
            )

        # Check expiration
        if is_expired(deal_room.expires_at):
            return AccessVerificationResponse(
                granted=False,
                message="This deal room has expired",
            )

        # Check max views
        if deal_room.max_views:
            view_count = len(deal_room.view_events)
            if view_count >= deal_room.max_views:
                return AccessVerificationResponse(
                    granted=False,
                    message="This deal room has reached its view limit",
                )

        # Handle different access levels
        if deal_room.access_level == AccessLevel.PUBLIC:
            return self._grant_access(deal_room, request.email)

        elif deal_room.access_level == AccessLevel.PASSWORD:
            if not request.password:
                return AccessVerificationResponse(
                    granted=False,
                    message="Password required",
                )
            if not deal_room.password_hash:
                return self._grant_access(deal_room, request.email)
            if verify_password(request.password, deal_room.password_hash):
                return self._grant_access(deal_room, request.email)
            return AccessVerificationResponse(
                granted=False,
                message="Invalid password",
            )

        elif deal_room.access_level == AccessLevel.EMAIL_GATE:
            if not request.email:
                return AccessVerificationResponse(
                    granted=False,
                    message="Email required to access this deal room",
                )
            return self._grant_access(deal_room, request.email)

        elif deal_room.access_level == AccessLevel.INVITE_ONLY:
            # Check invitation token
            if request.invitation_token:
                invitation = self._validate_invitation_token(
                    deal_room_id, request.invitation_token
                )
                if invitation:
                    self._mark_invitation_accepted(invitation)
                    return self._grant_access(deal_room, invitation.email)

            # Check if email is in allowed list
            if request.email and deal_room.allowed_emails:
                if request.email.lower() in [e.lower() for e in deal_room.allowed_emails]:
                    return self._grant_access(deal_room, request.email)

            return AccessVerificationResponse(
                granted=False,
                message="You need an invitation to access this deal room",
            )

        return AccessVerificationResponse(
            granted=False,
            message="Access denied",
        )

    def verify_access_by_slug(
        self,
        slug: str,
        request: AccessVerificationRequest,
    ) -> Tuple[Optional[DealRoom], AccessVerificationResponse]:
        """
        Verify access by deal room slug.

        Args:
            slug: URL slug of the deal room
            request: Access verification request

        Returns:
            Tuple of (deal room if found, access response)
        """
        deal_room = self.db.query(DealRoom).filter(DealRoom.slug == slug).first()

        if not deal_room:
            return None, AccessVerificationResponse(
                granted=False,
                message="Deal room not found",
            )

        response = self.verify_access(deal_room.id, request)
        return deal_room, response

    def _grant_access(
        self,
        deal_room: DealRoom,
        email: Optional[str] = None,
    ) -> AccessVerificationResponse:
        """Grant access and generate token."""
        token = generate_access_token(deal_room.id, email)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        return AccessVerificationResponse(
            granted=True,
            access_token=token,
            expires_at=expires_at,
            message="Access granted",
        )

    def check_requires_auth(self, deal_room_id: UUID) -> dict:
        """
        Check what authentication is required for a deal room.

        Args:
            deal_room_id: UUID of the deal room

        Returns:
            Dict with authentication requirements
        """
        deal_room = self.db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()

        if not deal_room:
            return {'error': 'Deal room not found'}

        return {
            'access_level': deal_room.access_level.value,
            'requires_password': deal_room.access_level == AccessLevel.PASSWORD,
            'requires_email': deal_room.access_level in [
                AccessLevel.EMAIL_GATE, AccessLevel.INVITE_ONLY
            ],
            'requires_invitation': deal_room.access_level == AccessLevel.INVITE_ONLY,
            'requires_nda': deal_room.require_nda,
        }

    # =========================================================================
    # INVITATIONS
    # =========================================================================

    def create_invitation(
        self,
        deal_room_id: UUID,
        request: InvitationCreateRequest,
    ) -> Optional[DealRoomInvitation]:
        """
        Create an invitation to a deal room.

        Args:
            deal_room_id: UUID of the deal room
            request: Invitation creation request

        Returns:
            Created invitation or None
        """
        deal_room = self.db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
        if not deal_room:
            return None

        # Check for existing invitation
        existing = self.db.query(DealRoomInvitation).filter(
            and_(
                DealRoomInvitation.deal_room_id == deal_room_id,
                DealRoomInvitation.email == request.email,
                DealRoomInvitation.accepted_at.is_(None),
            )
        ).first()

        if existing:
            # Update existing invitation
            existing.message = request.message
            existing.token = generate_invitation_token()
            existing.expires_at = request.expires_at or get_expiry_date(7)
            existing.sent_at = None  # Will be set when email is sent
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new invitation
        invitation = DealRoomInvitation(
            deal_room_id=deal_room_id,
            email=request.email,
            name=request.name,
            message=request.message,
            token=generate_invitation_token(),
            expires_at=request.expires_at or get_expiry_date(7),
        )

        # Add email to allowed list if invite-only
        if deal_room.access_level == AccessLevel.INVITE_ONLY:
            if not deal_room.allowed_emails:
                deal_room.allowed_emails = []
            if request.email.lower() not in [e.lower() for e in deal_room.allowed_emails]:
                deal_room.allowed_emails.append(request.email)

        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)

        logger.info(f"Created invitation for {request.email} to deal room {deal_room_id}")
        return invitation

    def get_invitation(self, invitation_id: UUID) -> Optional[DealRoomInvitation]:
        """Get an invitation by ID."""
        return self.db.query(DealRoomInvitation).filter(
            DealRoomInvitation.id == invitation_id
        ).first()

    def get_invitation_by_token(self, token: str) -> Optional[DealRoomInvitation]:
        """Get an invitation by token."""
        return self.db.query(DealRoomInvitation).filter(
            DealRoomInvitation.token == token
        ).first()

    def list_invitations(
        self,
        deal_room_id: UUID,
        include_accepted: bool = False,
    ) -> list:
        """
        List invitations for a deal room.

        Args:
            deal_room_id: UUID of the deal room
            include_accepted: Whether to include accepted invitations

        Returns:
            List of invitations
        """
        query = self.db.query(DealRoomInvitation).filter(
            DealRoomInvitation.deal_room_id == deal_room_id
        )

        if not include_accepted:
            query = query.filter(DealRoomInvitation.accepted_at.is_(None))

        return query.order_by(DealRoomInvitation.created_at.desc()).all()

    def mark_invitation_sent(self, invitation_id: UUID) -> Optional[DealRoomInvitation]:
        """Mark an invitation as sent."""
        invitation = self.get_invitation(invitation_id)
        if invitation:
            invitation.sent_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(invitation)
        return invitation

    def mark_invitation_opened(self, token: str) -> Optional[DealRoomInvitation]:
        """Mark an invitation as opened (link clicked)."""
        invitation = self.get_invitation_by_token(token)
        if invitation and not invitation.opened_at:
            invitation.opened_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(invitation)
        return invitation

    def _validate_invitation_token(
        self,
        deal_room_id: UUID,
        token: str,
    ) -> Optional[DealRoomInvitation]:
        """Validate an invitation token."""
        invitation = self.db.query(DealRoomInvitation).filter(
            and_(
                DealRoomInvitation.deal_room_id == deal_room_id,
                DealRoomInvitation.token == token,
            )
        ).first()

        if not invitation:
            return None

        # Check expiration
        if is_expired(invitation.expires_at):
            return None

        # Check if already accepted
        if invitation.accepted_at:
            return None

        return invitation

    def _mark_invitation_accepted(self, invitation: DealRoomInvitation):
        """Mark an invitation as accepted."""
        invitation.accepted_at = datetime.utcnow()
        self.db.commit()

    def delete_invitation(self, invitation_id: UUID) -> bool:
        """Delete an invitation."""
        invitation = self.get_invitation(invitation_id)
        if not invitation:
            return False

        # Remove email from allowed list
        deal_room = self.db.query(DealRoom).filter(
            DealRoom.id == invitation.deal_room_id
        ).first()
        if deal_room and deal_room.allowed_emails:
            deal_room.allowed_emails = [
                e for e in deal_room.allowed_emails
                if e.lower() != invitation.email.lower()
            ]

        self.db.delete(invitation)
        self.db.commit()

        return True

    def resend_invitation(self, invitation_id: UUID) -> Optional[DealRoomInvitation]:
        """
        Resend an invitation by regenerating the token.

        Args:
            invitation_id: UUID of the invitation

        Returns:
            Updated invitation or None
        """
        invitation = self.get_invitation(invitation_id)
        if not invitation:
            return None

        # Regenerate token and reset dates
        invitation.token = generate_invitation_token()
        invitation.sent_at = None
        invitation.opened_at = None
        invitation.expires_at = get_expiry_date(7)

        self.db.commit()
        self.db.refresh(invitation)

        return invitation

    # =========================================================================
    # EMAIL HELPERS
    # =========================================================================

    def get_invitation_link(
        self,
        invitation: DealRoomInvitation,
        base_url: str,
    ) -> str:
        """
        Generate the invitation link for an invitation.

        Args:
            invitation: The invitation
            base_url: Base URL of the application

        Returns:
            Full invitation URL
        """
        deal_room = self.db.query(DealRoom).filter(
            DealRoom.id == invitation.deal_room_id
        ).first()

        if deal_room:
            return f"{base_url}/room/{deal_room.slug}?invite={invitation.token}"
        return f"{base_url}/invite/{invitation.token}"

    def to_response(self, invitation: DealRoomInvitation) -> InvitationResponse:
        """Convert invitation to response schema."""
        return InvitationResponse(
            id=invitation.id,
            deal_room_id=invitation.deal_room_id,
            email=invitation.email,
            name=invitation.name,
            message=invitation.message,
            token=invitation.token,
            sent_at=invitation.sent_at,
            opened_at=invitation.opened_at,
            accepted_at=invitation.accepted_at,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )
