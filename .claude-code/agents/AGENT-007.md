# AGENT-007 — `workflow/prospect-enrichment`

**Branch Name:** `feature/prospect-enrichment`

**Role:** Build the prospect research and enrichment service for Workflow 3.

**Responsibilities:**
- Create enrichment service in `/backend/app/services/enrichment/`
- Accept inputs:
  - Individual: name, title, company, email
  - Bulk: event attendee lists, CSV imports
- Gather and verify:
  - Contact information validation
  - Company data (size, industry, funding, tech stack)
  - LinkedIn profile insights
  - Recent news and events
- Map enriched data to CRM fields
- Support batch processing for event lists

**Files/Folders Touched:**
- `/backend/app/services/enrichment/*`
- `/backend/app/models/prospect.py`
- `/backend/app/models/company.py`
- `/backend/app/api/enrichment.py`

**Dependencies:** AGENT-002, AGENT-004

**Acceptance Criteria:**
- Enriches individual prospects
- Processes bulk CSV/event lists
- Returns verified, structured data
- Maps to HubSpot contact fields
- Handles rate limits gracefully
