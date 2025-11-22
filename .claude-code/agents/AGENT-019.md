# AGENT-019 — `infra/deployment`

**Branch Name:** `feature/deployment-config`

**Role:** Set up deployment configuration and CI/CD pipeline.

**Responsibilities:**
- Create deployment configs:
  - Docker Compose for local development
  - Dockerfile for backend and frontend
  - Environment configuration templates
- Set up CI/CD:
  - GitHub Actions workflows
  - Automated testing on PR
  - Staging deployment pipeline
- Add infrastructure as code:
  - Database setup scripts
  - Environment provisioning

**Files/Folders Touched:**
- `/docker-compose.yml`
- `/backend/Dockerfile`
- `/frontend/Dockerfile`
- `/.github/workflows/*`
- `/infra/*`

**Dependencies:** AGENT-002, AGENT-003

**Acceptance Criteria:**
- `docker-compose up` starts full stack
- CI runs tests on every PR
- Staging deploys automatically on merge
- Environment variables documented
- Zero-downtime deployment strategy
