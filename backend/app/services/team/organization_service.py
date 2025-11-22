"""Organization service for managing organizations."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.core.security import get_password_hash


class OrganizationService:
    """Service for organization CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_organization(
        self,
        data: OrganizationCreate,
        admin_email: str,
        admin_password: str,
        admin_name: str,
    ) -> tuple[Organization, User]:
        """Create a new organization with an admin user."""
        # Check if organization slug already exists
        existing = await self.get_by_slug(data.slug)
        if existing:
            raise ValueError(f"Organization with slug '{data.slug}' already exists")

        # Check if user email already exists
        existing_user = await self.db.execute(
            select(User).where(User.email == admin_email)
        )
        if existing_user.scalar_one_or_none():
            raise ValueError(f"User with email '{admin_email}' already exists")

        # Create organization
        org = Organization(
            name=data.name,
            slug=data.slug,
            description=data.description,
            logo_url=data.logo_url,
            primary_color=data.primary_color,
            settings=data.settings or Organization().default_settings,
        )
        self.db.add(org)
        await self.db.flush()  # Get the org ID

        # Create admin user
        admin_user = User(
            email=admin_email,
            full_name=admin_name,
            hashed_password=get_password_hash(admin_password),
            organization_id=org.id,
            role=UserRole.ADMIN.value,
            is_verified=True,
        )
        self.db.add(admin_user)
        await self.db.commit()
        await self.db.refresh(org)
        await self.db.refresh(admin_user)

        return org, admin_user

    async def get_by_id(self, org_id: str) -> Organization | None:
        """Get an organization by ID."""
        result = await self.db.execute(
            select(Organization)
            .where(Organization.id == org_id)
            .options(selectinload(Organization.teams))
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Get an organization by slug."""
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_organizations(
        self,
        page: int = 1,
        per_page: int = 20,
        active_only: bool = True,
    ) -> tuple[list[Organization], int]:
        """List organizations with pagination."""
        query = select(Organization)
        if active_only:
            query = query.where(Organization.is_active == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        organizations = list(result.scalars().all())

        return organizations, total

    async def update_organization(
        self,
        org_id: str,
        data: OrganizationUpdate,
    ) -> Organization | None:
        """Update an organization."""
        org = await self.get_by_id(org_id)
        if not org:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "settings" and value is not None:
                # Merge settings instead of replacing
                org.update_settings(value)
            else:
                setattr(org, field, value)

        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def deactivate_organization(self, org_id: str) -> bool:
        """Deactivate an organization (soft delete)."""
        org = await self.get_by_id(org_id)
        if not org:
            return False

        org.is_active = False
        await self.db.commit()
        return True

    async def reactivate_organization(self, org_id: str) -> bool:
        """Reactivate a deactivated organization."""
        org = await self.get_by_id(org_id)
        if not org:
            return False

        org.is_active = True
        await self.db.commit()
        return True

    async def get_organization_stats(self, org_id: str) -> dict:
        """Get statistics for an organization."""
        org = await self.get_by_id(org_id)
        if not org:
            return {}

        # Count users
        user_count = (
            await self.db.execute(
                select(func.count())
                .select_from(User)
                .where(User.organization_id == org_id, User.is_active == True)
            )
        ).scalar() or 0

        # Count active users by role
        role_counts = {}
        for role in UserRole:
            count = (
                await self.db.execute(
                    select(func.count())
                    .select_from(User)
                    .where(
                        User.organization_id == org_id,
                        User.role == role.value,
                        User.is_active == True,
                    )
                )
            ).scalar() or 0
            role_counts[role.value] = count

        return {
            "total_users": user_count,
            "users_by_role": role_counts,
            "total_teams": len([t for t in org.teams if t.is_active]),
            "max_users": org.max_users,
            "max_teams": org.max_teams,
            "plan": org.plan,
        }
