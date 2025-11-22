# AGENT-011 — `data/models-schemas`

**Branch Name:** `feature/data-models-schemas`

**Role:** Define core data models, database schemas, and shared types.

**Responsibilities:**
- Create database models in `/backend/app/models/`
- Define core entities:
  - User, Team, Organization
  - Call, Transcript, SPICEDAnalysis
  - Content, ContentTemplate
  - Prospect, Company
  - CoachingReport, CoachingScore
- Set up database with SQLAlchemy/Prisma
- Create Pydantic schemas for API validation
- Add migration system

**Files/Folders Touched:**
- `/backend/app/models/*`
- `/backend/app/db/*`
- `/data/schemas/*`
- `/backend/alembic/` (migrations)

**Dependencies:** AGENT-002

**Acceptance Criteria:**
- All core entities defined
- Database migrations work
- Pydantic schemas validate correctly
- Relationships properly defined
- Schema documentation generated
