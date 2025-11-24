# AGENT-MVP-012 — `phase4/analytics-dashboard`

**Branch Name:** `phase4/analytics-dashboard`

**Role:** Make the analytics dashboard show real data from the system.

**End Goal:** Dashboard displays actual metrics from transcripts, enrichments, and content generated.

---

## What Must Work When Done

1. User navigates to `/analytics` or `/dashboard`
2. Dashboard shows real metrics:
   - Total transcripts analyzed
   - Average SPICED scores
   - Prospects enriched
   - Content pieces generated
   - Outreach campaigns created
3. Charts show trends over time
4. No hardcoded/mock data - all from database

---

## Responsibilities

### Backend - Analytics Service
1. Create/enhance `backend/app/services/analytics/` service
2. Implement queries for:
   - Transcript count and SPICED score averages
   - Prospect count and enrichment rates
   - Content generation by type
   - Activity over time (daily/weekly)
3. Cache results for performance (optional)

### Backend - API
1. Wire `analytics` router in `backend/app/api/__init__.py`
2. Fix any import errors in `backend/app/api/analytics.py`
3. Ensure endpoints return real data from database
4. Key endpoints:
   - `GET /api/v1/analytics/overview` - summary metrics
   - `GET /api/v1/analytics/transcripts` - transcript metrics
   - `GET /api/v1/analytics/prospects` - enrichment metrics
   - `GET /api/v1/analytics/content` - content metrics
   - `GET /api/v1/analytics/activity` - time series data

### Frontend
1. Update `frontend/lib/api/analytics.ts` to call real backend
2. Update `frontend/app/analytics/page.tsx` - remove hardcoded data
3. Update `frontend/app/dashboard/page.tsx` - use real metrics
4. Connect charts to real time series data

---

## Files/Folders Touched

**Backend:**
- `/backend/app/api/__init__.py` - wire analytics router
- `/backend/app/api/analytics.py` - verify/fix endpoints
- `/backend/app/services/analytics/` - implement service (may need creation)

**Frontend:**
- `/frontend/lib/api/analytics.ts` - call real endpoints
- `/frontend/app/analytics/page.tsx` - remove mock data
- `/frontend/app/dashboard/page.tsx` - use real metrics
- `/frontend/components/analytics/` - verify charts work with real data

---

## Analytics Overview Response

```json
{
  "overview": {
    "total_transcripts": 42,
    "total_prospects": 156,
    "total_content": 28,
    "total_campaigns": 12
  },
  "spiced_averages": {
    "situation": 7.2,
    "pain": 6.8,
    "impact": 5.9,
    "critical_event": 4.5,
    "decision": 6.1
  },
  "content_by_type": {
    "deck_pitch": 12,
    "proposal": 8,
    "contract": 5,
    "one_pager": 3
  },
  "activity_last_7_days": [
    {"date": "2024-11-18", "transcripts": 3, "prospects": 12, "content": 2},
    {"date": "2024-11-19", "transcripts": 5, "prospects": 8, "content": 4},
    ...
  ]
}
```

---

## Test Script

```bash
# 1. Start system
docker-compose up --build -d
sleep 15

# 2. Create some test data first
# Upload a transcript
curl -X POST http://localhost:8000/api/v1/transcript/parse \
  -H "Content-Type: application/json" \
  -d '{"transcript_text": "Test transcript for analytics", "company_name": "Test Co"}'

# Enrich a prospect
curl -X POST http://localhost:8000/api/v1/enrichment/lookup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "company_name": "Test Co"}'

# Generate content
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"content_type": "deck_pitch", "goal": "Test", "product_info": {"name": "Test"}}'

# 3. Now test analytics
curl http://localhost:8000/api/v1/analytics/overview

# 4. Should show counts > 0 for transcripts, prospects, content

# 5. Test frontend
# Open http://localhost:3000/dashboard
# Should see real numbers, not "0" or hardcoded values
# Charts should have data points
```

---

## Dependencies

- AGENT-MVP-011 (Phase 3 orchestrator complete)

---

## Acceptance Criteria

- [ ] Analytics router wired and working
- [ ] Overview endpoint returns real counts
- [ ] SPICED averages calculated from actual transcripts
- [ ] Content counts by type are accurate
- [ ] Activity time series has real data
- [ ] Frontend dashboard shows real metrics
- [ ] Charts render with real data
- [ ] Metrics update when new data is added
- [ ] No hardcoded values in frontend
