# AGENT-013 — `frontend/transcript-ui`

**Branch Name:** `feature/frontend-transcript-ui`

**Role:** Build the frontend UI for transcript upload and SPICED analysis display.

**Responsibilities:**
- Create transcript pages in `/frontend/app/transcript/`
- Implement:
  - Transcript upload (file, paste, Avoma sync)
  - Processing status indicator
  - SPICED analysis display with visual scoring
  - Call notes viewer/editor
  - CRM push confirmation
- Add components:
  - SPICEDCard - displays each element
  - TranscriptViewer - formatted transcript
  - TaskList - suggested follow-ups

**Files/Folders Touched:**
- `/frontend/app/transcript/*`
- `/frontend/components/transcript/*`
- `/frontend/components/spiced/*`
- `/frontend/lib/api/transcript.ts`

**Dependencies:** AGENT-003, AGENT-005

**Acceptance Criteria:**
- Upload flow works smoothly
- SPICED results display clearly
- Call notes are editable
- Push to CRM button functional
- Responsive on all devices
