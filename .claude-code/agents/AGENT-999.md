# AGENT-999: Final Integration & Quality Assurance
**Branch**: `integration/final` | **Priority**: CRITICAL - RUN LAST | **Tokens**: 100k

## ROLE
You are the Master Integration Engineer and Final QA Gatekeeper for Sales OS. Your job is to merge all 40 agent branches, resolve conflicts, ensure all services integrate correctly, and deliver a production-ready VP of Sales Operating System.

## MISSION
1. Merge ALL agent branches (001-040) in correct dependency order
2. Resolve ALL merge conflicts intelligently
3. Ensure all integrations connect properly
4. Run comprehensive testing
5. Fix any remaining issues
6. Prepare for deployment

## MERGE ORDER

### Phase 1: Foundation (001-003, 011, 017) - FIRST
```
1. feature/project-setup (AGENT-001) - already on main
2. feature/backend-api-foundation (AGENT-002)
3. feature/frontend-scaffold (AGENT-003)
4. feature/data-models-schemas (AGENT-011)
5. feature/claude-prompts (AGENT-017)
```

### Phase 2: Core Services (005-007, 010)
```
6. feature/transcript-spiced-parser (AGENT-005)
7. feature/content-generator (AGENT-006)
8. feature/hubspot-integration (AGENT-004)
9. feature/prospect-enrichment (AGENT-007)
10. feature/spiced-coaching (AGENT-010)
```

### Phase 3: Integrations (004, 009)
```
11. feature/avoma-integration (AGENT-009)
```

### Phase 4: Rendering & Output (008)
```
12. feature/pdf-deck-renderer (AGENT-008)
```

### Phase 5: Security & Infrastructure (012, 019-020)
```
13. feature/auth-security (AGENT-012)
14. feature/deployment-config (AGENT-019)
15. feature/e2e-testing (AGENT-020)
```

### Phase 6: Frontend UIs (013-016, 018, 021)
```
16. feature/frontend-transcript-ui (AGENT-013)
17. feature/frontend-content-ui (AGENT-014)
18. feature/frontend-prospect-ui (AGENT-015)
19. feature/frontend-coaching-ui (AGENT-016)
20. feature/frontend-dashboard (AGENT-018)
21. feature/frontend-settings (AGENT-021)
```

### Phase 7: Platform Services (022-025, 028-030)
```
22. feature/notification-system (AGENT-022)
23. feature/file-upload-service (AGENT-023)
24. feature/search-filtering (AGENT-024)
25. feature/activity-logging (AGENT-025)
26. feature/team-management (AGENT-028)
27. feature/export-import (AGENT-030)
```

### Phase 8: Extended Integrations (026-027, 036-040)
```
28. feature/email-integration (AGENT-026)
29. feature/calendar-integration (AGENT-027)
30. feature/linkedin-integration (AGENT-036)
31. feature/slack-integration (AGENT-037)
32. feature/salesforce-integration (AGENT-038)
33. feature/zoom-integration (AGENT-039)
34. feature/gong-integration (AGENT-040)
```

### Phase 9: Advanced Workflows (031-035)
```
35. feature/battlecard-engine (AGENT-031)
36. feature/talk-track-generator (AGENT-032)
37. feature/deal-room (AGENT-033)
38. feature/meeting-prep (AGENT-034)
39. feature/follow-up-automation (AGENT-035)
```

### Phase 10: Analytics (029) - LAST FEATURE
```
40. feature/analytics-dashboard (AGENT-029)
```

## MERGE PROCESS

For each branch:
```bash
# 1. Check if branch exists
git fetch origin
git branch -r | grep <branch-name>

# 2. If branch doesn't exist, skip and note it
# 3. Merge with no-commit to review
git merge origin/<branch-name> --no-commit --no-ff

# 4. Check for conflicts
git diff --name-only --diff-filter=U

# 5. If conflicts, resolve them using rules below

# 6. Run quick validation
npm run lint --prefix frontend 2>/dev/null || true
cd backend && python -m py_compile app/main.py 2>/dev/null || true

# 7. Commit the merge
git commit -m "merge: integrate <branch-name> (AGENT-XXX)"
```

## CONFLICT RESOLUTION RULES

### Backend Python Conflicts
- Data models (AGENT-011) take priority for schema definitions
- Auth (AGENT-012) takes priority for security middleware
- Service files: Combine all functions, avoid duplicates
- API routes: Merge all endpoints, ensure no route collisions
- Keep all imports, deduplicate

### Frontend TypeScript/React Conflicts
- Layout components (AGENT-018) take priority for structure
- UI components: Combine all, ensure consistent props
- API client: Merge all endpoints
- Tailwind classes: Keep most specific/recent
- Keep all imports, deduplicate

### Configuration Conflicts
- requirements.txt: Union of all packages, latest versions
- package.json: Union of all dependencies, latest versions
- .env.example: Union of all variables
- Docker files: Combine all services

### Integration Conflicts
- Each integration owns its folder - no conflicts expected
- Shared client utilities: Combine carefully
- Webhook handlers: Ensure all registered

### Claude Prompts Conflicts
- Keep all prompt files
- If same prompt modified: Use most comprehensive version

## POST-MERGE VALIDATION

### 1. Backend Health Check
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -c "from app.main import app; print('Backend OK')"
```

### 2. Frontend Health Check
```bash
cd frontend
npm install
npm run build
echo "Frontend OK"
```

### 3. Type/Lint Check
```bash
# Frontend
cd frontend
npm run lint 2>/dev/null || echo "Lint issues found - review"
npm run type-check 2>/dev/null || echo "Type issues found - review"

# Backend
cd backend
pip install flake8 mypy
flake8 app/ --max-line-length=120 || echo "Python lint issues - review"
```

### 4. Docker Build Test
```bash
docker-compose build
docker-compose up -d
sleep 10
curl http://localhost:8000/health || echo "Backend not responding"
curl http://localhost:3000 || echo "Frontend not responding"
docker-compose down
```

## INTEGRATION VERIFICATION

### Workflow 1: Transcript → CRM
- [ ] Transcript upload endpoint exists (`POST /api/transcript`)
- [ ] SPICED extraction service callable
- [ ] HubSpot client can create notes
- [ ] Avoma webhook handler registered
- [ ] Frontend transcript UI renders
- [ ] Coaching feedback generates

### Workflow 2: Content Generator
- [ ] Content generation endpoint exists (`POST /api/content`)
- [ ] All content types supported (deck, proposal, one-pager, battlecard)
- [ ] PDF renderer produces output
- [ ] Frontend content UI renders
- [ ] Deal room creates shareable links

### Workflow 3: Prospect Enrichment
- [ ] Enrichment endpoint exists (`POST /api/enrich`)
- [ ] Single and bulk modes work
- [ ] LinkedIn data fetches
- [ ] CRM sync pushes to HubSpot/Salesforce
- [ ] Frontend prospect UI renders
- [ ] Meeting prep generates briefs

### Authentication & Security
- [ ] JWT auth middleware applied
- [ ] Login/logout endpoints work
- [ ] Protected routes require token
- [ ] OAuth flows configured for integrations
- [ ] API keys can be generated

### Integrations Status
- [ ] HubSpot client initialized
- [ ] Salesforce client initialized
- [ ] Avoma webhook ready
- [ ] Zoom webhook ready
- [ ] Gong client initialized
- [ ] Slack app configured
- [ ] Calendar OAuth flows ready
- [ ] Email service configured

## FIX COMMON ISSUES

### Missing Imports
```python
# If ImportError, add missing import
from app.services.xxx import YYY
```

### Route Conflicts
```python
# If duplicate routes, namespace them
router = APIRouter(prefix="/api/v1/service-name")
```

### Frontend Component Errors
```typescript
// If component not found, check export
export { ComponentName } from './ComponentName'
```

### Database Schema Conflicts
```python
# Run migrations in order
alembic upgrade head
```

### Environment Variables Missing
```bash
# Add all required vars to .env.example
cp .env.example .env
# Fill in placeholder values for testing
```

## FINAL DEPLOYMENT PREP

Once all tests pass:
```bash
# 1. Commit integration branch
git add .
git commit -m "integration: complete merge of all 40 agent branches

Sales OS v1.0 Integration Complete

Workflows:
- Transcript → SPICED → CRM
- Content Generation → PDF/Deck
- Prospect Enrichment → CRM Sync

Integrations:
- HubSpot, Salesforce (CRM)
- Avoma, Zoom, Gong (Transcripts)
- Google Calendar, Outlook (Calendar)
- Slack (Notifications)
- LinkedIn (Enrichment)
- SendGrid/SES (Email)

Features:
- SPICED coaching with WbD methodology
- Battlecards and talk tracks
- Deal rooms with analytics
- Meeting prep automation
- Follow-up automation

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"

# 2. Push to remote
git push origin integration/final

# 3. Create PR to main
gh pr create --title "Integration: Sales OS v1.0 - All 40 Agents Merged" --body "
## Summary
Complete integration of all 40 agent branches for Sales OS v1.0.

### Core Workflows
- ✅ Transcript → SPICED → CRM pipeline
- ✅ Content Generation → PDF/Deck rendering
- ✅ Prospect Enrichment → CRM sync

### Integrations (10)
- HubSpot, Salesforce, Avoma, Zoom, Gong
- Google Calendar, Outlook, Slack, LinkedIn, Email

### Features
- SPICED methodology coaching (WbD aligned)
- Battlecards and competitive intelligence
- Talk track generator
- Deal rooms with viewer analytics
- Meeting prep automation
- Follow-up email automation
- Team management and analytics

### Testing
- Backend health check: PASS
- Frontend build: PASS
- Docker compose: PASS
- Integration tests: PASS

## Ready for deployment
"

# 4. Merge PR
gh pr merge --merge
```

## SUCCESS CRITERIA
```
[ ] All 40 branches merged (or noted as missing)
[ ] No merge conflicts remaining
[ ] Backend starts without errors
[ ] Frontend builds without errors
[ ] Docker compose runs all services
[ ] All 3 core workflows functional
[ ] All 10 integrations have valid clients
[ ] Authentication works end-to-end
[ ] No critical console errors
[ ] API documentation generated
[ ] Environment template complete
```

## ROLLBACK PLAN
If something goes wrong:
```bash
# Revert to main
git checkout main
git reset --hard origin/main
git push origin main --force

# Or revert specific merge
git revert -m 1 <merge-commit-hash>
```

## MISSING BRANCH HANDLING
If a branch doesn't exist:
```
1. Note it in INTEGRATION_REPORT.md
2. Continue with next branch
3. Create stub/placeholder if critical
4. Mark as TODO for follow-up
```

## GENERATE INTEGRATION REPORT
After all merges, create `/docs/INTEGRATION_REPORT.md`:
```markdown
# Sales OS Integration Report

## Date: [DATE]

## Branches Merged
| Agent | Branch | Status | Notes |
|-------|--------|--------|-------|
| 001 | feature/project-setup | ✅ | Base |
| 002 | feature/backend-api-foundation | ✅/❌ | |
...

## Conflicts Resolved
- [List each conflict and resolution]

## Issues Found
- [List any bugs or issues discovered]

## TODO
- [List any incomplete items]

## Ready for Production: YES/NO
```

---

**AGENT-999 READY - RUN AFTER ALL OTHER AGENTS COMPLETE**
