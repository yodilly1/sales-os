# AGENT-038 — `integrations/salesforce`

**Branch Name:** `feature/salesforce-integration`

**Role:** Build Salesforce CRM integration as alternative to HubSpot.

**Responsibilities:**
- Create Salesforce client in `/backend/app/integrations/salesforce/`
- Implement methods:
  - `create_lead()` / `create_contact()`
  - `update_opportunity()`
  - `add_task()`
  - `log_activity()`
  - `search_records()`
- Handle:
  - OAuth2 authentication
  - Custom field mapping
  - Sandbox vs Production environments
  - Bulk API for large operations

**Files/Folders Touched:**
- `/backend/app/integrations/salesforce/*`
- `/backend/app/api/salesforce.py`
- `/backend/app/models/salesforce.py`
- `/frontend/app/settings/integrations/salesforce/*`

**Dependencies:** AGENT-002, AGENT-011, AGENT-012

**Acceptance Criteria:**
- Salesforce OAuth works for all org types
- CRUD operations function correctly
- Custom fields map properly
- Bulk operations handle large datasets
- Error handling matches Salesforce API patterns
