# AGENT-015 — `frontend/prospect-ui`

**Branch Name:** `feature/frontend-prospect-ui`

**Role:** Build the frontend UI for prospect research and enrichment.

**Responsibilities:**
- Create prospect pages in `/frontend/app/prospects/`
- Implement:
  - Single prospect lookup form
  - Bulk upload (CSV, event list)
  - Enrichment progress tracker
  - Results table with sorting/filtering
  - CRM sync status indicators
- Add components:
  - ProspectCard - enriched profile view
  - CompanyCard - company insights
  - BulkUploader - CSV/list handler
  - EnrichmentQueue - batch status

**Files/Folders Touched:**
- `/frontend/app/prospects/*`
- `/frontend/components/prospects/*`
- `/frontend/lib/api/enrichment.ts`

**Dependencies:** AGENT-003, AGENT-007

**Acceptance Criteria:**
- Single lookup returns results quickly
- Bulk upload handles large files
- Progress tracking is accurate
- Results can be exported
- CRM sync works reliably
