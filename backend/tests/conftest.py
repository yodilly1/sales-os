"""
Pytest Configuration and Fixtures for Sales OS Backend Tests

This module provides:
- Database fixtures (test database setup/teardown)
- API client fixtures (TestClient with auth)
- Factory fixtures for creating test data
- Mock fixtures for external services
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import app components (will be available when app is built)
# from app.main import app
# from app.core.config import settings
# from app.db.base import Base
# from app.db.session import get_db


# =============================================================================
# Configuration
# =============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
TEST_DATABASE_URL_SYNC = "sqlite:///./test.db"


# =============================================================================
# Event Loop Fixture
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine (sync)."""
    engine = create_engine(
        TEST_DATABASE_URL_SYNC,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_test_engine():
    """Create an async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a database session for testing (sync)."""
    # Create tables
    # Base.metadata.create_all(bind=test_engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # Drop tables after test
        # Base.metadata.drop_all(bind=test_engine)


@pytest_asyncio.fixture(scope="function")
async def async_db_session(async_test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for testing."""
    # Create tables
    # async with async_test_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        async_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()
            # Drop tables after test
            # async with async_test_engine.begin() as conn:
            #     await conn.run_sync(Base.metadata.drop_all)


# =============================================================================
# Application Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    """Create a test FastAPI application."""
    from fastapi import FastAPI

    app = FastAPI(
        title="Sales OS Test API",
        description="Test API for Sales OS",
        version="0.1.0",
    )

    # Add test routes (will be replaced with actual app routes)
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/api/v1/test")
    async def test_endpoint():
        return {"message": "test"}

    return app


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(
    test_app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated async HTTP client for testing."""
    # Create test auth token
    test_token = "test-auth-token"

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {test_token}",
        },
    ) as client:
        yield client


# =============================================================================
# Mock Data Fixtures
# =============================================================================

@pytest.fixture
def sample_transcript() -> dict[str, Any]:
    """Provide sample transcript data."""
    return {
        "id": "transcript-test-1",
        "title": "Test Sales Call",
        "content": """
            Sales Rep: Hi, thanks for taking the time to chat today.
            Prospect: Of course, I've been looking for a solution like yours.
            Sales Rep: Great! Can you tell me about your current situation?
            Prospect: We're struggling with manual data entry and it's taking up 20 hours a week.
            Sales Rep: That sounds frustrating. What problems is this causing?
            Prospect: We're missing deadlines and our team morale is low.
            Sales Rep: I understand. What would it mean if you could solve this?
            Prospect: It would be huge - we could focus on actually growing the business.
            Sales Rep: And is there a specific timeline you're working with?
            Prospect: We need to have something in place before end of quarter.
        """,
        "duration": 1800,
        "participants": ["Sales Rep", "Prospect"],
        "created_at": "2024-01-15T10:00:00Z",
    }


@pytest.fixture
def sample_spiced_analysis() -> dict[str, Any]:
    """Provide sample SPICED analysis data."""
    return {
        "id": "spiced-test-1",
        "transcript_id": "transcript-test-1",
        "situation": "Company struggling with manual data entry processes affecting productivity",
        "problem": "Spending 20+ hours per week on repetitive data entry tasks",
        "implication": "Missing deadlines, low team morale, unable to focus on growth initiatives",
        "critical_event": "End of quarter deadline approaching",
        "decision": "Need solution in place before end of quarter",
        "confidence": 0.92,
        "created_at": "2024-01-15T10:05:00Z",
    }


@pytest.fixture
def sample_content() -> dict[str, Any]:
    """Provide sample content data."""
    return {
        "id": "content-test-1",
        "type": "proposal",
        "title": "Sales Proposal - Test Company",
        "goal": "Close enterprise deal",
        "product_info": "Sales OS - VP of Sales Operating System",
        "generated_content": "<html><body><h1>Sales Proposal</h1></body></html>",
        "format": "html",
        "created_at": "2024-01-15T11:00:00Z",
    }


@pytest.fixture
def sample_prospect() -> dict[str, Any]:
    """Provide sample prospect data."""
    return {
        "id": "prospect-test-1",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "company": "Example Corp",
        "title": "VP of Sales",
        "phone": "+1-555-0123",
        "linkedin": "https://linkedin.com/in/johndoe",
        "verified": False,
        "crm_synced": False,
        "created_at": "2024-01-15T12:00:00Z",
    }


@pytest.fixture
def sample_company() -> dict[str, Any]:
    """Provide sample company data."""
    return {
        "id": "company-test-1",
        "name": "Example Corporation",
        "domain": "example.com",
        "industry": "Technology",
        "size": "100-500",
        "revenue": "$10M-$50M",
        "location": "San Francisco, CA",
        "description": "A leading technology company",
    }


# =============================================================================
# Mock Service Fixtures
# =============================================================================

@pytest.fixture
def mock_crm_response() -> dict[str, Any]:
    """Provide mock CRM sync response."""
    return {
        "success": True,
        "crm_id": "hubspot-contact-123",
        "crm_type": "hubspot",
        "synced_at": "2024-01-15T12:00:00Z",
    }


@pytest.fixture
def mock_enrichment_response() -> dict[str, Any]:
    """Provide mock enrichment response."""
    return {
        "verified": True,
        "enrichment_data": {
            "email_verified": True,
            "phone_verified": True,
            "linkedin_profile": "https://linkedin.com/in/johndoe",
            "company_info": {
                "name": "Example Corp",
                "industry": "Technology",
                "size": "100-500",
                "revenue": "$10M-$50M",
            },
        },
        "enriched_at": "2024-01-15T12:00:00Z",
    }


@pytest.fixture
def mock_ai_response() -> dict[str, Any]:
    """Provide mock AI/LLM response."""
    return {
        "content": "Generated content here...",
        "model": "claude-3-sonnet",
        "tokens_used": 1500,
        "finish_reason": "stop",
    }


# =============================================================================
# Utility Functions
# =============================================================================

def create_test_user(
    email: str = "test@example.com",
    role: str = "user",
) -> dict[str, Any]:
    """Create a test user dictionary."""
    return {
        "id": "user-test-1",
        "email": email,
        "name": "Test User",
        "role": role,
        "is_active": True,
    }


def create_test_token(user_id: str = "user-test-1") -> str:
    """Create a test JWT token."""
    # In real implementation, use proper JWT encoding
    return f"test-token-{user_id}"
