# AGENT-MVP-005 — `phase2/smashmouth-web-research`

**Branch Name:** `phase2/smashmouth-web-research`

**Role:** Port Smashmouth's web research engine to enhance prospect enrichment with real-time web data.

**End Goal:** Enrichment returns real company intel from Google search, not just API provider data.

---

## What Must Work When Done

1. User looks up a prospect on `/prospects` page
2. Backend performs web search (Google via Serper) for company info
3. Claude analyzes the search results for business intelligence
4. Frontend displays enriched data including:
   - Recent news/press releases
   - Funding information
   - Company description from web
   - Key business insights
5. Works even without Clearbit/Apollo API keys

---

## Source Code to Port

Read and adapt from these Smashmouth files:

```
C:\Users\leerg\OneDrive\Desktop\Smashmouth\core\web_research_engine.py
C:\Users\leerg\OneDrive\Desktop\Smashmouth\core\enhanced_ai_research_engine.py
```

Key functions to port:
- `research_company_comprehensive()` - main research function
- `search_google()` - Serper API integration
- `analyze_company_with_fresh_data()` - Claude analysis
- `classify_revenue_model()` - business classification

---

## Responsibilities

### Backend - New Provider
1. Create `backend/app/services/enrichment/providers/web_research.py`
2. Port Serper API integration for Google search
3. Implement rate limiting and caching
4. Add `SERPER_API_KEY` to config

### Backend - AI Analysis
1. Create `backend/app/services/enrichment/ai_analyzer.py`
2. Port Claude-based company analysis from Smashmouth
3. Extract: funding stage, revenue model, key insights
4. Integrate with existing `claude_client.py`

### Backend - Integration
1. Register web research as new provider in `EnrichmentService`
2. Call AI analyzer after web research completes
3. Merge web research data with other provider data

### Frontend
1. Display web research results in prospect card
2. Show "Recent News" section
3. Show "AI Insights" section
4. Handle loading state for web research (can be slower)

---

## Files/Folders to Create

**New Files:**
- `/backend/app/services/enrichment/providers/web_research.py`
- `/backend/app/services/enrichment/ai_analyzer.py`

**Modify:**
- `/backend/app/services/enrichment/service.py` - add web research provider
- `/backend/app/core/config.py` - add SERPER_API_KEY
- `/frontend/components/prospects/ProspectCard.tsx` - show web data

---

## Environment Required

```bash
SERPER_API_KEY=xxx          # Required for Google search
ANTHROPIC_API_KEY=sk-ant-xxx  # Required for AI analysis
```

Get Serper API key at: https://serper.dev (free tier available)

---

## Test Script

```bash
# 1. Start the system
docker-compose up --build -d
sleep 15

# 2. Test web research directly
curl -X POST http://localhost:8000/api/v1/enrichment/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ceo@stripe.com",
    "company_name": "Stripe",
    "company_domain": "stripe.com",
    "include_web_research": true
  }'

# 3. Response should include:
# - web_research.news (recent articles)
# - web_research.funding (funding info if found)
# - ai_insights.revenue_model
# - ai_insights.key_findings

# 4. Test frontend
# Open http://localhost:3000/prospects
# Search for "Stripe"
# Should see web research data in results
```

---

## Dependencies

- AGENT-MVP-004 (Phase 1 orchestrator complete)

---

## Acceptance Criteria

- [ ] Web research provider created and registered
- [ ] Serper API called for Google search
- [ ] Search results analyzed by Claude
- [ ] Enrichment response includes web research data
- [ ] Enrichment response includes AI insights
- [ ] Frontend displays web research results
- [ ] Works for well-known companies (Stripe, Salesforce, etc.)
- [ ] Graceful fallback if Serper API key not configured
- [ ] Rate limiting prevents API abuse
