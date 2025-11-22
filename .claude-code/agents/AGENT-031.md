# AGENT-031 — `workflow/battlecard-engine`

**Branch Name:** `feature/battlecard-engine`

**Role:** Build specialized battlecard generation engine for competitive intelligence.

**Responsibilities:**
- Create battlecard service in `/backend/app/services/battlecards/`
- Implement battlecard types:
  - Competitive battlecards (vs specific competitors)
  - Objection handling cards
  - Feature comparison matrices
  - Win/loss analysis cards
- Features:
  - Competitor database management
  - Auto-update from win/loss data
  - Version history
  - Team sharing and favorites

**Files/Folders Touched:**
- `/backend/app/services/battlecards/*`
- `/backend/app/api/battlecards.py`
- `/backend/app/models/battlecard.py`
- `/data/reference/competitors/*`
- `/frontend/app/battlecards/*`

**Dependencies:** AGENT-002, AGENT-006, AGENT-011

**Acceptance Criteria:**
- All battlecard types generate correctly
- Competitor data maintained accurately
- Cards update based on new intelligence
- Easy to share across team
- Print-friendly format
