"""Team-based data isolation middleware and utilities."""

from typing import TypeVar, Generic
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.team import TeamMember

T = TypeVar("T")


class DataIsolationFilter:
    """
    Utility class for filtering queries based on user's team membership
    and role permissions.

    This implements team-based data isolation:
    - Admins can see all data in their organization
    - Managers can see data for teams they lead
    - Reps can only see their own data
    """

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    def get_accessible_user_ids(self) -> list[str]:
        """
        Get list of user IDs this user can access based on their role.
        Returns None if user can access all users in org (admin).
        """
        if self.user.is_admin:
            return None  # Can access all

        accessible_ids = [self.user.id]  # Always can access self

        if self.user.is_manager:
            # Can access team members from teams they lead
            for membership in self.user.team_memberships:
                if membership.is_team_lead and membership.is_active:
                    for team_member in membership.team.members:
                        if team_member.is_active:
                            accessible_ids.append(team_member.user_id)

        return list(set(accessible_ids))

    async def get_accessible_team_ids(self) -> list[str]:
        """
        Get list of team IDs this user can access.
        Returns None if user can access all teams (admin).
        """
        if self.user.is_admin:
            return None  # Can access all

        return [
            m.team_id
            for m in self.user.team_memberships
            if m.is_active
        ]

    def can_access_user(self, target_user_id: str) -> bool:
        """Check if the current user can access data for another user."""
        if self.user.id == target_user_id:
            return True

        if self.user.is_admin:
            return True

        if self.user.is_manager:
            for membership in self.user.team_memberships:
                if membership.is_team_lead and membership.is_active:
                    for team_member in membership.team.members:
                        if (
                            team_member.user_id == target_user_id
                            and team_member.is_active
                        ):
                            return True
        return False

    def can_access_team(self, team_id: str) -> bool:
        """Check if the current user can access data for a team."""
        if self.user.is_admin:
            return True

        return any(
            m.team_id == team_id and m.is_active
            for m in self.user.team_memberships
        )

    def can_manage_team(self, team_id: str) -> bool:
        """Check if the current user can manage (edit) a team."""
        if self.user.is_admin:
            return True

        return any(
            m.team_id == team_id and m.is_team_lead and m.is_active
            for m in self.user.team_memberships
        )


class OrganizationScopedQuery:
    """
    Mixin for applying organization-level data isolation to queries.

    All data queries should be scoped to the user's organization.
    """

    @staticmethod
    def apply_org_filter(query, model, organization_id: str):
        """Apply organization filter to a query."""
        if hasattr(model, "organization_id"):
            return query.where(model.organization_id == organization_id)
        return query


class TeamScopedQuery:
    """
    Mixin for applying team-level data isolation to queries.

    Data can be scoped to specific teams based on user permissions.
    """

    @staticmethod
    def apply_team_filter(query, model, team_ids: list[str] | None):
        """Apply team filter to a query. None means no filtering (full access)."""
        if team_ids is None:
            return query  # No filtering for admins

        if hasattr(model, "team_id"):
            return query.where(model.team_id.in_(team_ids))
        return query


class UserScopedQuery:
    """
    Mixin for applying user-level data isolation to queries.

    Data can be scoped to specific users based on permissions.
    """

    @staticmethod
    def apply_user_filter(query, model, user_ids: list[str] | None):
        """Apply user filter to a query. None means no filtering (full access)."""
        if user_ids is None:
            return query  # No filtering for admins

        if hasattr(model, "user_id"):
            return query.where(model.user_id.in_(user_ids))
        elif hasattr(model, "owner_id"):
            return query.where(model.owner_id.in_(user_ids))
        elif hasattr(model, "created_by_id"):
            return query.where(model.created_by_id.in_(user_ids))
        return query


def create_isolated_query(
    model,
    user: User,
    organization_id: str,
    team_filter: bool = True,
    user_filter: bool = False,
):
    """
    Create a query with appropriate data isolation based on user role.

    Args:
        model: The SQLAlchemy model to query
        user: The current user
        organization_id: The organization ID to scope to
        team_filter: Whether to apply team-level filtering
        user_filter: Whether to apply user-level filtering (stricter)

    Returns:
        A SQLAlchemy select query with appropriate filters
    """
    query = select(model)

    # Always apply organization filter
    query = OrganizationScopedQuery.apply_org_filter(query, model, organization_id)

    # Apply team filter if needed
    if team_filter and not user.is_admin:
        team_ids = [
            m.team_id
            for m in user.team_memberships
            if m.is_active
        ]
        query = TeamScopedQuery.apply_team_filter(query, model, team_ids)

    # Apply user filter if needed (strictest isolation)
    if user_filter and not user.is_admin:
        filter_instance = DataIsolationFilter(None, user)
        user_ids = filter_instance.get_accessible_user_ids()
        query = UserScopedQuery.apply_user_filter(query, model, user_ids)

    return query


# Example usage in a service:
"""
async def get_calls_for_user(
    db: AsyncSession,
    user: User,
) -> list[Call]:
    # Create an isolated query that respects team boundaries
    query = create_isolated_query(
        model=Call,
        user=user,
        organization_id=user.organization_id,
        team_filter=True,
        user_filter=False,  # Managers can see team calls
    )

    result = await db.execute(query)
    return list(result.scalars().all())
"""
