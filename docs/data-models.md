# Sales OS Data Models Documentation

This document provides comprehensive documentation for all data models, database schemas, and shared types used in Sales OS.

## Overview

Sales OS uses a PostgreSQL database with SQLAlchemy ORM for data persistence. All models follow these conventions:

- **UUID Primary Keys**: All entities use UUID v4 as primary keys
- **Timestamps**: All entities include `created_at` and `updated_at` timestamps
- **Soft Deletes**: Key entities support soft deletion via `deleted_at` field
- **Pydantic Validation**: All API inputs/outputs are validated using Pydantic v2

## Entity Relationship Diagram

```
+----------------+       +----------------+       +----------------+
|  Organization  |<----->|      Team      |<----->|      User      |
+----------------+       +----------------+       +----------------+
        |                                                 |
        |                                                 |
        v                                                 v
+----------------+                               +----------------+
|HubSpotIntegr.  |                               |      Call      |
+----------------+                               +----------------+
                                                        |
                    +-----------------------------------+
                    |                   |               |
                    v                   v               v
            +----------------+   +----------------+   +----------------+
            |   Transcript   |   |SPICEDAnalysis  |   |CoachingReport  |
            +----------------+   +----------------+   +----------------+
                                                              |
                                                              v
                                                      +----------------+
                                                      | CoachingScore  |
                                                      +----------------+

+----------------+       +----------------+       +----------------+
|    Company     |<----->|    Prospect    |<----->|    Content     |
+----------------+       +----------------+       +----------------+
                                                         |
                                                         v
                                                 +----------------+
                                                 |ContentTemplate |
                                                 +----------------+
```

## Core Entities

### User Management

#### Organization

Represents a company using Sales OS.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | Organization name |
| industry | String(100) | Industry sector |
| size | String(50) | Company size category |
| domain | String(255) | Primary domain (unique) |
| logo_url | String(500) | URL to organization logo |
| settings | JSON | Organization settings |
| hubspot_api_key | String(500) | HubSpot API key (encrypted) |
| claude_api_key | String(500) | Claude API key (encrypted) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| deleted_at | DateTime | Soft delete timestamp |

**Relationships:**
- Has many Teams
- Has many Users
- Has one HubSpotIntegration

#### Team

Organizes users within an organization.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | Team name |
| description | Text | Team description |
| organization_id | UUID FK | Parent organization |
| manager_id | UUID FK | Team manager (User) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| deleted_at | DateTime | Soft delete timestamp |

**Relationships:**
- Belongs to Organization
- Has many Users (members)
- Has one User (manager)

#### User

Individual user account.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| email | String(255) | Email address (unique) |
| password_hash | String(255) | Hashed password |
| first_name | String(100) | First name |
| last_name | String(100) | Last name |
| role | Enum | admin, manager, sales_rep, viewer |
| is_active | Boolean | Account active status |
| is_verified | Boolean | Email verified status |
| avatar_url | String(500) | Profile picture URL |
| phone | String(50) | Phone number |
| timezone | String(50) | User timezone |
| last_login_at | DateTime | Last login timestamp |
| organization_id | UUID FK | Parent organization |
| team_id | UUID FK | Assigned team |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| deleted_at | DateTime | Soft delete timestamp |

**Relationships:**
- Belongs to Organization
- Belongs to Team
- Has many Calls
- Has many Content items
- Has many CoachingReports

---

### Call & Transcript

#### Call

Represents a sales call.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| title | String(500) | Call title |
| source | Enum | zoom, teams, avoma, manual_upload, etc. |
| call_type | Enum | discovery, demo, negotiation, closing, etc. |
| status | Enum | pending, processing, transcribed, analyzed, failed |
| scheduled_at | DateTime | Scheduled time |
| started_at | DateTime | Actual start time |
| ended_at | DateTime | End time |
| duration_seconds | Integer | Call duration |
| recording_url | String(1000) | URL to recording |
| external_id | String(255) | External system ID |
| participants | JSON | List of participants |
| user_id | UUID FK | Call owner |
| prospect_id | UUID FK | Related prospect |
| company_id | UUID FK | Related company |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| deleted_at | DateTime | Soft delete timestamp |

**Relationships:**
- Belongs to User
- Belongs to Prospect (optional)
- Belongs to Company (optional)
- Has one Transcript
- Has one SPICEDAnalysis
- Has many CoachingReports

#### Transcript

Call transcription data.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| raw_text | Text | Raw transcript text |
| structured_text | JSON | Structured transcript with speaker labels |
| language | String(10) | Language code (e.g., "en") |
| word_count | Integer | Total word count |
| confidence_score | Float | Transcription confidence (0-1) |
| transcription_service | String(100) | Service used for transcription |
| processed_at | DateTime | Processing completion time |
| call_id | UUID FK | Parent call (unique) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- Belongs to Call (one-to-one)

---

### SPICED Analysis

#### SPICEDAnalysis

SPICED methodology analysis based on Winning by Design framework.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| situation | Text | S - Current state and context |
| pain | Text | P - Key challenges and problems |
| impact | Text | I - Business impact of the pain |
| critical_event | Text | C - Timeline drivers and urgency |
| expected_decision | Text | E - Decision process |
| decision_criteria | Text | D - Decision factors |
| situation_score | Integer(1-5) | Score for Situation |
| pain_score | Integer(1-5) | Score for Pain |
| impact_score | Integer(1-5) | Score for Impact |
| critical_event_score | Integer(1-5) | Score for Critical Event |
| expected_decision_score | Integer(1-5) | Score for Expected Decision |
| decision_criteria_score | Integer(1-5) | Score for Decision Criteria |
| overall_score | Float | Average SPICED score |
| confidence_score | Float | Analysis confidence (0-1) |
| call_summary | Text | Brief call summary |
| call_notes | Text | Detailed call notes |
| follow_up_tasks | JSON | Recommended follow-up tasks |
| key_quotes | JSON | Important quotes from prospect |
| action_items | JSON | Action items identified |
| gaps_identified | JSON | Gaps in discovery |
| recommended_questions | JSON | Questions for follow-up |
| model_version | String(50) | AI model version used |
| analyzed_at | DateTime | Analysis completion time |
| call_id | UUID FK | Parent call (unique) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- Belongs to Call (one-to-one)

---

### Content Generation

#### ContentTemplate

Templates for content generation.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | Template name |
| description | Text | Template description |
| content_type | Enum | sales_deck, proposal, one_pager, battlecard, etc. |
| template_structure | JSON | Template structure definition |
| brand_guidelines | JSON | Brand styling guidelines |
| color_scheme | JSON | Color palette |
| font_family | String(100) | Primary font |
| is_default | Boolean | Default template flag |
| is_public | Boolean | Publicly available flag |
| version | Integer | Template version |
| usage_count | Integer | Times used |
| organization_id | UUID FK | Owner organization |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| deleted_at | DateTime | Soft delete timestamp |

**Relationships:**
- Belongs to Organization (optional)
- Has many Content items

#### Content

Generated sales content.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| title | String(500) | Content title |
| content_type | Enum | Type of content |
| status | Enum | draft, generating, generated, approved, etc. |
| goal | Text | Purpose of the content |
| product_info | JSON | Product information input |
| audience_info | JSON | Target audience metadata |
| additional_context | Text | Additional context |
| content_data | JSON | Generated content structure |
| rendered_html | Text | Rendered HTML output |
| rendered_pdf_url | String(1000) | PDF download URL |
| rendered_pptx_url | String(1000) | PowerPoint download URL |
| version | Integer | Content version |
| parent_id | UUID FK | Parent content (for revisions) |
| tags | JSON | Content tags |
| generated_at | DateTime | Generation timestamp |
| model_version | String(50) | AI model version used |
| created_by_id | UUID FK | Creator user |
| template_id | UUID FK | Template used |
| prospect_id | UUID FK | Target prospect |
| company_id | UUID FK | Target company |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| deleted_at | DateTime | Soft delete timestamp |

**Relationships:**
- Belongs to User (created_by)
- Belongs to ContentTemplate (optional)
- Belongs to Prospect (optional)
- Belongs to Company (optional)
- Has many Content (revisions)

---

### Prospect & Company

#### Company

Prospect organization data.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | Company name |
| domain | String(255) | Primary domain (unique) |
| website | String(500) | Website URL |
| industry | String(100) | Industry sector |
| sub_industry | String(100) | Sub-industry |
| size | Enum | startup, small, medium, large, enterprise |
| employee_count | Integer | Number of employees |
| annual_revenue | Float | Annual revenue |
| funding_stage | Enum | bootstrapped, seed, series_a, etc. |
| total_funding | Float | Total funding raised |
| founded_year | Integer | Year founded |
| headquarters_city | String(100) | HQ city |
| headquarters_state | String(100) | HQ state |
| headquarters_country | String(100) | HQ country |
| description | Text | Company description |
| tagline | String(500) | Company tagline |
| logo_url | String(500) | Logo URL |
| tech_stack | JSON | Technologies used |
| tools_used | JSON | Tools and software |
| linkedin_url | String(500) | LinkedIn page URL |
| twitter_handle | String(100) | Twitter handle |
| crunchbase_url | String(500) | Crunchbase URL |
| enrichment_data | JSON | Raw enrichment data |
| recent_news | JSON | Recent news articles |
| recent_events | JSON | Recent company events |
| key_initiatives | JSON | Strategic initiatives |
| is_verified | Boolean | Data verification status |
| last_enriched_at | DateTime | Last enrichment time |
| hubspot_id | String(100) | HubSpot company ID |
| salesforce_id | String(100) | Salesforce account ID |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| deleted_at | DateTime | Soft delete timestamp |

**Relationships:**
- Has many Prospects
- Has many Calls
- Has many Content items

#### Prospect

Individual contact/lead.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| first_name | String(100) | First name |
| last_name | String(100) | Last name |
| email | String(255) | Email address |
| phone | String(50) | Phone number |
| mobile | String(50) | Mobile number |
| title | String(255) | Job title |
| department | String(100) | Department |
| seniority | String(50) | Seniority level |
| status | Enum | new, contacted, engaged, qualified, etc. |
| lead_score | Integer | Lead score (0-100) |
| linkedin_url | String(500) | LinkedIn profile URL |
| twitter_handle | String(100) | Twitter handle |
| avatar_url | String(500) | Profile picture URL |
| enrichment_data | JSON | Raw enrichment data |
| work_history | JSON | Work experience |
| education | JSON | Education history |
| interests | JSON | Interests and topics |
| recent_posts | JSON | Recent social posts |
| notes | Text | Internal notes |
| pain_points | JSON | Identified pain points |
| goals | JSON | Identified goals |
| is_verified | Boolean | Data verification status |
| last_enriched_at | DateTime | Last enrichment time |
| last_contacted_at | DateTime | Last contact time |
| hubspot_id | String(100) | HubSpot contact ID |
| salesforce_id | String(100) | Salesforce contact ID |
| company_id | UUID FK | Associated company |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| deleted_at | DateTime | Soft delete timestamp |

**Relationships:**
- Belongs to Company (optional)
- Has many Calls
- Has many Content items

---

### Coaching

#### CoachingReport

Comprehensive coaching report for a sales call.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| overall_score | Float | Overall score (1-5) |
| level | Enum | needs_improvement, developing, proficient, advanced, expert |
| confidence_score | Float | Analysis confidence (0-1) |
| executive_summary | Text | Brief summary |
| key_strengths | JSON | Identified strengths |
| key_improvements | JSON | Areas for improvement |
| wbd_methodology_alignment | Float | WbD alignment score (0-1) |
| wbd_feedback | Text | WbD-specific feedback |
| action_items | JSON | Recommended actions |
| learning_resources | JSON | Suggested resources |
| practice_scenarios | JSON | Practice scenarios |
| improvement_areas | JSON | Trending improvements |
| regression_areas | JSON | Trending regressions |
| trend_summary | Text | Performance trend summary |
| model_version | String(50) | AI model version used |
| analyzed_at | DateTime | Analysis timestamp |
| call_id | UUID FK | Analyzed call |
| user_id | UUID FK | User being coached |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- Belongs to Call
- Belongs to User
- Has many CoachingScores

#### CoachingScore

Individual SPICED component scores.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| component | String(1) | SPICED component (S, P, I, C, E, D) |
| score | Integer(1-5) | Component score |
| feedback | Text | Detailed feedback |
| strengths | JSON | Component strengths |
| areas_for_improvement | JSON | Improvement areas |
| evidence_quotes | JSON | Supporting quotes |
| missed_opportunities | JSON | Missed opportunities |
| recommended_questions | JSON | Suggested questions |
| best_practices | JSON | Best practices |
| coaching_report_id | UUID FK | Parent report |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- Belongs to CoachingReport

---

### Integrations

#### HubSpotIntegration

HubSpot OAuth2 integration.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| access_token | String(500) | OAuth2 access token (encrypted) |
| refresh_token | String(500) | OAuth2 refresh token (encrypted) |
| token_expires_at | DateTime | Token expiration time |
| scopes | JSON | Granted scopes |
| hub_id | String(100) | HubSpot portal ID |
| hub_domain | String(255) | HubSpot domain |
| hub_name | String(255) | HubSpot account name |
| is_active | Boolean | Integration active status |
| last_sync_at | DateTime | Last sync timestamp |
| last_sync_status | String(50) | Last sync status |
| last_sync_error | Text | Last sync error |
| contacts_synced | Integer | Total contacts synced |
| companies_synced | Integer | Total companies synced |
| deals_synced | Integer | Total deals synced |
| contact_field_mapping | JSON | Contact field mapping |
| company_field_mapping | JSON | Company field mapping |
| deal_field_mapping | JSON | Deal field mapping |
| organization_id | UUID FK | Owner organization (unique) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- Belongs to Organization (one-to-one)

---

## Enumerations

### User Roles
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"
```

### Call Sources
```python
class CallSource(str, Enum):
    ZOOM = "zoom"
    TEAMS = "teams"
    GOOGLE_MEET = "google_meet"
    AVOMA = "avoma"
    GONG = "gong"
    CHORUS = "chorus"
    MANUAL_UPLOAD = "manual_upload"
    OTHER = "other"
```

### Call Types
```python
class CallType(str, Enum):
    DISCOVERY = "discovery"
    DEMO = "demo"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"
    CHECK_IN = "check_in"
    KICKOFF = "kickoff"
    OTHER = "other"
```

### Content Types
```python
class ContentType(str, Enum):
    SALES_DECK = "sales_deck"
    PROPOSAL = "proposal"
    ONE_PAGER = "one_pager"
    BATTLECARD = "battlecard"
    CASE_STUDY = "case_study"
    EMAIL_SEQUENCE = "email_sequence"
    FOLLOW_UP_EMAIL = "follow_up_email"
    EXECUTIVE_SUMMARY = "executive_summary"
    ROI_CALCULATOR = "roi_calculator"
    OTHER = "other"
```

### Prospect Status
```python
class ProspectStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    CHURNED = "churned"
```

### Coaching Levels
```python
class CoachingLevel(str, Enum):
    NEEDS_IMPROVEMENT = "needs_improvement"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"
    EXPERT = "expert"
```

---

## Database Migrations

Migrations are managed using Alembic. The initial migration creates all tables with proper foreign key constraints and indexes.

### Running Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Rollback last migration
alembic downgrade -1
```

### Migration Files Location

- Configuration: `/backend/alembic.ini`
- Migration scripts: `/backend/alembic/versions/`

---

## Pydantic Schemas

All API request/response validation is handled by Pydantic v2 schemas located in `/backend/app/schemas/`.

### Schema Organization

- `base.py` - Base schemas and utilities
- `user.py` - User, Team, Organization schemas
- `transcript.py` - Call and Transcript schemas
- `spiced.py` - SPICED Analysis schemas
- `content.py` - Content and Template schemas
- `prospect.py` - Prospect and Company schemas
- `coaching.py` - Coaching Report and Score schemas

### Common Patterns

```python
# Base schema with Pydantic configuration
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

# Create schema (for POST requests)
class EntityCreate(EntityBase):
    required_field: str

# Update schema (for PATCH requests)
class EntityUpdate(BaseSchema):
    optional_field: Optional[str] = None

# Response schema (for API responses)
class EntityResponse(EntityBase, IDSchema, TimestampSchema):
    pass
```

---

## JSON Schema Files

JSON Schema definitions are available in `/data/schemas/` for:
- External validation
- Documentation generation
- Frontend form validation
- API contract definition

All schemas follow JSON Schema Draft 2020-12 specification.
