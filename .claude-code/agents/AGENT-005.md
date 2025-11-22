# AGENT-005 — `workflow/transcript-spiced`

**Branch Name:** `feature/transcript-spiced-parser`

**Role:** Build the transcript parser and SPICED field extractor for Workflow 1 (Transcript → CRM).

**Responsibilities:**
- Create transcript parser in `/backend/app/services/transcript/`
- Implement SPICED methodology extraction:
  - **S**ituation - Current state, context
  - **P**ain - Problems, challenges, frustrations
  - **I**mpact - Business impact, consequences
  - **C**ritical Event - Timeline drivers, urgency
  - **E**xpected Decision - Decision process, criteria
  - **D**ecision Criteria - How they'll evaluate solutions
- Use Claude API for intelligent extraction
- Generate structured call notes
- Create CRM-ready task recommendations

**Files/Folders Touched:**
- `/backend/app/services/transcript/*`
- `/backend/app/models/spiced.py`
- `/backend/app/models/transcript.py`
- `/backend/app/api/transcript.py`
- `/claude/prompts/spiced_extraction.md`

**Dependencies:** AGENT-002

**Acceptance Criteria:**
- Accepts raw transcript text input
- Returns structured SPICED JSON
- Generates formatted call note
- Suggests follow-up tasks
- Handles various transcript formats (Zoom, Teams, Avoma)
