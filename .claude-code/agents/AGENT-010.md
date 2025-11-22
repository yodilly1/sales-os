# AGENT-010 — `coaching/spiced-coach`

**Branch Name:** `feature/spiced-coaching`

**Role:** Build the SPICED coaching module aligned with Winning by Design methodology.

**Responsibilities:**
- Create coaching service in `/backend/app/services/coaching/`
- Analyze calls against SPICED framework:
  - Score each SPICED element (1-5)
  - Identify gaps and missed opportunities
  - Suggest specific improvements
  - Provide WbD-aligned coaching tips
- Generate coaching reports:
  - Per-call feedback
  - Trend analysis over time
  - Team benchmarking
- Include WbD best practices and talk tracks

**Files/Folders Touched:**
- `/backend/app/services/coaching/*`
- `/backend/app/models/coaching.py`
- `/backend/app/api/coaching.py`
- `/claude/prompts/spiced_coaching.md`
- `/data/reference/wbd_methodology.md`

**Dependencies:** AGENT-002, AGENT-005

**Acceptance Criteria:**
- Scores calls on SPICED elements
- Provides actionable coaching feedback
- Aligns with WbD methodology
- Generates trend reports
- Feedback is specific and constructive
