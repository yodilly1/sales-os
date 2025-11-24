# AGENT-MVP-002 — `phase1/enrichment-flow`

**Branch Name:** `phase1/enrichment-flow`

**Role:** Make the complete prospect enrichment flow work end-to-end.

**End Goal:** User can enter a prospect's email/company and see enriched data in the UI.

---

## What Must Work When Done

1. User navigates to `/prospects` page
2. User enters prospect email or company name
3. Backend enriches prospect using available providers
4. Frontend displays enriched data (company info, contact details, social profiles)
5. Bulk CSV upload works for multiple prospects
6. No mock data - real enrichment (even if limited without API keys)

---

## Responsibilities

### Backend
1. Wire `enrichment` router in `backend/app/api/__init__.py`
2. Fix any import errors in `backend/app/api/enrichment.py`
3. Verify `EnrichmentService` initializes (even with no API keys)
4. Add graceful handling when no enrichment providers configured
5. Test endpoint: `POST /api/v1/enrichment/lookup`

### Frontend
1. Update `frontend/lib/api/enrichment.ts` to call real backend
2. Update `frontend/app/prospects/page.tsx` to use real API
3. Remove all mock data and `generateMock*` functions
4. Display whatever data the backend returns (even if minimal)
5. Handle "no enrichment providers configured" gracefully

### Integration
1. Test single prospect lookup flow
2. Test bulk CSV upload flow
3. Verify data persists (can refresh and see same prospects)

---

## Files/Folders Touched

**Backend:**
- `/backend/app/api/__init__.py` - add enrichment router
- `/backend/app/api/enrichment.py` - verify/fix imports
- `/backend/app/services/enrichment/__init__.py` - verify exports
- `/backend/app/services/enrichment/service.py` - verify works
- `/backend/app/services/enrichment/providers/` - check providers init
- `/backend/app/models/prospect.py` - verify model

**Frontend:**
- `/frontend/lib/api/enrichment.ts` - update to real endpoints
- `/frontend/app/prospects/page.tsx` - remove mock, use real API
- `/frontend/components/prospects/` - verify components work

---

## Environment (Optional - works without)

```bash
# These make enrichment richer, but system works without them
CLEARBIT_API_KEY=xxx
APOLLO_API_KEY=xxx
HUNTER_API_KEY=xxx
```

---

## Test Script

```bash
# 1. Start the system
docker-compose up --build -d

# 2. Wait for services
sleep 15

# 3. Test backend endpoint
curl -X POST http://localhost:8000/api/v1/enrichment/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@acme.com",
    "company_name": "Acme Corporation",
    "company_domain": "acme.com"
  }'

# 4. Should return prospect data (even if minimal without API keys)

# 5. Test frontend
# Open http://localhost:3000/prospects
# Enter email: test@acme.com
# Click lookup
# Verify some data appears (even if just echoed back)
```

---

## Dependencies

- AGENT-MVP-001 (Phase 1 should be sequential to avoid conflicts)

---

## Acceptance Criteria

- [ ] Backend starts without import errors
- [ ] `POST /api/v1/enrichment/lookup` returns data (not 500 error)
- [ ] Frontend prospects page loads without errors
- [ ] Single prospect lookup shows results in UI
- [ ] Bulk CSV upload accepts file and processes it
- [ ] No mock data in the flow
- [ ] Graceful message if no enrichment providers configured
