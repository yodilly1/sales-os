# AGENT-033 — `workflow/deal-room`

**Branch Name:** `feature/deal-room`

**Role:** Build digital deal rooms for sharing content with prospects.

**Responsibilities:**
- Create deal room service in `/backend/app/services/dealroom/`
- Implement:
  - Branded shareable links
  - Content organization (folders, sections)
  - Viewer analytics (who viewed what, when)
  - Access controls (password, expiry)
  - Mutual action plans
- Deal room contents:
  - Proposals and decks
  - Case studies
  - Pricing information
  - Contract documents

**Files/Folders Touched:**
- `/backend/app/services/dealroom/*`
- `/backend/app/api/dealroom.py`
- `/backend/app/models/dealroom.py`
- `/frontend/app/dealroom/*`
- `/frontend/app/[room_slug]/*` (public view)

**Dependencies:** AGENT-002, AGENT-008, AGENT-012

**Acceptance Criteria:**
- Deal rooms create with unique URLs
- Branding applies correctly
- Analytics track all views accurately
- Access controls enforced
- Mobile-friendly viewing experience
