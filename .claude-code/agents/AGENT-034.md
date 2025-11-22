# AGENT-034 — `workflow/meeting-prep`

**Branch Name:** `feature/meeting-prep`

**Role:** Build automated meeting preparation briefs.

**Responsibilities:**
- Create meeting prep service in `/backend/app/services/meetingprep/`
- Auto-generate prep briefs including:
  - Attendee profiles (from enrichment)
  - Company research summary
  - Previous call history and SPICED context
  - Suggested agenda and questions
  - Relevant content recommendations
- Delivery:
  - Email brief before meeting
  - In-app prep view
  - Calendar event attachment

**Files/Folders Touched:**
- `/backend/app/services/meetingprep/*`
- `/backend/app/api/meetingprep.py`
- `/backend/app/models/meetingprep.py`
- `/claude/prompts/meeting_prep.md`
- `/frontend/app/prep/*`

**Dependencies:** AGENT-002, AGENT-007, AGENT-027, AGENT-005

**Acceptance Criteria:**
- Briefs generate automatically before meetings
- Content is relevant and actionable
- Previous context included accurately
- Delivery methods all work
- Can manually trigger regeneration
