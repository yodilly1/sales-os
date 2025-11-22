# AGENT-028 — `backend/team-management`

**Branch Name:** `feature/team-management`

**Role:** Build team and organization management features.

**Responsibilities:**
- Create team service in `/backend/app/services/team/`
- Implement:
  - Organization creation and settings
  - Team creation within orgs
  - User invitations (email invite flow)
  - Role assignment (admin, manager, rep)
  - Team-based data isolation
- Features:
  - Org-wide settings inheritance
  - Team performance aggregation
  - User deactivation/reactivation

**Files/Folders Touched:**
- `/backend/app/services/team/*`
- `/backend/app/api/team.py`
- `/backend/app/api/organization.py`
- `/backend/app/models/team.py`
- `/frontend/app/team/*`

**Dependencies:** AGENT-002, AGENT-011, AGENT-012

**Acceptance Criteria:**
- Orgs and teams CRUD works
- Invitations send and can be accepted
- Roles enforce correct permissions
- Data properly isolated by team
- Admin can manage all users
