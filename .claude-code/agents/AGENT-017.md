# AGENT-017 — `claude/prompts-infrastructure`

**Branch Name:** `feature/claude-prompts`

**Role:** Set up Claude AI prompt templates and infrastructure.

**Responsibilities:**
- Create prompt management system in `/claude/`
- Define prompt templates:
  - `/claude/prompts/spiced_extraction.md` - Extract SPICED from transcripts
  - `/claude/prompts/spiced_coaching.md` - Generate coaching feedback
  - `/claude/prompts/content_generation.md` - Content creation prompts
  - `/claude/prompts/prospect_enrichment.md` - Research prompts
- Add prompt versioning system
- Create prompt testing utilities
- Document prompt engineering guidelines

**Files/Folders Touched:**
- `/claude/prompts/*`
- `/claude/lib/*`
- `/claude/tests/*`
- `/backend/app/services/claude_client.py`

**Dependencies:** AGENT-002

**Acceptance Criteria:**
- All core prompts defined and documented
- Prompts produce consistent, quality output
- Version control for prompt iterations
- Test suite validates prompt behavior
- Easy to add/modify prompts
