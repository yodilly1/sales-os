# Sales OS MVP Build Plan

This document outlines how to execute the 13 MVP agents in order to transform Sales OS into a fully working system.

---

## Overview

The build is organized into 4 phases:

| Phase | Focus | Agents | Goal |
|-------|-------|--------|------|
| 1 | Core Flows | MVP-001 to MVP-004 | Basic transcript, enrichment, content flows working |
| 2 | Enhanced Features | MVP-005 to MVP-007 | Web research + outreach campaigns |
| 3 | Premium Features | MVP-008 to MVP-011 | Financial models + HTML templates + contracts |
| 4 | Polish | MVP-012 to MVP-013 | Analytics dashboard + final testing |

---

## Phase 1: Core Workflows

**Goal:** Get the three core flows working end-to-end with real APIs.

### Step 1.1: Transcript Flow (MVP-001)

```bash
git checkout -b phase1/transcript-flow
# Execute AGENT-MVP-001.md
# Test: Upload transcript → See SPICED analysis
git push origin phase1/transcript-flow
```

**Verify:**
- [ ] `POST /api/v1/transcript/parse` returns SPICED data
- [ ] Frontend shows analysis results
- [ ] Claude API is actually called (response time >1s)

### Step 1.2: Enrichment Flow (MVP-002)

```bash
git checkout -b phase1/enrichment-flow
# Execute AGENT-MVP-002.md
# Test: Enter email → See enriched data
git push origin phase1/enrichment-flow
```

**Verify:**
- [ ] `POST /api/v1/enrichment/lookup` returns data
- [ ] Frontend displays prospect info
- [ ] Works even without API keys (graceful fallback)

### Step 1.3: Content Flow (MVP-003)

```bash
git checkout -b phase1/content-flow
# Execute AGENT-MVP-003.md
# Test: Generate deck → See slides
git push origin phase1/content-flow
```

**Verify:**
- [ ] `POST /api/v1/content/generate` returns content
- [ ] Frontend shows generated slides/sections
- [ ] **No `generateMockContent()` function exists**

### Step 1.4: Phase 1 Merge (MVP-004)

```bash
git checkout main
git pull origin main
git merge origin/phase1/transcript-flow --no-ff
git merge origin/phase1/enrichment-flow --no-ff
git merge origin/phase1/content-flow --no-ff
# Resolve any conflicts
docker-compose down -v && docker-compose up --build -d
# Test all three flows work together
git push origin main
```

**Verify:**
- [ ] All three features work independently
- [ ] No import errors in backend
- [ ] No console errors in frontend

---

## Phase 2: Enhanced Features

**Goal:** Add real web research and outreach campaign generation.

### Step 2.1: Web Research (MVP-005)

```bash
git checkout main
git pull origin main
git checkout -b phase2/smashmouth-web-research
# Execute AGENT-MVP-005.md
# Port code from Smashmouth project
git push origin phase2/smashmouth-web-research
```

**Requires:** `SERPER_API_KEY` in `.env`

**Verify:**
- [ ] Enrichment includes web research data
- [ ] AI insights are generated
- [ ] Recent news/funding info appears

### Step 2.2: Outreach Campaigns (MVP-006)

```bash
git checkout main
git pull origin main
git checkout -b phase2/outreach-campaigns
# Execute AGENT-MVP-006.md
git push origin phase2/outreach-campaigns
```

**Verify:**
- [ ] Can generate campaign from prospect
- [ ] Instantly CSV downloads correctly
- [ ] HeyReach CSV downloads correctly
- [ ] Messages are personalized (not generic)

### Step 2.3: Phase 2 Merge (MVP-007)

```bash
git checkout main
git pull origin main
git merge origin/phase2/smashmouth-web-research --no-ff
git merge origin/phase2/outreach-campaigns --no-ff
docker-compose down -v && docker-compose up --build -d
git push origin main
```

**Verify:**
- [ ] Phase 1 features still work
- [ ] Web research enhances enrichment
- [ ] Outreach generation and export work

---

## Phase 3: Premium Features

**Goal:** Add financial ROI models, beautiful HTML output, and contract generation.

### Step 3.1: Financial Models (MVP-008)

```bash
git checkout main
git pull origin main
git checkout -b phase3/financial-models
# Execute AGENT-MVP-008.md
# Port calculators from Proposal Builder
git push origin phase3/financial-models
```

**Verify:**
- [ ] Proposals include ROI calculations
- [ ] Payback period calculated
- [ ] Numbers change with inputs (not hardcoded)

### Step 3.2: HTML Templates (MVP-009)

```bash
git checkout main
git pull origin main
git checkout -b phase3/html-templates
# Execute AGENT-MVP-009.md
# Port styling from Presentation Builder, MAP
git push origin phase3/html-templates
```

**Verify:**
- [ ] Content renders as beautiful HTML
- [ ] Animated backgrounds work
- [ ] Can download HTML file
- [ ] Print-to-PDF ready

### Step 3.3: Contract Generation (MVP-010)

```bash
git checkout main
git pull origin main
git checkout -b phase3/contract-generation
# Execute AGENT-MVP-010.md
# Port template from Contract Builder
git push origin phase3/contract-generation
```

**Verify:**
- [ ] Contract type available in content generator
- [ ] Customer info substituted correctly
- [ ] Pricing table populated
- [ ] Can download markdown

### Step 3.4: Phase 3 Merge (MVP-011)

```bash
git checkout main
git pull origin main
git merge origin/phase3/financial-models --no-ff
git merge origin/phase3/html-templates --no-ff
git merge origin/phase3/contract-generation --no-ff
docker-compose down -v && docker-compose up --build -d
git push origin main
```

**Verify:**
- [ ] All Phase 1 & 2 features work
- [ ] Proposals have financial analysis
- [ ] Content has beautiful HTML output
- [ ] Contracts generate correctly

---

## Phase 4: Polish & Finalize

**Goal:** Wire analytics and ensure everything works perfectly.

### Step 4.1: Analytics Dashboard (MVP-012)

```bash
git checkout main
git pull origin main
git checkout -b phase4/analytics-dashboard
# Execute AGENT-MVP-012.md
git push origin phase4/analytics-dashboard
git checkout main
git merge origin/phase4/analytics-dashboard --no-ff
git push origin main
```

**Verify:**
- [ ] Dashboard shows real metrics
- [ ] Numbers update when data changes
- [ ] Charts render correctly

### Step 4.2: Final Polish (MVP-013)

```bash
git checkout main
git pull origin main
git checkout -b phase4/final-polish
# Execute AGENT-MVP-013.md
# Test ALL flows end-to-end
# Fix any bugs discovered
git push origin phase4/final-polish
git checkout main
git merge origin/phase4/final-polish --no-ff
git push origin main
```

**Final Checklist:**
- [ ] Login → Dashboard works
- [ ] Transcript → SPICED analysis works
- [ ] Enrichment → Web research → Save works
- [ ] Content → Generate → HTML preview → Download works
- [ ] Proposal → Financial analysis → Download works
- [ ] Contract → Generate → Download works
- [ ] Outreach → Generate → Export CSVs works
- [ ] Analytics → Real data displayed
- [ ] No 500 errors on any flow
- [ ] No console errors in browser

---

## Environment Setup

Before starting, ensure `.env` has:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://salesos:salesos_dev_password@postgres:5432/salesos
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=sk-ant-xxx

# Phase 2+ (enhanced enrichment)
SERPER_API_KEY=xxx

# Optional (basic enrichment works without)
CLEARBIT_API_KEY=xxx
APOLLO_API_KEY=xxx

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Quick Start Commands

```bash
# Start system
docker-compose up --build -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Reset everything
docker-compose down -v
docker-compose up --build -d

# Test backend health
curl http://localhost:8000/health

# Open frontend
# http://localhost:3000
```

---

## Troubleshooting

### Backend won't start
```bash
docker-compose logs backend | tail -50
# Look for import errors, fix in __init__.py
```

### Frontend shows blank page
```bash
docker-compose logs frontend | tail -50
# Check for TypeScript/build errors
```

### API returns 500
```bash
docker-compose exec backend python -c "from app.api import api_router"
# This will show import errors
```

### Mock data still appearing
Search and remove:
```bash
grep -r "generateMock" frontend/
grep -r "MOCK_" frontend/
# Delete any found functions/constants
```

---

## Agent Execution Tips

1. **Read the agent file completely** before starting
2. **Follow the test script** after each change
3. **Don't skip the verification** - it catches problems early
4. **Commit often** - easier to rollback
5. **Ask for help** if stuck on a merge conflict

---

## Success Criteria

When complete, Sales OS will:

1. ✅ Authenticate users
2. ✅ Parse transcripts and extract SPICED methodology
3. ✅ Enrich prospects with web research and AI insights
4. ✅ Generate professional content with financial ROI models
5. ✅ Render beautiful HTML output
6. ✅ Generate SaaS contracts
7. ✅ Create personalized outreach campaigns
8. ✅ Export to Instantly and HeyReach
9. ✅ Display real analytics on dashboard
10. ✅ Handle errors gracefully

**This is a complete, working Sales OS MVP.**
