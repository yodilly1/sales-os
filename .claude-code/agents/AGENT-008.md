# AGENT-008 — `rendering/pdf-deck`

**Branch Name:** `feature/pdf-deck-renderer`

**Role:** Build the PDF and deck rendering engine for polished, branded output.

**Responsibilities:**
- Create rendering service in `/backend/app/services/rendering/`
- Implement renderers:
  - PDF generator (proposals, one-pagers)
  - Slide deck generator (pitch decks, QBR decks)
  - Web-based deck viewer (shareable links)
- Apply brand styling:
  - Professional typography
  - Consistent color palette
  - Logo placement
  - Elegant layouts
- Support export formats: PDF, PPTX, HTML

**Files/Folders Touched:**
- `/backend/app/services/rendering/*`
- `/backend/app/api/render.py`
- `/data/templates/styles/*`
- `/data/assets/` (logos, fonts)
- `/frontend/app/deck/` (web deck viewer)

**Dependencies:** AGENT-002, AGENT-003, AGENT-006

**Acceptance Criteria:**
- Generates professional PDFs from content JSON
- Creates slide decks with consistent branding
- Web deck viewer displays content elegantly
- Supports multiple export formats
- Output is print-ready quality
