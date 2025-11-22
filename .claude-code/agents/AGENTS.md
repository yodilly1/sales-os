# Sales OS Agent Manifest

## Overview
This manifest lists all Claude Code agents for the Sales OS project. Each agent owns a single feature branch and has zero conflict with other agents.

## Execution Order

### Phase 1: Foundation
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-001 | Project Setup | `feature/project-setup` | None |
| AGENT-002 | Backend API Foundation | `feature/backend-api-foundation` | 001 |
| AGENT-003 | Frontend Scaffold | `feature/frontend-scaffold` | 001 |
| AGENT-011 | Data Models & Schemas | `feature/data-models-schemas` | 002 |
| AGENT-017 | Claude Prompts Infrastructure | `feature/claude-prompts` | 002 |

### Phase 2: Core Services
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-005 | Transcript SPICED Parser | `feature/transcript-spiced-parser` | 002 |
| AGENT-006 | Content Generator | `feature/content-generator` | 002 |
| AGENT-007 | Prospect Enrichment | `feature/prospect-enrichment` | 002, 004 |
| AGENT-010 | SPICED Coaching | `feature/spiced-coaching` | 002, 005 |

### Phase 3: Integrations
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-004 | HubSpot Integration | `feature/hubspot-integration` | 002 |
| AGENT-009 | Avoma Integration | `feature/avoma-integration` | 002, 005 |

### Phase 4: Rendering & Output
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-008 | PDF/Deck Renderer | `feature/pdf-deck-renderer` | 002, 003, 006 |

### Phase 5: Frontend UIs
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-013 | Transcript UI | `feature/frontend-transcript-ui` | 003, 005 |
| AGENT-014 | Content UI | `feature/frontend-content-ui` | 003, 006, 008 |
| AGENT-015 | Prospect UI | `feature/frontend-prospect-ui` | 003, 007 |
| AGENT-016 | Coaching UI | `feature/frontend-coaching-ui` | 003, 010 |
| AGENT-018 | Dashboard | `feature/frontend-dashboard` | 003, 012 |

### Phase 6: Security & Infrastructure
| Agent | Name | Branch | Dependencies |
|-------|------|--------|--------------|
| AGENT-012 | Authentication & Security | `feature/auth-security` | 002, 003, 011 |
| AGENT-019 | Deployment Config | `feature/deployment-config` | 002, 003 |
| AGENT-020 | E2E Testing | `feature/e2e-testing` | 002, 003, 005, 006, 007 |

---

## Workflow Coverage

### Workflow 1: Transcript → CRM
- AGENT-005: SPICED extraction
- AGENT-004: HubSpot sync
- AGENT-009: Avoma ingestion
- AGENT-010: Coaching feedback
- AGENT-013: Transcript UI

### Workflow 2: Content Generator
- AGENT-006: Content generation engine
- AGENT-008: PDF/deck rendering
- AGENT-014: Content UI

### Workflow 3: Prospect Enrichment
- AGENT-007: Enrichment service
- AGENT-004: CRM sync
- AGENT-015: Prospect UI

---

## Dependency Graph

```
AGENT-001 (Project Setup)
├── AGENT-002 (Backend API)
│   ├── AGENT-004 (HubSpot)
│   │   └── AGENT-007 (Enrichment)
│   ├── AGENT-005 (Transcript SPICED)
│   │   ├── AGENT-009 (Avoma)
│   │   └── AGENT-010 (Coaching)
│   ├── AGENT-006 (Content Generator)
│   ├── AGENT-011 (Data Models)
│   │   └── AGENT-012 (Auth) ←── also depends on 002, 003
│   └── AGENT-017 (Claude Prompts)
│
└── AGENT-003 (Frontend Scaffold)
    ├── AGENT-008 (Rendering) ←── also depends on 002, 006
    ├── AGENT-013 (Transcript UI) ←── also depends on 005
    ├── AGENT-014 (Content UI) ←── also depends on 006, 008
    ├── AGENT-015 (Prospect UI) ←── also depends on 007
    ├── AGENT-016 (Coaching UI) ←── also depends on 010
    └── AGENT-018 (Dashboard) ←── also depends on 012

AGENT-019 (Deployment) ←── depends on 002, 003
AGENT-020 (E2E Testing) ←── depends on 002, 003, 005, 006, 007
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
