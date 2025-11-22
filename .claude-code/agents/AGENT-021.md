# AGENT-021 — `frontend/settings`

**Branch Name:** `feature/frontend-settings`

**Role:** Build the settings and configuration UI for users and organizations.

**Responsibilities:**
- Create settings pages in `/frontend/app/settings/`
- Implement:
  - User profile settings (name, avatar, preferences)
  - Organization settings (branding, defaults)
  - Integration connections (HubSpot, Avoma status)
  - API key management
  - Notification preferences
- Add components:
  - SettingsNav - settings navigation
  - IntegrationCard - connection status
  - ApiKeyManager - create/revoke keys

**Files/Folders Touched:**
- `/frontend/app/settings/*`
- `/frontend/components/settings/*`
- `/frontend/lib/api/settings.ts`

**Dependencies:** AGENT-003, AGENT-012

**Acceptance Criteria:**
- All settings pages functional
- Integration status displays correctly
- API keys can be managed securely
- Changes save and persist
- Responsive design
