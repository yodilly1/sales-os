# AGENT-035 — `workflow/follow-up-automation`

**Branch Name:** `feature/follow-up-automation`

**Role:** Build automated follow-up generation and scheduling.

**Responsibilities:**
- Create follow-up service in `/backend/app/services/followup/`
- Auto-generate from call analysis:
  - Follow-up email drafts
  - Task/reminder creation
  - Content recommendations to send
  - Next meeting suggestions
- Automation features:
  - Scheduled send times
  - Approval workflow (auto/manual)
  - Sequence support (multi-touch)
  - CRM task sync

**Files/Folders Touched:**
- `/backend/app/services/followup/*`
- `/backend/app/api/followup.py`
- `/backend/app/models/followup.py`
- `/claude/prompts/followup_generation.md`
- `/frontend/components/followup/*`

**Dependencies:** AGENT-002, AGENT-005, AGENT-026, AGENT-004

**Acceptance Criteria:**
- Follow-ups generated from SPICED analysis
- Emails are personalized and relevant
- Scheduling works reliably
- Approval flow configurable
- Tasks sync to CRM correctly
