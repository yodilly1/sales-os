# AGENT-026 — `integrations/email`

**Branch Name:** `feature/email-integration`

**Role:** Build email integration for sending and tracking sales communications.

**Responsibilities:**
- Create email service in `/backend/app/integrations/email/`
- Implement:
  - Email sending via SendGrid/SES
  - Email templates (follow-up, proposal, intro)
  - Open/click tracking
  - Bounce handling
  - Unsubscribe management
- Integrate with workflows:
  - Post-call follow-up emails
  - Content delivery emails
  - Prospect outreach sequences

**Files/Folders Touched:**
- `/backend/app/integrations/email/*`
- `/backend/app/api/email.py`
- `/backend/app/models/email.py`
- `/data/templates/email/*`

**Dependencies:** AGENT-002, AGENT-011

**Acceptance Criteria:**
- Emails send reliably
- Templates render correctly with variables
- Tracking captures opens and clicks
- Bounces handled gracefully
- Compliant with email regulations
