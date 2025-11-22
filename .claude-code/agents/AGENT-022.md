# AGENT-022 — `backend/notifications`

**Branch Name:** `feature/notification-system`

**Role:** Build the notification system for real-time alerts and updates.

**Responsibilities:**
- Create notification service in `/backend/app/services/notifications/`
- Implement:
  - In-app notifications (bell icon)
  - Email notifications (digest, instant)
  - WebSocket real-time updates
  - Notification preferences per user
- Notification types:
  - Transcript processed
  - Content generated
  - Enrichment complete
  - Coaching feedback ready
  - Integration sync status

**Files/Folders Touched:**
- `/backend/app/services/notifications/*`
- `/backend/app/api/notifications.py`
- `/backend/app/models/notification.py`
- `/backend/app/websockets/*`
- `/frontend/components/notifications/*`

**Dependencies:** AGENT-002, AGENT-011

**Acceptance Criteria:**
- Real-time notifications delivered via WebSocket
- Email notifications send correctly
- Users can configure preferences
- Notifications persist and can be marked read
- No duplicate notifications
