# AGENT-016 — `frontend/coaching-ui`

**Branch Name:** `feature/frontend-coaching-ui`

**Role:** Build the frontend UI for SPICED coaching and analytics.

**Responsibilities:**
- Create coaching pages in `/frontend/app/coaching/`
- Implement:
  - Coaching dashboard with metrics
  - Per-call feedback viewer
  - SPICED score trends (charts)
  - Team leaderboard
  - Improvement recommendations
- Add components:
  - SPICEDRadar - radar chart for scores
  - TrendChart - performance over time
  - FeedbackPanel - coaching comments
  - WbDTips - methodology tips

**Files/Folders Touched:**
- `/frontend/app/coaching/*`
- `/frontend/components/coaching/*`
- `/frontend/lib/api/coaching.ts`

**Dependencies:** AGENT-003, AGENT-010

**Acceptance Criteria:**
- Dashboard shows key metrics at glance
- Charts render correctly
- Feedback is actionable and clear
- WbD methodology well-represented
- Mobile-responsive design
