# AGENT-014 — `frontend/content-ui`

**Branch Name:** `feature/frontend-content-ui`

**Role:** Build the frontend UI for content generation workflow.

**Responsibilities:**
- Create content pages in `/frontend/app/content/`
- Implement:
  - Content type selector (deck, proposal, one-pager, battlecard)
  - Input form for goal, product info, audience
  - Generation progress indicator
  - Preview panel with live updates
  - Export options (PDF, PPTX, link)
- Add components:
  - ContentForm - input wizard
  - ContentPreview - live preview
  - ExportMenu - download/share options

**Files/Folders Touched:**
- `/frontend/app/content/*`
- `/frontend/components/content/*`
- `/frontend/lib/api/content.ts`

**Dependencies:** AGENT-003, AGENT-006, AGENT-008

**Acceptance Criteria:**
- Content type selection is intuitive
- Form captures all needed inputs
- Preview updates in real-time
- Export produces quality output
- Brand styling consistent throughout
