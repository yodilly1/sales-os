# AGENT-003 — `frontend/scaffold`

**Branch Name:** `feature/frontend-scaffold`

**Role:** Set up the frontend scaffold with Next.js, TypeScript, and Tailwind CSS.

**Responsibilities:**
- Initialize Next.js 14+ app in `/frontend` with App Router
- Configure TypeScript
- Set up Tailwind CSS with elegant, professional theme
- Create folder structure:
  - `/frontend/app/` - App router pages
  - `/frontend/components/` - Reusable UI components
  - `/frontend/lib/` - Utilities and helpers
  - `/frontend/styles/` - Global styles
- Add placeholder landing page with Sales OS branding
- Configure `.env.local.example`

**Files/Folders Touched:**
- `/frontend/*`

**Dependencies:** AGENT-001

**Acceptance Criteria:**
- `npm run dev` starts without error
- Landing page renders with Sales OS branding
- Tailwind styles apply correctly
