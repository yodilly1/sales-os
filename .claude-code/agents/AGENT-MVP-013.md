# AGENT-MVP-013 — `phase4/final-polish`

**Branch Name:** `phase4/final-polish`

**Role:** Final integration testing, bug fixes, and polish.

**End Goal:** Complete, working Sales OS MVP ready for use.

---

## What Must Work When Done

Complete end-to-end flows:

1. **Login** → User can authenticate
2. **Transcript** → Upload → SPICED analysis → tasks generated
3. **Enrich** → Lookup prospect → Web research → AI insights → Save
4. **Content** → Generate proposal with financials → View HTML → Download
5. **Contract** → Generate agreement → Download
6. **Outreach** → Generate campaign → Export CSVs
7. **Analytics** → Dashboard shows real data
8. **Settings** → User can update profile

---

## Responsibilities

### Full Flow Testing
1. Test each flow end-to-end as a real user would
2. Document any errors or issues found
3. Fix blocking bugs
4. Create test data for demo purposes

### Bug Fixes
1. Fix any 500 errors discovered
2. Fix any frontend console errors
3. Fix any broken UI elements
4. Ensure loading states work properly

### Polish
1. Ensure error messages are user-friendly
2. Add loading spinners where missing
3. Ensure navigation works correctly
4. Verify mobile responsiveness (basic)

### Documentation
1. Update README with setup instructions
2. Create `.env.example` with all required variables
3. Document API endpoints in `/docs`
4. Add demo data script

---

## Test Checklist

### Authentication
- [ ] Can register new account
- [ ] Can login with credentials
- [ ] Protected pages redirect to login
- [ ] Can logout

### Transcript Flow
- [ ] Navigate to /transcript
- [ ] Paste transcript text
- [ ] Click analyze
- [ ] See SPICED results within 30 seconds
- [ ] See follow-up tasks
- [ ] No errors in console

### Enrichment Flow
- [ ] Navigate to /prospects
- [ ] Enter email/company
- [ ] Click lookup
- [ ] See enriched data
- [ ] Web research data visible (if Serper configured)
- [ ] Can save prospect

### Content Flow
- [ ] Navigate to /content
- [ ] Select deck type
- [ ] Fill in form
- [ ] Click generate
- [ ] See generated slides
- [ ] View HTML preview
- [ ] Download works

### Proposal with Financials
- [ ] Select proposal type
- [ ] Fill in financial inputs
- [ ] Generate
- [ ] See ROI calculations
- [ ] Numbers are calculated, not static

### Contract Flow
- [ ] Select contract type
- [ ] Fill in customer info
- [ ] Generate
- [ ] See contract with substitutions
- [ ] Download markdown

### Outreach Flow
- [ ] View enriched prospect
- [ ] Click generate outreach
- [ ] See email sequence preview
- [ ] Download Instantly CSV
- [ ] Download HeyReach CSV
- [ ] CSVs have correct format

### Analytics
- [ ] Navigate to /dashboard
- [ ] See real numbers (not 0 or mock)
- [ ] Charts render
- [ ] Navigate to /analytics
- [ ] Date filters work (if implemented)

---

## Environment File Template

Create/update `.env.example`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://salesos:salesos_dev_password@postgres:5432/salesos

# Authentication
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-change-in-production

# AI (Required)
ANTHROPIC_API_KEY=sk-ant-xxx

# Enrichment (Optional - enhances features)
SERPER_API_KEY=xxx
CLEARBIT_API_KEY=xxx
APOLLO_API_KEY=xxx

# CRM Integrations (Optional)
HUBSPOT_CLIENT_ID=xxx
HUBSPOT_CLIENT_SECRET=xxx

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Demo Data Script

Create `backend/scripts/create_demo_data.py`:

```python
# Creates sample data for demo purposes
# - Sample transcript with SPICED analysis
# - Sample enriched prospects
# - Sample generated content
# - Sample outreach campaigns
```

---

## Final Validation

```bash
# 1. Clean start
docker-compose down -v
docker-compose up --build -d
sleep 30

# 2. Run demo data script (if created)
docker-compose exec backend python scripts/create_demo_data.py

# 3. Open browser
# http://localhost:3000

# 4. Complete each flow manually
# Document any issues

# 5. Check for errors
docker-compose logs backend | grep -i error
docker-compose logs frontend | grep -i error
```

---

## Dependencies

- AGENT-MVP-012 complete (analytics dashboard)

---

## Acceptance Criteria

- [ ] All 8 flows work end-to-end
- [ ] No 500 errors on happy path
- [ ] No console errors in browser
- [ ] Loading states show during API calls
- [ ] Error states display user-friendly messages
- [ ] `.env.example` documented
- [ ] README has setup instructions
- [ ] Demo data available (optional)
- [ ] System is ready for actual use
