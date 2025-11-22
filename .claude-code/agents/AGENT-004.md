# AGENT-004 — `integrations/hubspot`

**Branch Name:** `feature/hubspot-integration`

**Role:** Build HubSpot CRM integration for contacts, deals, and notes.

**Responsibilities:**
- Create HubSpot client in `/backend/app/integrations/hubspot/`
- Implement methods:
  - `create_contact()`
  - `update_contact()`
  - `create_deal()`
  - `add_note_to_contact()`
  - `create_task()`
  - `search_contacts()`
- Add API routes in `/backend/app/api/hubspot.py`
- Handle OAuth2 token refresh
- Add rate limiting and error handling

**Files/Folders Touched:**
- `/backend/app/integrations/hubspot/*`
- `/backend/app/api/hubspot.py`
- `/backend/app/models/hubspot.py`

**Dependencies:** AGENT-002

**Acceptance Criteria:**
- HubSpot client connects with valid API key
- CRUD operations for contacts work
- Notes and tasks can be created on contacts
- Proper error handling for API failures
