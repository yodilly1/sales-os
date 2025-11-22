# AGENT-029 — `frontend/analytics`

**Branch Name:** `feature/analytics-dashboard`

**Role:** Build comprehensive analytics dashboard for sales performance insights.

**Responsibilities:**
- Create analytics pages in `/frontend/app/analytics/`
- Implement dashboards:
  - Call analytics (volume, duration, SPICED scores)
  - Content analytics (generated, downloaded, shared)
  - Pipeline analytics (prospects enriched, converted)
  - Team performance (leaderboards, trends)
- Add visualizations:
  - Line charts (trends over time)
  - Bar charts (comparisons)
  - Pie charts (distributions)
  - Data tables (detailed breakdowns)

**Files/Folders Touched:**
- `/frontend/app/analytics/*`
- `/frontend/components/analytics/*`
- `/frontend/components/charts/*`
- `/frontend/lib/api/analytics.ts`
- `/backend/app/api/analytics.py`

**Dependencies:** AGENT-003, AGENT-011, AGENT-018

**Acceptance Criteria:**
- All dashboards load performantly
- Charts render correctly with real data
- Date range filtering works
- Export to CSV/PDF available
- Mobile-responsive layouts
