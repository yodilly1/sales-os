"""Invitation service for managing user invitations."""

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invitation import Invitation, InvitationStatus
from app.models.user import User, UserRole
from app.models.team import TeamMember
from app.models.organization import Organization
from app.schemas.invitation import InvitationCreate
from app.core.security import (
    get_password_hash,
    create_invitation_token,
    decode_invitation_token,
)


class InvitationService:
    """Service for invitation CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invitation(
        self,
        organization_id: str,
        data: InvitationCreate,
        invited_by_id: str,
    ) -> Invitation:
        """Create a new invitation."""
        # Check if user already exists
        existing_user = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if existing_user.scalar_one_or_none():
            raise ValueError(f"User with email '{data.email}' already exists")

        # Check for pending invitation
        existing_invite = await self.get_pending_by_email(
            organization_id, data.email
        )
        if existing_invite:
            raise ValueError(
                f"A pending invitation already exists for '{data.email}'"
            )

        # Check organization limits
        org = await self.db.get(Organization, organization_id)
        if not org:
            raise ValueError("Organization not found")

        current_user_count = (
            await self.db.execute(
                select(func.count())
                .select_from(User)
                .where(User.organization_id == organization_id, User.is_active == True)
            )
        ).scalar() or 0

        pending_invite_count = (
            await self.db.execute(
                select(func.count())
                .select_from(Invitation)
                .where(
                    Invitation.organization_id == organization_id,
                    Invitation.status == InvitationStatus.PENDING.value,
                )
            )
        ).scalar() or 0

        if current_user_count + pending_invite_count >= org.max_users:
            raise ValueError(
                f"Organization has reached maximum user limit ({org.max_users})"
            )

        # Generate invitation token
        token = create_invitation_token(
            invitation_id="pending",  # Will update after creation
            email=data.email,
        )

        # Create invitation
        role_value = data.role.value if isinstance(data.role, UserRole) else data.role
        invitation = Invitation.create_with_expiry(
            email=data.email,
            token=token,
            organization_id=organization_id,
            invited_by_id=invited_by_id,
            role=role_value,
            team_id=data.team_id,
            message=data.message,
        )
        self.db.add(invitation)
        await self.db.flush()

        # Update token with actual invitation ID
        invitation.token = create_invitation_token(
            invitation_id=invitation.id,
            email=data.email,
        )
        await self.db.commit()
        await self.db.refresh(invitation)

        return invitation

    async def get_by_id(self, invitation_id: str) -> Invitation | None:
        """Get an invitation by ID."""
        result = await self.db.execute(
            select(Invitation)
            .where(Invitation.id == invitation_id)
            .options(
                selectinload(Invitation.organization),
                selectinload(Invitation.team),
                selectinload(Invitation.invited_by),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Invitation | None:
        """Get an invitation by token."""
        result = await self.db.execute(
            select(Invitation)
            .where(Invitation.token == token)
            .options(
                selectinload(Invitation.organization),
                selectinload(Invitation.team),
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_by_email(
        self,
        organization_id: str,
        email: str,
    ) -> Invitation | None:
        """Get a pending invitation for an email in an organization."""
        result = await self.db.execute(
            select(Invitation).where(
                Invitation.organization_id == organization_id,
                Invitation.email == email,
                Invitation.status == InvitationStatus.PENDING.value,
            )
        )
        return result.scalar_one_or_none()

    async def list_invitations(
        self,
        organization_id: str,
        page: int = 1,
        per_page: int = 20,
        status: InvitationStatus | None = None,
    ) -> tuple[list[Invitation], int]:
        """List invitations in an organization with pagination."""
        query = (
            select(Invitation)
            .where(Invitation.organization_id == organization_id)
            .options(selectinload(Invitation.invited_by))
        )

        if status:
            query = query.where(Invitation.status == status.value)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        invitations = list(result.scalars().all())

        return invitations, total

    async def accept_invitation(
        self,
        token: str,
        full_name: str,
        password: str,
    ) -> User:
        """Accept an invitation and create the user."""
        # Validate token
        token_data = decode_invitation_token(token)
        if not token_data:
            raise ValueError("Invalid or expired invitation token")

        invitation = await self.get_by_token(token)
        if not invitation:
            raise ValueError("Invitation not found")

        if not invitation.is_valid:
            if invitation.is_expired:
                invitation.mark_expired()
                await self.db.commit()
                raise ValueError("Invitation has expired")
            raise ValueError("Invitation is no longer valid")

        # Check if email already registered (edge case)
        existing_user = await self.db.execute(
            select(User).where(User.email == invitation.email)
        )
        if existing_user.scalar_one_or_none():
            raise ValueError("An account with this email already exists")

        # Create user
        user = User(
            email=invitation.email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            organization_id=invitation.organization_id,
            role=invitation.role,
            is_verified=True,  # Verified via invitation
        )
        self.db.add(user)
        await self.db.flush()

        # Add to team if specified
        if invitation.team_id:
            team_member = TeamMember(
                team_id=invitation.team_id,
                user_id=user.id,
                is_team_lead=False,
            )
            self.db.add(team_member)

        # Mark invitation as accepted
        invitation.accept()
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def revoke_invitation(self, invitation_id: str) -> bool:
        """Revoke a pending invitation."""
        invitation = await self.get_by_id(invitation_id)
        if not invitation:
            return False

        if invitation.status != InvitationStatus.PENDING.value:
            raise ValueError("Can only revoke pending invitations")

        invitation.revoke()
        await self.db.commit()
        return True

    async def resend_invitation(self, invitation_id: str) -> Invitation:
        """Resend an invitation with a new token and expiry."""
        invitation = await self.get_by_id(invitation_id)
        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.status == InvitationStatus.ACCEPTED.value:
            raise ValueError("Cannot resend an accepted invitation")

        # Generate new token and reset expiry
        invitation.token = create_invitation_token(
            invitation_id=invitation.id,
            email=invitation.email,
        )
        invitation.status = InvitationStatus.PENDING.value
        # Update expires_at through the create_with_expiry pattern
        from datetime import timedelta
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(hours=72)

        await self.db.commit()
        await self.db.refresh(invitation)

        return invitation

    async def cleanup_expired_invitations(self, organization_id: str) -> int:
        """Mark all expired invitations as expired."""
        result = await self.db.execute(
            select(Invitation).where(
                Invitation.organization_id == organization_id,
                Invitation.status == InvitationStatus.PENDING.value,
                Invitation.expires_at < datetime.now(timezone.utc),
            )
        )
        expired_invitations = result.scalars().all()

        count = 0
        for invitation in expired_invitations:
            invitation.mark_expired()
            count += 1

        if count > 0:
            await self.db.commit()

        return count
