# AGENT-037 — `integrations/slack`

**Branch Name:** `feature/slack-integration`

**Role:** Build Slack integration for notifications and quick actions.

**Responsibilities:**
- Create Slack service in `/backend/app/integrations/slack/`
- Implement:
  - OAuth2 workspace connection
  - Channel notifications (call processed, content ready)
  - DM notifications for personal alerts
  - Slash commands (/salesos prep, /salesos coach)
  - Interactive messages (approve follow-up, view summary)

**Files/Folders Touched:**
- `/backend/app/integrations/slack/*`
- `/backend/app/api/slack.py`
- `/backend/app/api/webhooks.py`
- `/backend/app/models/slack.py`

**Dependencies:** AGENT-002, AGENT-012, AGENT-022

**Acceptance Criteria:**
- Slack OAuth connects workspace
- Notifications post to correct channels
- Slash commands respond appropriately
- Interactive actions work reliably
- Respects user notification preferences
