# AGENT-012 — `security/auth`

**Branch Name:** `feature/auth-security`

**Role:** Implement authentication, authorization, and security infrastructure.

**Responsibilities:**
- Set up authentication in `/backend/app/core/auth/`
- Implement:
  - JWT token generation and validation
  - OAuth2 flow for integrations
  - API key management
  - Role-based access control (RBAC)
- Secure endpoints with middleware
- Add rate limiting
- Implement audit logging

**Files/Folders Touched:**
- `/backend/app/core/auth/*`
- `/backend/app/core/security.py`
- `/backend/app/middleware/`
- `/backend/app/api/auth.py`
- `/frontend/lib/auth.ts`

**Dependencies:** AGENT-002, AGENT-003, AGENT-011

**Acceptance Criteria:**
- JWT auth works end-to-end
- Protected routes require valid token
- OAuth2 flow for HubSpot/Avoma
- Rate limiting prevents abuse
- Audit logs capture key actions
