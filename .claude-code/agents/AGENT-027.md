# AGENT-027 — `integrations/calendar`

**Branch Name:** `feature/calendar-integration`

**Role:** Build calendar integration for scheduling and meeting context.

**Responsibilities:**
- Create calendar service in `/backend/app/integrations/calendar/`
- Support providers:
  - Google Calendar
  - Microsoft Outlook/365
- Implement:
  - OAuth2 calendar connection
  - Meeting list retrieval
  - Meeting details (attendees, agenda)
  - Link meetings to transcripts
  - Upcoming meetings dashboard widget

**Files/Folders Touched:**
- `/backend/app/integrations/calendar/*`
- `/backend/app/api/calendar.py`
- `/backend/app/models/calendar.py`
- `/frontend/components/calendar/*`

**Dependencies:** AGENT-002, AGENT-012

**Acceptance Criteria:**
- Google Calendar OAuth works
- Outlook OAuth works
- Meetings sync correctly
- Transcript-meeting linking accurate
- Calendar widget shows upcoming calls
