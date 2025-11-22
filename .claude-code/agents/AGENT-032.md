# AGENT-032 — `workflow/talk-track-generator`

**Branch Name:** `feature/talk-track-generator`

**Role:** Build talk track and script generator aligned with WbD methodology.

**Responsibilities:**
- Create talk track service in `/backend/app/services/talktracks/`
- Generate scripts for:
  - Discovery calls (SPICED questions)
  - Demo scripts (value-focused)
  - Objection responses
  - Closing conversations
  - Follow-up call guides
- Features:
  - Persona-based customization
  - Industry-specific language
  - A/B script variants
  - Performance tracking by script

**Files/Folders Touched:**
- `/backend/app/services/talktracks/*`
- `/backend/app/api/talktracks.py`
- `/backend/app/models/talktrack.py`
- `/claude/prompts/talktrack_generation.md`
- `/frontend/app/talktracks/*`

**Dependencies:** AGENT-002, AGENT-010, AGENT-017

**Acceptance Criteria:**
- Scripts follow WbD methodology
- Customization produces relevant output
- Scripts are natural and conversational
- Can track which scripts perform best
- Easy to iterate and version
