# AGENT-039 — `integrations/zoom`

**Branch Name:** `feature/zoom-integration`

**Role:** Build Zoom integration for recording and transcript ingestion.

**Responsibilities:**
- Create Zoom service in `/backend/app/integrations/zoom/`
- Implement:
  - OAuth2 app connection
  - Recording list retrieval
  - Transcript download (VTT/SRT)
  - Meeting metadata extraction
  - Webhook for new recordings
- Auto-processing:
  - New recording → download transcript → SPICED analysis

**Files/Folders Touched:**
- `/backend/app/integrations/zoom/*`
- `/backend/app/api/zoom.py`
- `/backend/app/api/webhooks.py`
- `/backend/app/models/zoom.py`

**Dependencies:** AGENT-002, AGENT-005, AGENT-012

**Acceptance Criteria:**
- Zoom OAuth connects accounts
- Recordings listed correctly
- Transcripts download and parse
- Webhooks trigger processing pipeline
- Handles cloud vs local recordings
