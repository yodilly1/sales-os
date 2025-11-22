# AGENT-023 — `backend/file-upload`

**Branch Name:** `feature/file-upload-service`

**Role:** Build the file upload service for transcripts, CSVs, and assets.

**Responsibilities:**
- Create file service in `/backend/app/services/files/`
- Implement:
  - Chunked file uploads for large files
  - File type validation (transcripts, CSV, images)
  - Secure file storage (S3 compatible)
  - File processing queue
  - Temporary file cleanup
- Support formats:
  - Transcripts: .txt, .vtt, .srt, .json
  - Data: .csv, .xlsx
  - Assets: .png, .jpg, .pdf

**Files/Folders Touched:**
- `/backend/app/services/files/*`
- `/backend/app/api/files.py`
- `/backend/app/models/file.py`
- `/backend/app/core/storage.py`

**Dependencies:** AGENT-002, AGENT-011

**Acceptance Criteria:**
- Large files upload without timeout
- Invalid files rejected with clear errors
- Files stored securely with access control
- Processing queue handles backlog
- Cleanup removes orphaned files
