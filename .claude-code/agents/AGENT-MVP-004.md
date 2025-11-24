# AGENT-MVP-004 — `phase1/orchestrator`

**Branch Name:** `main` (merge target)

**Role:** Merge Phase 1 branches, resolve conflicts, verify everything works together.

**End Goal:** All three Phase 1 flows work together in a single deployed system.

---

## What Must Work When Done

After merging all Phase 1 branches:

1. **Transcript Flow**: Upload → SPICED analysis → tasks (from MVP-001)
2. **Enrichment Flow**: Lookup prospect → see enriched data (from MVP-002)
3. **Content Flow**: Generate deck → see/download output (from MVP-003)
4. All three features work without interfering with each other
5. Single `docker-compose up` runs everything

---

## Merge Order

```bash
# 1. Ensure on main and up to date
git checkout main
git pull origin main

# 2. Merge MVP-001 (transcript flow)
git fetch origin
git merge origin/phase1/transcript-flow --no-ff -m "merge: phase1/transcript-flow (MVP-001)"

# 3. Merge MVP-002 (enrichment flow)
git merge origin/phase1/enrichment-flow --no-ff -m "merge: phase1/enrichment-flow (MVP-002)"

# 4. Merge MVP-003 (content flow)
git merge origin/phase1/content-flow --no-ff -m "merge: phase1/content-flow (MVP-003)"
```

---

## Conflict Resolution Rules

### `backend/app/api/__init__.py`
- Keep ALL router registrations from all branches
- Ensure no duplicate imports
- Final file should have: transcript, enrichment, content routers (plus existing ones)

### `frontend/lib/api/` files
- Each branch owns its own file, no conflicts expected
- If `index.ts` conflicts, combine all exports

### `package.json` / `requirements.txt`
- Union of all dependencies
- Use latest version if conflicts

---

## Post-Merge Validation

```bash
# 1. Rebuild and start
docker-compose down -v
docker-compose up --build -d

# 2. Wait for startup
sleep 20

# 3. Health check
curl http://localhost:8000/health

# 4. Test Transcript Flow
curl -X POST http://localhost:8000/api/v1/transcript/parse \
  -H "Content-Type: application/json" \
  -d '{"transcript_text": "Rep: What challenges do you face?\nProspect: Manual billing takes forever.", "company_name": "Test"}'

# 5. Test Enrichment Flow
curl -X POST http://localhost:8000/api/v1/enrichment/lookup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "company_name": "Example Inc"}'

# 6. Test Content Flow
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"content_type": "deck_pitch", "goal": "Intro pitch", "product_info": {"name": "Test"}}'

# 7. Test Frontend
# Open http://localhost:3000
# Navigate to /transcript - should work
# Navigate to /prospects - should work
# Navigate to /content - should work
```

---

## Fix Common Issues

### Import Errors
```python
# If router import fails, check the file has:
router = APIRouter()
# at module level, not inside a function
```

### Multiple Routers Same Prefix
```python
# If route conflict, namespace them:
api_router.include_router(transcript_router, prefix="/transcript", tags=["Transcript"])
api_router.include_router(enrichment_router, prefix="/enrichment", tags=["Enrichment"])
```

### Frontend Build Errors
```bash
# If TypeScript errors, check for:
# - Missing type imports
# - Unused variables
# Run: cd frontend && npm run type-check
```

---

## Final Commit

```bash
git add .
git commit -m "$(cat <<'EOF'
Phase 1 Complete: Core Workflows Operational

Working Features:
- Transcript upload → SPICED analysis → follow-up tasks
- Prospect enrichment → company/contact data display
- Content generation → deck/proposal output

All features connected to real APIs (no mock data).
Tested end-to-end with Claude API integration.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push origin main
```

---

## Dependencies

- AGENT-MVP-001 complete
- AGENT-MVP-002 complete
- AGENT-MVP-003 complete

---

## Acceptance Criteria

- [ ] All three branches merged without errors
- [ ] Docker compose starts all services
- [ ] `/api/v1/transcript/parse` works
- [ ] `/api/v1/enrichment/lookup` works
- [ ] `/api/v1/content/generate` works
- [ ] Frontend pages load: /transcript, /prospects, /content
- [ ] Each feature works independently
- [ ] No regressions in health check or auth
- [ ] Changes pushed to GitHub
