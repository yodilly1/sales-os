# AGENT-MVP-003 — `phase1/content-flow`

**Branch Name:** `phase1/content-flow`

**Role:** Make the complete content generation flow work end-to-end.

**End Goal:** User can generate a sales deck/proposal and see/download the actual output.

---

## What Must Work When Done

1. User navigates to `/content` page
2. User fills out content generation form (type, goal, product info, audience)
3. Backend generates content via Claude API
4. Frontend displays the generated content (slides, sections, etc.)
5. User can download/export the content
6. No mock data - real Claude API calls

---

## Responsibilities

### Backend
1. Wire `content` router in `backend/app/api/__init__.py`
2. Fix any import errors in `backend/app/api/content.py`
3. Verify `ContentGenerator` service works with Claude
4. Verify `ContentPromptBuilder` generates proper prompts
5. Test endpoint: `POST /api/v1/content/generate`

### Frontend
1. Update `frontend/lib/api/content.ts` to call real backend
2. Update `frontend/app/content/page.tsx` to use real API
3. **DELETE the `generateMockContent()` function entirely**
4. Display generated content properly (deck slides, proposal sections)
5. Add download/export functionality if not present

### Integration
1. Test generating a pitch deck
2. Test generating a proposal
3. Verify content is different each time (not cached/mock)

---

## Files/Folders Touched

**Backend:**
- `/backend/app/api/__init__.py` - add content router
- `/backend/app/api/content.py` - verify/fix imports
- `/backend/app/services/content/__init__.py` - verify exports
- `/backend/app/services/content/generator.py` - verify works
- `/backend/app/services/content/prompts.py` - verify prompts
- `/backend/app/services/claude_client.py` - already configured from MVP-001

**Frontend:**
- `/frontend/lib/api/content.ts` - update to real endpoints, remove mock
- `/frontend/app/content/page.tsx` - remove mock, use real API
- `/frontend/components/content/` - verify components work

---

## Environment Required

```bash
ANTHROPIC_API_KEY=sk-ant-xxx  # Required for content generation
```

---

## Test Script

```bash
# 1. Start the system
docker-compose up --build -d

# 2. Wait for services
sleep 15

# 3. Test backend endpoint
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "deck_pitch",
    "goal": "Introduce our billing automation platform",
    "product_info": {
      "name": "Vayu",
      "description": "Revenue operations platform for usage-based billing"
    },
    "audience": {
      "role": "VP Finance",
      "industry": "SaaS"
    }
  }'

# 4. Should return generated deck content with slides

# 5. Test frontend
# Open http://localhost:3000/content
# Select "Pitch Deck" type
# Fill in product info
# Click Generate
# Verify slides appear (takes 10-30 seconds for Claude)
```

---

## Dependencies

- AGENT-MVP-001 (Claude client already configured)

---

## Acceptance Criteria

- [ ] Backend starts without import errors
- [ ] `POST /api/v1/content/generate` returns generated content (not 500)
- [ ] Response contains actual slides/sections (not empty)
- [ ] Generation takes 5-30 seconds (proves Claude is called)
- [ ] Frontend content page loads without errors
- [ ] Form submission triggers real generation
- [ ] Generated content displays in UI
- [ ] **No `generateMockContent` or similar mock functions exist**
- [ ] Running generation twice produces different content
