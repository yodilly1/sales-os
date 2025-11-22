# AGENT-030 — `backend/export-import`

**Branch Name:** `feature/export-import`

**Role:** Build data export and import service for portability and backups.

**Responsibilities:**
- Create export service in `/backend/app/services/export/`
- Implement exports:
  - Transcript data + SPICED analysis (JSON, CSV)
  - Generated content (ZIP with all formats)
  - Prospect lists (CSV, HubSpot format)
  - Coaching reports (PDF, CSV)
  - Full account backup (JSON archive)
- Implement imports:
  - Prospect CSV import with mapping
  - Transcript bulk import
  - Template import

**Files/Folders Touched:**
- `/backend/app/services/export/*`
- `/backend/app/services/import/*`
- `/backend/app/api/export.py`
- `/backend/app/api/import.py`

**Dependencies:** AGENT-002, AGENT-011, AGENT-023

**Acceptance Criteria:**
- Exports generate correct formats
- Large exports handled async with progress
- Imports validate data before processing
- Import errors reported clearly
- Backup/restore works reliably
