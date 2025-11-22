# AGENT-036 — `integrations/linkedin`

**Branch Name:** `feature/linkedin-integration`

**Role:** Build LinkedIn integration for prospect research and outreach tracking.

**Responsibilities:**
- Create LinkedIn service in `/backend/app/integrations/linkedin/`
- Implement:
  - Profile data enrichment
  - Company page data extraction
  - Connection status tracking
  - Activity monitoring (posts, engagement)
- Features:
  - LinkedIn URL parsing
  - Profile-to-prospect matching
  - Outreach tracking (InMail, connection requests)
  - Sales Navigator integration (if available)

**Files/Folders Touched:**
- `/backend/app/integrations/linkedin/*`
- `/backend/app/api/linkedin.py`
- `/backend/app/models/linkedin.py`
- `/frontend/components/linkedin/*`

**Dependencies:** AGENT-002, AGENT-007, AGENT-012

**Acceptance Criteria:**
- Profile enrichment returns accurate data
- Company data extracted correctly
- Outreach activities tracked
- Rate limits handled gracefully
- Privacy-compliant implementation
