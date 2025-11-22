# AGENT-024 — `backend/search`

**Branch Name:** `feature/search-filtering`

**Role:** Build global search and advanced filtering across all entities.

**Responsibilities:**
- Create search service in `/backend/app/services/search/`
- Implement:
  - Full-text search across transcripts, content, prospects
  - Faceted filtering (date, type, status, tags)
  - Search suggestions and autocomplete
  - Recent searches history
  - Saved search queries
- Index entities:
  - Calls/Transcripts
  - Generated content
  - Prospects/Companies
  - Coaching reports

**Files/Folders Touched:**
- `/backend/app/services/search/*`
- `/backend/app/api/search.py`
- `/backend/app/models/search.py`
- `/frontend/components/search/*`

**Dependencies:** AGENT-002, AGENT-011

**Acceptance Criteria:**
- Search returns relevant results quickly (<500ms)
- Filters work correctly in combination
- Autocomplete suggests useful completions
- Search history persists per user
- Results properly paginated
