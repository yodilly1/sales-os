"""
Base model configuration for SQLAlchemy ORM.

This module provides the declarative base class used by all database models
in the Sales OS application.
"""

from sqlalchemy.orm import declarative_base

# Create the declarative base class
Base = declarative_base()
