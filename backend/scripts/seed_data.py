import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

from app.models import (
    User, Organization, Company, Prospect, Call, Transcript, SPICEDAnalysis,
    Team, ContentTemplate
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_data():
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Starting database seed...")

            # 1. Create Organization
            org_id = uuid4()
            org = Organization(
                id=org_id,
                name="Demo Organization",
                industry="Technology",
                size="50-200",
                domain="demo.salesos.dev",
                settings=json.dumps({"theme": "dark"})
            )
            session.add(org)
            logger.info(f"Created Organization: {org.name}")

            # 2. Create Team
            team_id = uuid4()
            team = Team(
                id=team_id,
                name="Sales Team Alpha",
                description="Top performing sales team",
                organization_id=org_id
            )
            session.add(team)
            logger.info(f"Created Team: {team.name}")

            # 3. Create Admin User
            user_id = uuid4()
            admin_user = User(
                id=user_id,
                email="admin@salesos.dev",
                password_hash=get_password_hash("admin123"),
                first_name="Admin",
                last_name="User",
                role="admin",
                is_active=True,
                is_verified=True,
                organization_id=org_id,
                team_id=team_id
            )
            session.add(admin_user)
            logger.info(f"Created Admin User: {admin_user.email}")
            sys.stdout.flush()

            # Update team manager
            team.manager_id = user_id

            # 4. Create Company
            company_id = uuid4()
            company = Company(
                id=company_id,
                name="Acme Corp",
                domain="acme.com",
                industry="Software",
                employee_count=500,
                description="Leading provider of coyote catching equipment.",
                is_verified=True
            )
            session.add(company)
            logger.info(f"Created Company: {company.name}")

            # 5. Create Prospect
            prospect_id = uuid4()
            prospect = Prospect(
                id=prospect_id,
                first_name="John",
                last_name="Doe",
                email="john.doe@acme.com",
                title="VP of Sales",
                company_id=company_id,
                status="qualified",
                is_verified=True
            )
            session.add(prospect)
            logger.info(f"Created Prospect: {prospect.first_name} {prospect.last_name}")

            # 6. Create Call
            call_id = uuid4()
            call = Call(
                id=call_id,
                title="Discovery Call with Acme Corp",
                source="zoom",
                status="processed",
                started_at=datetime.utcnow() - timedelta(days=1),
                ended_at=datetime.utcnow() - timedelta(days=1) + timedelta(minutes=30),
                duration_seconds=1800,
                user_id=user_id,
                prospect_id=prospect_id,
                company_id=company_id
            )
            session.add(call)
            logger.info(f"Created Call: {call.title}")

            # 7. Create Transcript
            transcript_id = uuid4()
            transcript = Transcript(
                id=transcript_id,
                call_id=call_id,
                raw_text="Sales Rep: Hi John, thanks for joining.\nJohn: Happy to be here.\nSales Rep: Tell me about your pain points.\nJohn: We need better coyote traps.",
                language="en",
                confidence_score=0.98
            )
            session.add(transcript)
            logger.info("Created Transcript")

            # 8. Create SPICED Analysis
            spiced_id = uuid4()
            spiced = SPICEDAnalysis(
                id=spiced_id,
                call_id=call_id,
                situation="Acme Corp is looking to expand their product line.",
                pain="Current traps are failing, causing customer churn.",
                impact="Losing $1M/year in revenue.",
                critical_event="Q4 launch deadline.",
                decision_criteria="Must be durable and affordable.",
                overall_score=8.5
            )
            session.add(spiced)
            logger.info("Created SPICED Analysis")

            await session.commit()
            logger.info("Database seed completed successfully!")

        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_data())
