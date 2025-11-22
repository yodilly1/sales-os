"""User service for managing users within organizations."""

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole
from app.models.team import TeamMember
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service for user CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self,
        organization_id: str,
        data: UserCreate,
    ) -> User:
        """Create a new user in an organization."""
        # Check if email already exists
        existing = await self.get_by_email(data.email)
        if existing:
            raise ValueError(f"User with email '{data.email}' already exists")

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=get_password_hash(data.password),
            organization_id=organization_id,
            role=data.role.value if isinstance(data.role, UserRole) else data.role,
            title=data.title,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(
        self,
        user_id: str,
        include_teams: bool = False,
    ) -> User | None:
        """Get a user by ID."""
        query = select(User).where(User.id == user_id)
        if include_teams:
            query = query.options(
                selectinload(User.team_memberships).selectinload(TeamMember.team)
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list_users(
        self,
        organization_id: str,
        page: int = 1,
        per_page: int = 20,
        active_only: bool = True,
        role: UserRole | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """List users in an organization with pagination and filtering."""
        query = select(User).where(User.organization_id == organization_id)

        if active_only:
            query = query.where(User.is_active == True)

        if role:
            query = query.where(User.role == role.value)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total

    async def update_user(
        self,
        user_id: str,
        data: UserUpdate,
        requesting_user: User | None = None,
    ) -> User | None:
        """Update a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Check permissions for role changes
        if "role" in update_data:
            if requesting_user and not requesting_user.is_admin:
                raise PermissionError("Only admins can change user roles")
            update_data["role"] = (
                update_data["role"].value
                if isinstance(update_data["role"], UserRole)
                else update_data["role"]
            )

        # Check permissions for activation changes
        if "is_active" in update_data:
            if requesting_user and not requesting_user.is_admin:
                raise PermissionError("Only admins can activate/deactivate users")

        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user (soft delete)."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        await self.db.commit()
        return True

    async def reactivate_user(self, user_id: str) -> bool:
        """Reactivate a deactivated user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_active = True
        await self.db.commit()
        return True

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change a user's password."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        return True

    async def reset_password(
        self,
        user_id: str,
        new_password: str,
    ) -> bool:
        """Reset a user's password (admin action)."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        return True

    async def verify_user(self, user_id: str) -> bool:
        """Mark a user as verified."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_verified = True
        await self.db.commit()
        return True

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> User | None:
        """Authenticate a user by email and password."""
        user = await self.get_by_email(email)
        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def get_users_by_team(
        self,
        team_id: str,
        active_only: bool = True,
    ) -> list[User]:
        """Get all users in a specific team."""
        query = (
            select(User)
            .join(TeamMember)
            .where(TeamMember.team_id == team_id)
        )
        if active_only:
            query = query.where(
                TeamMember.is_active == True,
                User.is_active == True,
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())
