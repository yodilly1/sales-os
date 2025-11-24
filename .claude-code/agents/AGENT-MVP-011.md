# AGENT-MVP-011 — `phase3/orchestrator`

**Branch Name:** `main` (merge target)

**Role:** Merge Phase 3 branches, verify all content generation enhancements work.

**End Goal:** Content generation produces professional output with financial models, beautiful HTML, and contracts.

---

## What Must Work When Done

After merging Phase 3 branches:

1. **Financial Models**: Proposals include calculated ROI/payback (from MVP-008)
2. **HTML Templates**: Content renders as beautiful HTML (from MVP-009)
3. **Contract Generation**: Can generate SaaS contracts (from MVP-010)
4. **All Previous Features**: Phase 1 & 2 features still work

---

## Merge Order

```bash
# 1. Ensure on main and up to date
git checkout main
git pull origin main

# 2. Merge MVP-008 (financial models)
git fetch origin
git merge origin/phase3/financial-models --no-ff -m "merge: phase3/financial-models (MVP-008)"

# 3. Merge MVP-009 (HTML templates)
git merge origin/phase3/html-templates --no-ff -m "merge: phase3/html-templates (MVP-009)"

# 4. Merge MVP-010 (contract generation)
git merge origin/phase3/contract-generation --no-ff -m "merge: phase3/contract-generation (MVP-010)"
```

---

## Conflict Resolution

### `backend/app/services/content/generator.py`
- Keep all generation methods (_generate_deck, _generate_proposal, _generate_contract)
- Integrate financial models into proposal generation
- Integrate HTML rendering

### `backend/app/models/content.py`
- Keep all schemas (FinancialInputs, ContractInputs, etc.)
- Ensure no duplicate field names

### `backend/app/core/constants.py`
- Add CONTRACT to ContentType enum
- Keep all existing types

### `frontend/app/content/page.tsx`
- Combine all form enhancements
- Keep financial inputs, contract inputs, HTML preview

---

## Post-Merge Validation

```bash
# 1. Rebuild
docker-compose down -v
docker-compose up --build -d
sleep 20

# 2. Test Phase 1 features
curl http://localhost:8000/api/v1/transcript/parse \
  -H "Content-Type: application/json" \
  -d '{"transcript_text": "Test", "company_name": "Test"}'

# 3. Test Phase 2 features
curl http://localhost:8000/api/v1/enrichment/lookup \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Stripe", "include_web_research": true}'

# 4. Test financial models in proposal
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "proposal",
    "goal": "Test proposal",
    "product_info": {"name": "Test"},
    "financial_inputs": {"arr": 10000000, "current_dso": 45, "target_dso": 30, "monthly_price": 5000}
  }'
# Should include financial_analysis in response

# 5. Test HTML rendering
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"content_type": "deck_pitch", "goal": "Test", "product_info": {"name": "Test"}, "render_html": true}'
# Should include html field in response

# 6. Test contract generation
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "contract",
    "contract_inputs": {"customer_name": "Test Corp", "customer_contact_name": "Test", "customer_contact_email": "test@test.com", "year1_price": 10000, "year2_price": 20000}
  }'
# Should include contract_markdown in response

# 7. Frontend tests
# - /content page loads
# - Can select all content types including Contract
# - Financial inputs show for proposals
# - HTML preview works
# - Download buttons work
```

---

## Final Commit

```bash
git add .
git commit -m "$(cat <<'EOF'
Phase 3 Complete: Enhanced Content Generation

New Features:
- Financial ROI models (DSO, labor savings, revenue leakage)
- Beautiful HTML templates with animations
- Contract/agreement generation

Enhancements:
- Proposals include calculated ROI and payback
- All content types render as professional HTML
- Glass-morphism styling, animated backgrounds
- Contracts use your proven template structure

All Phase 1 & 2 features remain operational.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push origin main
```

---

## Dependencies

- AGENT-MVP-008 complete
- AGENT-MVP-009 complete
- AGENT-MVP-010 complete

---

## Acceptance Criteria

- [ ] All three branches merged cleanly
- [ ] Docker compose starts all services
- [ ] Transcript flow works (Phase 1)
- [ ] Enrichment with web research works (Phase 2)
- [ ] Outreach export works (Phase 2)
- [ ] Proposals include financial analysis
- [ ] Content renders as beautiful HTML
- [ ] Contract generation works
- [ ] Frontend shows all enhancements
- [ ] Changes pushed to GitHub
