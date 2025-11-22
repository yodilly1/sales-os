"""Team service for managing teams and team members."""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import Team, TeamMember
from app.models.user import User
from app.models.organization import Organization
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberAdd, TeamMemberUpdate


class TeamService:
    """Service for team CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_team(
        self,
        organization_id: str,
        data: TeamCreate,
    ) -> Team:
        """Create a new team within an organization."""
        # Check if team slug already exists in this org
        existing = await self.get_by_slug(organization_id, data.slug)
        if existing:
            raise ValueError(
                f"Team with slug '{data.slug}' already exists in this organization"
            )

        # Check organization limits
        org = await self.db.get(Organization, organization_id)
        if not org:
            raise ValueError("Organization not found")

        current_team_count = (
            await self.db.execute(
                select(func.count())
                .select_from(Team)
                .where(Team.organization_id == organization_id, Team.is_active == True)
            )
        ).scalar() or 0

        if current_team_count >= org.max_teams:
            raise ValueError(
                f"Organization has reached maximum team limit ({org.max_teams})"
            )

        team = Team(
            name=data.name,
            slug=data.slug,
            description=data.description,
            organization_id=organization_id,
            settings=data.settings or {},
        )
        self.db.add(team)
        await self.db.commit()
        await self.db.refresh(team)
        return team

    async def get_by_id(
        self,
        team_id: str,
        include_members: bool = False,
    ) -> Team | None:
        """Get a team by ID."""
        query = select(Team).where(Team.id == team_id)
        if include_members:
            query = query.options(
                selectinload(Team.members).selectinload(TeamMember.user)
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, organization_id: str, slug: str) -> Team | None:
        """Get a team by slug within an organization."""
        result = await self.db.execute(
            select(Team).where(
                Team.organization_id == organization_id,
                Team.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    async def list_teams(
        self,
        organization_id: str,
        page: int = 1,
        per_page: int = 20,
        active_only: bool = True,
    ) -> tuple[list[Team], int]:
        """List teams in an organization with pagination."""
        query = select(Team).where(Team.organization_id == organization_id)
        if active_only:
            query = query.where(Team.is_active == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results with members count
        query = (
            query.options(selectinload(Team.members))
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(query)
        teams = list(result.scalars().all())

        return teams, total

    async def update_team(
        self,
        team_id: str,
        data: TeamUpdate,
    ) -> Team | None:
        """Update a team."""
        team = await self.get_by_id(team_id)
        if not team:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "settings" and value is not None:
                team.settings = {**team.settings, **value}
            else:
                setattr(team, field, value)

        await self.db.commit()
        await self.db.refresh(team)
        return team

    async def delete_team(self, team_id: str, soft_delete: bool = True) -> bool:
        """Delete a team (soft or hard delete)."""
        team = await self.get_by_id(team_id)
        if not team:
            return False

        if soft_delete:
            team.is_active = False
            await self.db.commit()
        else:
            await self.db.delete(team)
            await self.db.commit()
        return True

    # Team Member Management

    async def add_member(
        self,
        team_id: str,
        data: TeamMemberAdd,
    ) -> TeamMember:
        """Add a member to a team."""
        team = await self.get_by_id(team_id)
        if not team:
            raise ValueError("Team not found")

        user = await self.db.get(User, data.user_id)
        if not user:
            raise ValueError("User not found")

        # Check user belongs to same organization
        if user.organization_id != team.organization_id:
            raise ValueError("User does not belong to this organization")

        # Check if already a member
        existing = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == data.user_id,
            )
        )
        existing_member = existing.scalar_one_or_none()
        if existing_member:
            if existing_member.is_active:
                raise ValueError("User is already a member of this team")
            # Reactivate membership
            existing_member.is_active = True
            existing_member.is_team_lead = data.is_team_lead
            await self.db.commit()
            await self.db.refresh(existing_member)
            return existing_member

        member = TeamMember(
            team_id=team_id,
            user_id=data.user_id,
            is_team_lead=data.is_team_lead,
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(
        self,
        team_id: str,
        user_id: str,
        soft_delete: bool = True,
    ) -> bool:
        """Remove a member from a team."""
        result = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False

        if soft_delete:
            member.is_active = False
            await self.db.commit()
        else:
            await self.db.delete(member)
            await self.db.commit()
        return True

    async def update_member(
        self,
        team_id: str,
        user_id: str,
        data: TeamMemberUpdate,
    ) -> TeamMember | None:
        """Update a team member's role or status."""
        result = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)

        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def get_team_members(
        self,
        team_id: str,
        active_only: bool = True,
    ) -> list[TeamMember]:
        """Get all members of a team."""
        query = (
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .options(selectinload(TeamMember.user))
        )
        if active_only:
            query = query.where(TeamMember.is_active == True)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_teams(
        self,
        user_id: str,
        active_only: bool = True,
    ) -> list[Team]:
        """Get all teams a user belongs to."""
        query = (
            select(Team)
            .join(TeamMember)
            .where(TeamMember.user_id == user_id)
        )
        if active_only:
            query = query.where(
                TeamMember.is_active == True,
                Team.is_active == True,
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_team_performance(
        self,
        team_id: str,
    ) -> dict:
        """Get aggregated performance metrics for a team."""
        team = await self.get_by_id(team_id, include_members=True)
        if not team:
            return {}

        active_members = [m for m in team.members if m.is_active]

        # In a full implementation, this would aggregate data from
        # calls, coaching scores, content generation, etc.
        return {
            "team_id": team.id,
            "team_name": team.name,
            "total_members": len(team.members),
            "active_members": len(active_members),
            "total_calls": 0,  # TODO: Aggregate from calls table
            "avg_spiced_score": None,  # TODO: Aggregate from coaching table
            "total_content_generated": 0,  # TODO: Aggregate from content table
        }
