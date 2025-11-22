"""
User and Team Factories

Provides factory classes for creating user and team test data.
"""

from datetime import datetime, timezone
from typing import Any

import factory
from faker import Faker

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for creating User test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"user-{fake.uuid4()[:8]}")
    email = factory.LazyFunction(lambda: fake.email())
    name = factory.LazyFunction(lambda: fake.name())
    role = factory.LazyFunction(lambda: fake.random_element(["admin", "user", "viewer"]))
    is_active = True
    avatar_url = factory.LazyFunction(lambda: f"https://ui-avatars.com/api/?name={fake.name().replace(' ', '+')}")
    team_id = factory.LazyFunction(lambda: f"team-{fake.uuid4()[:8]}")
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    last_login = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    preferences = factory.LazyFunction(lambda: {
        "theme": "light",
        "notifications_enabled": True,
        "default_crm": "hubspot",
    })

    @classmethod
    def create_admin(cls, **kwargs) -> dict[str, Any]:
        """Create an admin user."""
        return cls.create(role="admin", **kwargs)

    @classmethod
    def create_viewer(cls, **kwargs) -> dict[str, Any]:
        """Create a viewer user."""
        return cls.create(role="viewer", **kwargs)


class TeamFactory(factory.Factory):
    """Factory for creating Team test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"team-{fake.uuid4()[:8]}")
    name = factory.LazyFunction(lambda: f"{fake.company()} Sales Team")
    organization_id = factory.LazyFunction(lambda: f"org-{fake.uuid4()[:8]}")
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    settings = factory.LazyFunction(lambda: {
        "default_crm": "hubspot",
        "auto_sync_enabled": True,
        "spiced_auto_analyze": True,
    })
    member_count = factory.LazyFunction(lambda: fake.random_int(min=3, max=20))

    @classmethod
    def create_with_members(cls, member_count: int = 5, **kwargs) -> dict[str, Any]:
        """Create a team with members."""
        team = cls.create(member_count=member_count, **kwargs)
        members = [
            UserFactory.create(team_id=team["id"])
            for _ in range(member_count)
        ]
        return {"team": team, "members": members}
