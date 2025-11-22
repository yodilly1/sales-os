# AGENT-040 — `integrations/gong`

**Branch Name:** `feature/gong-integration`

**Role:** Build Gong integration as alternative conversation intelligence source.

**Responsibilities:**
- Create Gong client in `/backend/app/integrations/gong/`
- Implement:
  - API authentication
  - Call list retrieval
  - Transcript extraction
  - Call metadata and participants
  - Gong insights import (optional)
- Sync features:
  - Scheduled sync of new calls
  - Historical import
  - Deduplication with other sources

**Files/Folders Touched:**
- `/backend/app/integrations/gong/*`
- `/backend/app/api/gong.py`
- `/backend/app/models/gong.py`
- `/frontend/app/settings/integrations/gong/*`

**Dependencies:** AGENT-002, AGENT-005, AGENT-012

**Acceptance Criteria:**
- Gong API authentication works
- Calls and transcripts import correctly
- Metadata preserved accurately
- Sync handles incremental updates
- No duplicate processing of calls
