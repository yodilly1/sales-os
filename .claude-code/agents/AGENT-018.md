# AGENT-018 — `frontend/dashboard`

**Branch Name:** `feature/frontend-dashboard`

**Role:** Build the main dashboard and navigation for Sales OS.

**Responsibilities:**
- Create main dashboard in `/frontend/app/dashboard/`
- Implement:
  - Overview metrics (calls processed, content generated, prospects enriched)
  - Recent activity feed
  - Quick action buttons
  - Navigation sidebar
  - User settings dropdown
- Add components:
  - Sidebar - main navigation
  - MetricCard - KPI display
  - ActivityFeed - recent actions
  - QuickActions - workflow shortcuts

**Files/Folders Touched:**
- `/frontend/app/dashboard/*`
- `/frontend/app/layout.tsx`
- `/frontend/components/dashboard/*`
- `/frontend/components/layout/*`

**Dependencies:** AGENT-003, AGENT-012

**Acceptance Criteria:**
- Dashboard loads quickly
- Metrics update in real-time
- Navigation is intuitive
- Responsive on all screen sizes
- Branded and polished appearance
