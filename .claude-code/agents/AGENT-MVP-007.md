# AGENT-MVP-007 — `phase2/orchestrator`

**Branch Name:** `main` (merge target)

**Role:** Merge Phase 2 branches, verify enhanced enrichment and outreach work.

**End Goal:** Enrichment includes real web data, outreach campaigns can be generated and exported.

---

## What Must Work When Done

After merging Phase 2 branches:

1. **Enhanced Enrichment**: Lookup shows web research + AI insights (from MVP-005)
2. **Outreach Campaigns**: Generate and download Instantly/HeyReach CSVs (from MVP-006)
3. **Phase 1 Features**: Still work (transcript, basic enrichment, content)
4. All features work together seamlessly

---

## Merge Order

```bash
# 1. Ensure on main and up to date
git checkout main
git pull origin main

# 2. Merge MVP-005 (web research)
git fetch origin
git merge origin/phase2/smashmouth-web-research --no-ff -m "merge: phase2/smashmouth-web-research (MVP-005)"

# 3. Merge MVP-006 (outreach campaigns)
git merge origin/phase2/outreach-campaigns --no-ff -m "merge: phase2/outreach-campaigns (MVP-006)"
```

---

## Conflict Resolution

### `backend/app/services/enrichment/service.py`
- Keep all existing providers
- Add web research provider registration
- Ensure provider initialization order is correct

### `backend/app/api/__init__.py`
- Add outreach router
- Keep all existing routers

### `backend/app/core/config.py`
- Add SERPER_API_KEY setting
- Keep all existing settings

---

## Post-Merge Validation

```bash
# 1. Rebuild
docker-compose down -v
docker-compose up --build -d
sleep 20

# 2. Test Phase 1 features still work
curl http://localhost:8000/api/v1/transcript/parse \
  -H "Content-Type: application/json" \
  -d '{"transcript_text": "Test transcript", "company_name": "Test"}'

curl http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"content_type": "deck_pitch", "goal": "Test", "product_info": {"name": "Test"}}'

# 3. Test enhanced enrichment
curl http://localhost:8000/api/v1/enrichment/lookup \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Stripe", "include_web_research": true}'
# Should include web_research and ai_insights fields

# 4. Test outreach generation
curl -X POST http://localhost:8000/api/v1/outreach/generate \
  -H "Content-Type: application/json" \
  -d '{"prospect_email": "test@stripe.com", "prospect_name": "Test User", "prospect_title": "VP Finance", "company_name": "Stripe"}'

# 5. Test CSV export (use campaign_id from step 4)
curl http://localhost:8000/api/v1/outreach/export/instantly/{campaign_id}

# 6. Frontend tests
# - /transcript still works
# - /content still works
# - /prospects shows web research data
# - /prospects has outreach generation button
```

---

## Final Commit

```bash
git add .
git commit -m "$(cat <<'EOF'
Phase 2 Complete: Enhanced Enrichment & Outreach

New Features:
- Web research via Serper API (Google search)
- AI-powered company analysis
- Outreach campaign generation
- Instantly CSV export
- HeyReach CSV export

Enhancements:
- Enrichment now includes real-time web data
- AI insights for revenue model, funding, key findings
- Personalized email/LinkedIn sequences

All Phase 1 features remain operational.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push origin main
```

---

## Dependencies

- AGENT-MVP-005 complete
- AGENT-MVP-006 complete

---

## Acceptance Criteria

- [ ] Both branches merged cleanly
- [ ] Docker compose starts all services
- [ ] Phase 1 features still work (transcript, content, basic enrichment)
- [ ] Enrichment includes web research data when `include_web_research=true`
- [ ] Outreach campaign generation works
- [ ] Instantly CSV downloads correctly
- [ ] HeyReach CSV downloads correctly
- [ ] Frontend shows new features
- [ ] Changes pushed to GitHub
