# AGENT-006 — `workflow/content-generator`

**Branch Name:** `feature/content-generator`

**Role:** Build the content generation engine for Workflow 2 (Content Generator).

**Responsibilities:**
- Create content generator service in `/backend/app/services/content/`
- Support content types:
  - Sales decks (pitch, renewal, QBR)
  - Proposals (custom, templated)
  - One-pagers (product, solution, case study)
  - Battlecards (competitive, objection handling)
- Accept inputs: content type, goal, product info, audience
- Use Claude API for intelligent content generation
- Output structured content ready for rendering
- Maintain brand voice and WbD alignment

**Files/Folders Touched:**
- `/backend/app/services/content/*`
- `/backend/app/models/content.py`
- `/backend/app/api/content.py`
- `/claude/prompts/content_generation.md`
- `/data/templates/` (content templates)

**Dependencies:** AGENT-002

**Acceptance Criteria:**
- Generates all 4 content types
- Accepts customization parameters
- Returns structured JSON for rendering
- Content is professional and WbD-aligned
- Supports product info injection
