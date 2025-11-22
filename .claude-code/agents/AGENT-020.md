# AGENT-020 — `testing/e2e`

**Branch Name:** `feature/e2e-testing`

**Role:** Set up end-to-end testing infrastructure and core test suites.

**Responsibilities:**
- Set up testing frameworks:
  - Playwright for frontend E2E
  - Pytest for backend integration tests
- Create core test suites:
  - Transcript → SPICED → CRM flow
  - Content generation → Export flow
  - Prospect enrichment → CRM sync flow
- Add test fixtures and mocks
- Configure test coverage reporting

**Files/Folders Touched:**
- `/frontend/tests/*`
- `/backend/tests/*`
- `/playwright.config.ts`
- `/backend/pytest.ini`
- `/.github/workflows/test.yml`

**Dependencies:** AGENT-002, AGENT-003, AGENT-005, AGENT-006, AGENT-007

**Acceptance Criteria:**
- All 3 core workflows have E2E tests
- Tests run in CI pipeline
- Coverage reporting configured
- Test fixtures are reusable
- Tests are deterministic and fast
