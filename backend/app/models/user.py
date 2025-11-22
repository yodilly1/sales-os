"""User, Team, and Organization models."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from pydantic import EmailStr

from .base import BaseDBModel, BaseModel, TimestampedSchema


class UserRole(str, Enum):
    """User role in the organization."""

    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"


class Organization(BaseDBModel):
    """Organization/workspace model."""

    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True)
    is_active = Column(Boolean, default=True)


class Team(BaseDBModel):
    """Team within an organization."""

    __tablename__ = "teams"

    name = Column(String(255), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)


class User(BaseDBModel):
    """User model."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255))
    role = Column(SQLEnum(UserRole), default=UserRole.SALES_REP)
    is_active = Column(Boolean, default=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"))


# Pydantic Schemas
class OrganizationSchema(TimestampedSchema):
    """Organization response schema."""

    name: str
    domain: Optional[str] = None
    is_active: bool = True


class TeamSchema(TimestampedSchema):
    """Team response schema."""

    name: str
    organization_id: str


class UserSchema(TimestampedSchema):
    """User response schema."""

    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    organization_id: str
    team_id: Optional[str] = None


class UserCreate(BaseModel):
    """User creation schema."""

    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.SALES_REP
    organization_id: str
    team_id: Optional[str] = None
