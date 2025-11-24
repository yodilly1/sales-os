# AGENT-MVP-001 — `phase1/transcript-flow`

**Branch Name:** `phase1/transcript-flow`

**Role:** Make the complete transcript → SPICED analysis flow work end-to-end.

**End Goal:** User can upload a transcript and see SPICED analysis results in the UI.

---

## What Must Work When Done

1. User navigates to `/transcript` page
2. User pastes or uploads transcript text
3. Backend parses transcript and runs SPICED extraction via Claude
4. Frontend displays the SPICED analysis (Situation, Pain, Impact, Critical Event, Decision)
5. Follow-up tasks are generated and displayed
6. No mock data - real Claude API calls

---

## Responsibilities

### Backend
1. Wire `transcript` router in `backend/app/api/__init__.py`
2. Fix any import errors in `backend/app/api/transcript.py`
3. Verify `TranscriptParser` and `SPICEDExtractor` services work
4. Ensure `claude_client.py` is configured with API key from env
5. Test endpoint manually: `POST /api/v1/transcript/parse`

### Frontend
1. Update `frontend/lib/api/transcript.ts` to call real backend
2. Update `frontend/app/transcript/page.tsx` to use real API (remove mock)
3. Ensure SPICED results display correctly in UI
4. Handle loading states and errors gracefully

### Integration
1. Test full flow: paste transcript → see analysis
2. Verify Claude API is called (check logs)
3. Confirm no hardcoded/mock data remains

---

## Files/Folders Touched

**Backend:**
- `/backend/app/api/__init__.py` - add transcript router
- `/backend/app/api/transcript.py` - verify/fix imports
- `/backend/app/services/transcript/__init__.py` - verify exports
- `/backend/app/services/transcript/parser.py` - verify works
- `/backend/app/services/transcript/spiced_extractor.py` - verify works
- `/backend/app/services/claude_client.py` - verify config
- `/backend/app/core/config.py` - ensure ANTHROPIC_API_KEY loaded

**Frontend:**
- `/frontend/lib/api/transcript.ts` - update to real endpoints
- `/frontend/app/transcript/page.tsx` - remove mock, use real API
- `/frontend/components/transcript/` - verify components work

---

## Environment Required

```bash
ANTHROPIC_API_KEY=sk-ant-xxx  # Required for SPICED extraction
```

---

## Test Script

```bash
# 1. Start the system
docker-compose up --build -d

# 2. Wait for services
sleep 15

# 3. Test backend endpoint directly
curl -X POST http://localhost:8000/api/v1/transcript/parse \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "Sales Rep: Hi, thanks for meeting today. Tell me about your current billing challenges.\nProspect: We spend 20 hours a month on manual reconciliation. Its killing our team.",
    "company_name": "Acme Corp",
    "generate_tasks": true
  }'

# 4. Verify response has SPICED analysis
# Should see: situation, pain, impact, critical_event, decision fields

# 5. Test frontend
# Open http://localhost:3000/transcript
# Paste the same transcript
# Click analyze
# Verify SPICED results appear
```

---

## Dependencies

- None (first agent in Phase 1)

---

## Acceptance Criteria

- [ ] Backend starts without import errors
- [ ] `POST /api/v1/transcript/parse` returns SPICED analysis (not 500 error)
- [ ] Claude API is actually called (visible in logs or response time >1s)
- [ ] Frontend transcript page loads without errors
- [ ] Pasting transcript and clicking analyze shows real SPICED results
- [ ] Follow-up tasks are generated and displayed
- [ ] No mock data or `generateMock*` functions in the flow
