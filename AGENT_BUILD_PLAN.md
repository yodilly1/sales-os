# Sales OS MVP - Phased Agent Build Plan

## Overview

This plan uses a phased approach: **Build → Combine → Review → Repeat**

Each phase has specific agents that create branches, then an orchestrator merges and reviews before the next phase begins.

---

## Phase 1: Wire Up Existing Code

**Goal**: Connect the code the 40 agents already built. No new features - just make it work.

### AGENT-PHASE1-001: Wire Core API Routes
**Branch**: `phase1/wire-core-apis`
**Priority**: P0
**Dependencies**: None

**Task**:
1. Update `backend/app/api/__init__.py` to include:
   - transcript router → `/api/v1/transcript`
   - enrichment router → `/api/v1/enrichment`
   - content router → `/api/v1/content`
   - team router → `/api/v1/team`
   - analytics router → `/api/v1/analytics`
2. Fix any import errors in these route files
3. Verify each router has proper `router = APIRouter()` definition
4. Test that server starts without errors

**Success Criteria**:
- [ ] `docker-compose up` starts without import errors
- [ ] `/api/v1/transcript/parse` endpoint responds (even if 500)
- [ ] `/api/v1/enrichment` endpoint responds
- [ ] `/api/v1/content` endpoint responds
- [ ] `/docs` shows all new endpoints

---

### AGENT-PHASE1-002: Wire Secondary API Routes
**Branch**: `phase1/wire-secondary-apis`
**Priority**: P0
**Dependencies**: None (can run parallel with 001)

**Task**:
1. Update `backend/app/api/__init__.py` to include:
   - coaching router → `/api/v1/coaching`
   - meetingprep router → `/api/v1/meetingprep`
   - render router → `/api/v1/render`
   - search router → `/api/v1/search`
   - talktracks router → `/api/v1/talktracks`
   - export router → `/api/v1/export`
   - hubspot router → `/api/v1/hubspot`
   - gong router → `/api/v1/gong`
   - salesforce router → `/api/v1/salesforce`
2. Fix any import errors in these route files
3. Test that server starts without errors

**Success Criteria**:
- [ ] All routers registered without errors
- [ ] `/docs` shows complete API surface
- [ ] No import errors on startup

---

### AGENT-PHASE1-003: Fix Service Dependencies
**Branch**: `phase1/fix-service-deps`
**Priority**: P0
**Dependencies**: None (can run parallel)

**Task**:
1. Check each service in `backend/app/services/` for import errors
2. Fix missing `__init__.py` exports
3. Ensure `claude_client.py` is properly configured
4. Verify database session dependency injection works
5. Fix any circular import issues

**Files to check**:
- `services/transcript/__init__.py`
- `services/enrichment/__init__.py`
- `services/content/__init__.py`
- `services/claude_client.py`
- `db/session.py`

**Success Criteria**:
- [ ] All services can be imported without errors
- [ ] `from app.services.transcript import TranscriptParser, SPICEDExtractor` works
- [ ] `from app.services.enrichment import EnrichmentService` works
- [ ] `from app.services.content import ContentGenerator` works

---

### PHASE 1 ORCHESTRATOR
**After AGENT-PHASE1-001, 002, 003 complete**

1. Merge all phase1 branches to `main`
2. Resolve any conflicts
3. Run `docker-compose up --build`
4. Verify `/docs` shows all endpoints
5. Run basic smoke tests on each endpoint
6. Document any issues for Phase 2

---

## Phase 2: Enhance Enrichment with Smashmouth

**Goal**: Port Smashmouth's superior web research capabilities.

### AGENT-PHASE2-001: Port Web Research Engine
**Branch**: `phase2/web-research-engine`
**Priority**: P1
**Dependencies**: Phase 1 complete

**Task**:
1. Create `backend/app/services/enrichment/providers/web_research.py`
2. Port core functionality from `Smashmouth/core/web_research_engine.py`:
   - Serper API integration for Google search
   - Company website scraping
   - News/press release fetching
   - Rate limiting and caching
3. Add `SERPER_API_KEY` to `backend/app/core/config.py`
4. Register as new provider in `EnrichmentService`

**Source Files** (read these):
- `C:\Users\leerg\OneDrive\Desktop\Smashmouth\core\web_research_engine.py`

**Success Criteria**:
- [ ] Web research provider returns real search results
- [ ] Rate limiting prevents API abuse
- [ ] Provider integrates with existing enrichment service

---

### AGENT-PHASE2-002: Port AI Research Analysis
**Branch**: `phase2/ai-research-analysis`
**Priority**: P1
**Dependencies**: AGENT-PHASE2-001

**Task**:
1. Enhance `backend/app/services/enrichment/service.py` with Claude analysis
2. Port from `Smashmouth/core/enhanced_ai_research_engine.py`:
   - `analyze_company_with_fresh_data()` method
   - Revenue model classification
   - Business intelligence extraction
   - Confidence scoring
3. Integrate with existing `claude_client.py`

**Source Files** (read these):
- `C:\Users\leerg\OneDrive\Desktop\Smashmouth\core\enhanced_ai_research_engine.py`

**Success Criteria**:
- [ ] Enrichment returns AI-analyzed company insights
- [ ] Revenue model classification works
- [ ] Confidence scores calculated

---

### AGENT-PHASE2-003: Add Outreach Campaign Export
**Branch**: `phase2/outreach-export`
**Priority**: P1
**Dependencies**: Phase 1 complete (can run parallel with 001/002)

**Task**:
1. Create `backend/app/services/outreach/` directory
2. Create `campaign_generator.py` - generates email sequences
3. Create `export_service.py` - exports to Instantly/HeyReach CSV format
4. Create `backend/app/api/outreach.py` router with endpoints:
   - `POST /api/v1/outreach/generate` - generate campaign from prospect
   - `GET /api/v1/outreach/export/instantly` - download Instantly CSV
   - `GET /api/v1/outreach/export/heyreach` - download HeyReach CSV
5. Wire router in `__init__.py`

**Source Files** (read these):
- `C:\Users\leerg\OneDrive\Desktop\Smashmouth\outreach\` directory
- `C:\Users\leerg\OneDrive\Desktop\Smashmouth\run_pipeline.py` (for output formats)

**Success Criteria**:
- [ ] Can generate 3-email sequence for prospect
- [ ] Can export Instantly-compatible CSV
- [ ] Can export HeyReach-compatible CSV

---

### PHASE 2 ORCHESTRATOR
**After AGENT-PHASE2-001, 002, 003 complete**

1. Merge all phase2 branches to `main`
2. Resolve conflicts (especially in enrichment service)
3. Test enrichment with web research enabled
4. Test outreach export endpoints
5. Verify no regressions in Phase 1 functionality

---

## Phase 3: Enhance Content Generation

**Goal**: Add financial models and better templates from your builder projects.

### AGENT-PHASE3-001: Port Financial ROI Models
**Branch**: `phase3/financial-models`
**Priority**: P1
**Dependencies**: Phase 2 complete

**Task**:
1. Create `backend/app/services/content/financial_models.py`
2. Port from Proposal Builder `_scripts/template_processor.py`:
   - DSO/Working Capital calculator
   - Labor Savings calculator
   - Revenue Leakage calculator
   - ROI and Payback period calculator
3. Integrate with `ContentGenerator._generate_proposal()`
4. Add financial metrics to proposal output

**Source Files** (read these):
- `C:\Users\leerg\OneDrive\Documents\Proposal Builder\_scripts\generate_proposal.py`
- `C:\Users\leerg\OneDrive\Documents\Proposal Builder\_scripts\template_processor.py` (if exists)
- `C:\Users\leerg\OneDrive\Documents\Proposal Builder\OptiMove_Proposal\` (for reference)

**Success Criteria**:
- [ ] Proposals include calculated ROI metrics
- [ ] DSO improvement calculations work
- [ ] Labor savings calculations work
- [ ] Payback period calculated

---

### AGENT-PHASE3-002: Add Contract Generation
**Branch**: `phase3/contract-generation`
**Priority**: P2
**Dependencies**: Phase 1 complete (can run parallel)

**Task**:
1. Add `ContentType.CONTRACT` to `backend/app/core/constants.py`
2. Create contract template in `backend/app/services/content/templates/`
3. Add `_generate_contract()` method to `ContentGenerator`
4. Template should include:
   - Order form with pricing
   - Master SaaS agreement terms
   - DPA exhibit placeholder
   - Signature blocks

**Source Files** (read these):
- `C:\Users\leerg\OneDrive\Documents\Contract Builder\Swimm\Vayu Master SaaS Agreement - Swimm.md`
- `C:\Users\leerg\OneDrive\Documents\Contract Builder\Sample Agreement\` (for structure)

**Success Criteria**:
- [ ] Can generate contract markdown from deal data
- [ ] Pricing table populated correctly
- [ ] Customer name/details substituted

---

### AGENT-PHASE3-003: Enhance HTML Rendering
**Branch**: `phase3/html-templates`
**Priority**: P1
**Dependencies**: Phase 1 complete (can run parallel)

**Task**:
1. Enhance `backend/app/services/rendering/html_renderer.py`
2. Port CSS/styling from your builder projects:
   - Animated gradient backgrounds
   - Floating orb animations
   - Glass-morphism cards
   - Professional typography
3. Create base template with your styling
4. Apply to proposal, deck, and one-pager rendering

**Source Files** (read these):
- `C:\Users\leerg\OneDrive\Documents\Presentation Builder\Reserv\index.html`
- `C:\Users\leerg\OneDrive\Documents\Proposal Builder\OptiMove_Proposal\index.html`
- `C:\Users\leerg\OneDrive\Documents\MAP\Nirvana Tech\Deploy\index.html`

**Success Criteria**:
- [ ] Rendered HTML has animated backgrounds
- [ ] Cards have glass-morphism styling
- [ ] Output is print-to-PDF ready
- [ ] Mobile responsive

---

### PHASE 3 ORCHESTRATOR
**After AGENT-PHASE3-001, 002, 003 complete**

1. Merge all phase3 branches to `main`
2. Resolve conflicts in content service
3. Test proposal generation with financial models
4. Test contract generation
5. Test HTML rendering quality
6. Verify no regressions

---

## Phase 4: Frontend Integration

**Goal**: Connect frontend to all the backend APIs, remove mock data.

### AGENT-PHASE4-001: Connect Transcript Flow
**Branch**: `phase4/frontend-transcript`
**Priority**: P0
**Dependencies**: Phase 1 complete

**Task**:
1. Update `frontend/lib/api/transcript.ts` to match backend endpoints
2. Update `frontend/app/transcript/page.tsx` to use real API
3. Remove mock data from transcript pages
4. Test upload → parse → display SPICED flow

**Success Criteria**:
- [ ] Can upload transcript text
- [ ] SPICED analysis displays correctly
- [ ] Call notes and tasks generated
- [ ] No console errors

---

### AGENT-PHASE4-002: Connect Enrichment Flow
**Branch**: `phase4/frontend-enrichment`
**Priority**: P0
**Dependencies**: Phase 2 complete

**Task**:
1. Update `frontend/lib/api/enrichment.ts` to match backend endpoints
2. Update `frontend/app/prospects/page.tsx` to use real API
3. Remove mock data and `generateMockContent()` calls
4. Test single lookup and bulk upload flows

**Success Criteria**:
- [ ] Can lookup single prospect
- [ ] Can upload CSV for bulk enrichment
- [ ] Enriched data displays correctly
- [ ] Web research data visible (if available)

---

### AGENT-PHASE4-003: Connect Content Flow
**Branch**: `phase4/frontend-content`
**Priority**: P0
**Dependencies**: Phase 3 complete

**Task**:
1. Update `frontend/lib/api/content.ts` to match backend endpoints
2. Update `frontend/app/content/page.tsx` to use real API
3. Remove `generateMockContent()` function entirely
4. Test content generation and display

**Success Criteria**:
- [ ] Can generate deck from form
- [ ] Can generate proposal with financial model
- [ ] Generated content displays correctly
- [ ] Can download/export content

---

### AGENT-PHASE4-004: Connect Analytics Dashboard
**Branch**: `phase4/frontend-analytics`
**Priority**: P1
**Dependencies**: Phase 1 complete

**Task**:
1. Update `frontend/lib/api/analytics.ts` to match backend endpoints
2. Update `frontend/app/analytics/page.tsx` to use real API
3. Replace hardcoded metrics with API calls
4. Connect charts to real data

**Success Criteria**:
- [ ] Dashboard shows real metrics
- [ ] Charts render with backend data
- [ ] Date range filtering works

---

### PHASE 4 ORCHESTRATOR
**After AGENT-PHASE4-001, 002, 003, 004 complete**

1. Merge all phase4 branches to `main`
2. Resolve any frontend conflicts
3. Full end-to-end testing:
   - Login → Upload transcript → View SPICED
   - Enrich prospect → Generate content → Download
   - View analytics dashboard
4. Fix any UI/UX issues discovered
5. Final smoke test all features

---

## Phase 5: Polish & Deploy

**Goal**: Final testing, documentation, and deployment prep.

### AGENT-PHASE5-001: End-to-End Testing
**Branch**: `phase5/e2e-testing`
**Priority**: P1

**Task**:
1. Create test scripts for critical flows
2. Test with real API keys (Claude, Serper if added)
3. Document any bugs found
4. Performance testing on key endpoints

---

### AGENT-PHASE5-002: Environment & Documentation
**Branch**: `phase5/documentation`
**Priority**: P1

**Task**:
1. Create `.env.example` with all required variables
2. Update README with setup instructions
3. Document API endpoints
4. Create deployment guide

---

### FINAL ORCHESTRATOR
**After all phases complete**

1. Final merge to `main`
2. Tag release version
3. Deploy to production environment
4. Celebrate 🎉

---

## Execution Summary

| Phase | Agents | Can Parallelize | Est. Time |
|-------|--------|-----------------|-----------|
| Phase 1 | 3 | Yes (all 3) | 2-3 hours |
| Phase 2 | 3 | Partial (001→002, 003 parallel) | 3-4 hours |
| Phase 3 | 3 | Yes (all 3) | 3-4 hours |
| Phase 4 | 4 | Partial (depends on backend) | 3-4 hours |
| Phase 5 | 2 | Yes | 2 hours |

**Total: 15 agents + 5 orchestrator passes = ~15-20 hours**

---

## How to Run

1. **Start Phase 1**: Run agents 001-003 in parallel
2. **Orchestrate**: Merge, test, fix issues
3. **Start Phase 2**: Run agents sequentially (001→002) + 003 parallel
4. **Orchestrate**: Merge, test
5. **Continue pattern for Phases 3-5**

Each phase produces a working increment - you can stop after any phase and have a functional system.
