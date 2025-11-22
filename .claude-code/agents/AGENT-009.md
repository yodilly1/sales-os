# AGENT-009 — `integrations/avoma`

**Branch Name:** `feature/avoma-integration`

**Role:** Build Avoma integration for automatic transcript ingestion.

**Responsibilities:**
- Create Avoma client in `/backend/app/integrations/avoma/`
- Implement methods:
  - `list_recordings()`
  - `get_transcript()`
  - `get_meeting_metadata()`
  - Webhook handler for new recordings
- Auto-trigger transcript processing pipeline
- Map Avoma metadata to internal models
- Handle authentication and token refresh

**Files/Folders Touched:**
- `/backend/app/integrations/avoma/*`
- `/backend/app/api/avoma.py`
- `/backend/app/api/webhooks.py`
- `/backend/app/models/avoma.py`

**Dependencies:** AGENT-002, AGENT-005

**Acceptance Criteria:**
- Connects to Avoma API successfully
- Retrieves transcripts automatically
- Webhook triggers SPICED extraction pipeline
- Meeting metadata captured correctly
- Handles API errors gracefully
