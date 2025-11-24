# AGENT-MVP-006 — `phase2/outreach-campaigns`

**Branch Name:** `phase2/outreach-campaigns`

**Role:** Add outreach campaign generation with export to Instantly and HeyReach.

**End Goal:** User can generate personalized email/LinkedIn sequences and download ready-to-import CSVs.

---

## What Must Work When Done

1. User views an enriched prospect
2. User clicks "Generate Outreach Campaign"
3. Backend generates personalized:
   - 3-email sequence for Instantly
   - LinkedIn connection request + follow-ups for HeyReach
4. User downloads CSV files ready to import into tools
5. Emails/messages use real prospect data (not templates)

---

## Source Code to Port

Read and adapt from these Smashmouth files:

```
C:\Users\leerg\OneDrive\Desktop\Smashmouth\outreach\
C:\Users\leerg\OneDrive\Desktop\Smashmouth\run_pipeline.py (output formats)
```

Key patterns:
- Instantly CSV format: `email,first_name,last_name,company,email_1_subject,email_1_body,email_2_subject,email_2_body,email_3_subject,email_3_body`
- HeyReach CSV format: `linkedin_url,first_name,last_name,company,connection_message,followup_1,followup_2`

---

## Responsibilities

### Backend - New Service
1. Create `backend/app/services/outreach/` directory
2. Create `campaign_generator.py` - generates personalized sequences
3. Create `export_service.py` - formats for Instantly/HeyReach
4. Use Claude to write personalized, human-sounding messages

### Backend - New API
1. Create `backend/app/api/outreach.py` with endpoints:
   - `POST /api/v1/outreach/generate` - generate campaign for prospect(s)
   - `GET /api/v1/outreach/export/instantly/{campaign_id}` - download Instantly CSV
   - `GET /api/v1/outreach/export/heyreach/{campaign_id}` - download HeyReach CSV
2. Wire router in `__init__.py`

### Frontend
1. Add "Generate Outreach" button to prospect card/page
2. Show campaign preview before download
3. Add download buttons for each format
4. Show which prospects have campaigns generated

---

## Files/Folders to Create

**New Files:**
- `/backend/app/services/outreach/__init__.py`
- `/backend/app/services/outreach/campaign_generator.py`
- `/backend/app/services/outreach/export_service.py`
- `/backend/app/api/outreach.py`

**Modify:**
- `/backend/app/api/__init__.py` - add outreach router
- `/frontend/app/prospects/page.tsx` - add outreach button
- `/frontend/lib/api/outreach.ts` - new API client (create)

---

## Message Quality Standards

From Smashmouth - messages must be:
- **Human-sounding** - no "leverage", "streamline", "optimize"
- **Research-based** - reference specific company details
- **Role-appropriate** - different messaging for CFO vs VP Ops
- **Concise** - respect recipient's time

---

## Test Script

```bash
# 1. Start the system
docker-compose up --build -d
sleep 15

# 2. Generate campaign for prospect
curl -X POST http://localhost:8000/api/v1/outreach/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prospect_id": "test-123",
    "prospect_email": "john@acme.com",
    "prospect_name": "John Smith",
    "prospect_title": "VP Finance",
    "company_name": "Acme Corp",
    "company_description": "B2B SaaS company with usage-based pricing"
  }'

# 3. Response should include campaign_id and preview

# 4. Download Instantly CSV
curl http://localhost:8000/api/v1/outreach/export/instantly/{campaign_id} \
  -o instantly_campaign.csv

# 5. Download HeyReach CSV
curl http://localhost:8000/api/v1/outreach/export/heyreach/{campaign_id} \
  -o heyreach_campaign.csv

# 6. Verify CSVs have proper format and personalized content
```

---

## Dependencies

- AGENT-MVP-005 (web research for better personalization)

---

## Acceptance Criteria

- [ ] Campaign generator creates 3-email sequence
- [ ] Campaign generator creates LinkedIn sequence
- [ ] Messages are personalized (not generic templates)
- [ ] Messages sound human (no AI buzzwords)
- [ ] Instantly CSV downloads in correct format
- [ ] HeyReach CSV downloads in correct format
- [ ] Frontend has generate/download buttons
- [ ] Can generate campaigns for multiple prospects
- [ ] Claude API used for message generation
