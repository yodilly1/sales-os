# Sales OS Agent Manifest

## Overview
This manifest lists all Claude Code agents for the Sales OS project. Each agent owns a single feature branch and has zero conflict with other agents.

**Total Agents: 40**

---

## Execution Order

### Phase 1: Foundation (001-003, 011, 017)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-001 | Project Setup | `feature/project-setup` | None |
| AGENT-002 | Backend API Foundation | `feature/backend-api-foundation` | 001 |
| AGENT-003 | Frontend Scaffold | `feature/frontend-scaffold` | 001 |
| AGENT-011 | Data Models & Schemas | `feature/data-models-schemas` | 002 |
| AGENT-017 | Claude Prompts Infrastructure | `feature/claude-prompts` | 002 |

### Phase 2: Core Services (005-007, 010)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-005 | Transcript SPICED Parser | `feature/transcript-spiced-parser` | 002 |
| AGENT-006 | Content Generator | `feature/content-generator` | 002 |
| AGENT-007 | Prospect Enrichment | `feature/prospect-enrichment` | 002, 004 |
| AGENT-010 | SPICED Coaching | `feature/spiced-coaching` | 002, 005 |

### Phase 3: Primary Integrations (004, 009)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-004 | HubSpot Integration | `feature/hubspot-integration` | 002 |
| AGENT-009 | Avoma Integration | `feature/avoma-integration` | 002, 005 |

### Phase 4: Rendering & Output (008)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-008 | PDF/Deck Renderer | `feature/pdf-deck-renderer` | 002, 003, 006 |

### Phase 5: Frontend UIs (013-016, 018, 021)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-013 | Transcript UI | `feature/frontend-transcript-ui` | 003, 005 |
| AGENT-014 | Content UI | `feature/frontend-content-ui` | 003, 006, 008 |
| AGENT-015 | Prospect UI | `feature/frontend-prospect-ui` | 003, 007 |
| AGENT-016 | Coaching UI | `feature/frontend-coaching-ui` | 003, 010 |
| AGENT-018 | Dashboard | `feature/frontend-dashboard` | 003, 012 |
| AGENT-021 | Settings UI | `feature/frontend-settings` | 003, 012 |

### Phase 6: Security & Infrastructure (012, 019-020)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-012 | Authentication & Security | `feature/auth-security` | 002, 003, 011 |
| AGENT-019 | Deployment Config | `feature/deployment-config` | 002, 003 |
| AGENT-020 | E2E Testing | `feature/e2e-testing` | 002, 003, 005, 006, 007 |

### Phase 7: Platform Services (022-025, 028, 030)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-022 | Notification System | `feature/notification-system` | 002, 011 |
| AGENT-023 | File Upload Service | `feature/file-upload-service` | 002, 011 |
| AGENT-024 | Search & Filtering | `feature/search-filtering` | 002, 011 |
| AGENT-025 | Activity Logging | `feature/activity-logging` | 002, 011 |
| AGENT-028 | Team Management | `feature/team-management` | 002, 011, 012 |
| AGENT-030 | Export/Import Service | `feature/export-import` | 002, 011, 023 |

### Phase 8: Extended Integrations (026-027, 036-040)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-026 | Email Integration | `feature/email-integration` | 002, 011 |
| AGENT-027 | Calendar Integration | `feature/calendar-integration` | 002, 012 |
| AGENT-036 | LinkedIn Integration | `feature/linkedin-integration` | 002, 007, 012 |
| AGENT-037 | Slack Integration | `feature/slack-integration` | 002, 012, 022 |
| AGENT-038 | Salesforce Integration | `feature/salesforce-integration` | 002, 011, 012 |
| AGENT-039 | Zoom Integration | `feature/zoom-integration` | 002, 005, 012 |
| AGENT-040 | Gong Integration | `feature/gong-integration` | 002, 005, 012 |

### Phase 9: Advanced Workflows (031-035)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-031 | Battlecard Engine | `feature/battlecard-engine` | 002, 006, 011 |
| AGENT-032 | Talk Track Generator | `feature/talk-track-generator` | 002, 010, 017 |
| AGENT-033 | Deal Room | `feature/deal-room` | 002, 008, 012 |
| AGENT-034 | Meeting Prep | `feature/meeting-prep` | 002, 005, 007, 027 |
| AGENT-035 | Follow-up Automation | `feature/follow-up-automation` | 002, 004, 005, 026 |

### Phase 10: Analytics (029)
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-029 | Analytics Dashboard | `feature/analytics-dashboard` | 003, 011, 018 |

---

## Workflow Coverage

### Workflow 1: Transcript → CRM
- AGENT-005: SPICED extraction
- AGENT-004: HubSpot sync
- AGENT-009: Avoma ingestion
- AGENT-010: Coaching feedback
- AGENT-013: Transcript UI
- AGENT-035: Follow-up automation
- AGENT-039: Zoom integration
- AGENT-040: Gong integration

### Workflow 2: Content Generator
- AGENT-006: Content generation engine
- AGENT-008: PDF/deck rendering
- AGENT-014: Content UI
- AGENT-031: Battlecard engine
- AGENT-032: Talk track generator
- AGENT-033: Deal room

### Workflow 3: Prospect Enrichment
- AGENT-007: Enrichment service
- AGENT-004: CRM sync
- AGENT-015: Prospect UI
- AGENT-034: Meeting prep
- AGENT-036: LinkedIn integration

---

## Integration Matrix

| Integration | Agent | CRM | Transcript | Calendar | Notifications |
|-------------|-------|-----|------------|----------|---------------|
| HubSpot | 004 | ✅ | - | - | - |
| Salesforce | 038 | ✅ | - | - | - |
| Avoma | 009 | - | ✅ | - | - |
| Zoom | 039 | - | ✅ | - | - |
| Gong | 040 | - | ✅ | - | - |
| Google Calendar | 027 | - | - | ✅ | - |
| Outlook | 027 | - | - | ✅ | - |
| Slack | 037 | - | - | - | ✅ |
| LinkedIn | 036 | - | - | - | - |
| Email (SendGrid/SES) | 026 | - | - | - | ✅ |

---

## Dependency Graph

```
AGENT-001 (Project Setup)
├── AGENT-002 (Backend API)
│   ├── AGENT-004 (HubSpot)
│   │   ├── AGENT-007 (Enrichment)
│   │   └── AGENT-035 (Follow-up)
│   ├── AGENT-005 (Transcript SPICED)
│   │   ├── AGENT-009 (Avoma)
│   │   ├── AGENT-010 (Coaching)
│   │   ├── AGENT-034 (Meeting Prep)
│   │   ├── AGENT-039 (Zoom)
│   │   └── AGENT-040 (Gong)
│   ├── AGENT-006 (Content Generator)
│   │   ├── AGENT-008 (Rendering)
│   │   └── AGENT-031 (Battlecards)
│   ├── AGENT-011 (Data Models)
│   │   ├── AGENT-012 (Auth)
│   │   ├── AGENT-022 (Notifications)
│   │   ├── AGENT-023 (File Upload)
│   │   ├── AGENT-024 (Search)
│   │   ├── AGENT-025 (Activity Log)
│   │   ├── AGENT-026 (Email)
│   │   ├── AGENT-028 (Team Mgmt)
│   │   ├── AGENT-030 (Export/Import)
│   │   ├── AGENT-031 (Battlecards)
│   │   └── AGENT-038 (Salesforce)
│   ├── AGENT-017 (Claude Prompts)
│   │   └── AGENT-032 (Talk Tracks)
│   └── AGENT-027 (Calendar)
│       └── AGENT-034 (Meeting Prep)
│
└── AGENT-003 (Frontend Scaffold)
    ├── AGENT-013 (Transcript UI)
    ├── AGENT-014 (Content UI)
    ├── AGENT-015 (Prospect UI)
    ├── AGENT-016 (Coaching UI)
    ├── AGENT-018 (Dashboard)
    │   └── AGENT-029 (Analytics)
    ├── AGENT-021 (Settings)
    └── AGENT-033 (Deal Room)

Cross-dependencies:
- AGENT-012 → 002, 003, 011
- AGENT-019 → 002, 003
- AGENT-020 → 002, 003, 005, 006, 007
- AGENT-036 → 002, 007, 012
- AGENT-037 → 002, 012, 022
```

---

## Agent Protocol

Each agent must:
1. Create the specified branch from `main` (or dependency branch)
2. Only modify files/folders listed in spec
3. Commit with success/failure status
4. Not conflict with parallel agents

## Status Key
- ✅ Complete
- 🔄 In Progress
- ⏳ Pending
- ❌ Failed
