# AGENT-002 — `backend/api-foundation`

**Branch Name:** `feature/backend-api-foundation`

**Role:** Set up the backend API foundation with FastAPI, project structure, and core configuration.

**Responsibilities:**
- Initialize FastAPI application in `/backend`
- Create folder structure:
  - `/backend/app/` - Main application
  - `/backend/app/api/` - API routes
  - `/backend/app/core/` - Config, settings, constants
  - `/backend/app/models/` - Pydantic models
  - `/backend/app/services/` - Business logic
  - `/backend/app/integrations/` - External service connectors
- Add `requirements.txt` with FastAPI, uvicorn, pydantic, python-dotenv
- Create `main.py` with health check endpoint
- Add `.env.example` for backend

**Files/Folders Touched:**
- `/backend/*`

**Dependencies:** AGENT-001

**Acceptance Criteria:**
- `uvicorn app.main:app` runs without error
- `/health` endpoint returns `{"status": "ok"}`
- Clean folder structure committed
