# AGENT-025 — `backend/activity-log`

**Branch Name:** `feature/activity-logging`

**Role:** Build comprehensive activity logging and audit trail system.

**Responsibilities:**
- Create activity service in `/backend/app/services/activity/`
- Log all key actions:
  - User actions (login, settings changes)
  - Transcript processing events
  - Content generation events
  - CRM sync operations
  - Integration events
- Implement:
  - Structured log format
  - Activity feed API
  - Audit trail for compliance
  - Log retention policies

**Files/Folders Touched:**
- `/backend/app/services/activity/*`
- `/backend/app/api/activity.py`
- `/backend/app/models/activity.py`
- `/backend/app/middleware/activity_logger.py`

**Dependencies:** AGENT-002, AGENT-011

**Acceptance Criteria:**
- All key actions logged automatically
- Activity feed displays chronologically
- Audit trail queryable by date/user/action
- Logs don't impact performance
- Retention policy enforced
