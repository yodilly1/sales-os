-- Sales OS Database Initialization Script
-- This runs automatically when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS integrations;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Core Tables

-- Organizations
CREATE TABLE IF NOT EXISTS core.organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Teams
CREATE TABLE IF NOT EXISTS core.teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users
CREATE TABLE IF NOT EXISTS core.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id) ON DELETE CASCADE,
    team_id UUID REFERENCES core.teams(id) ON DELETE SET NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'rep',  -- admin, manager, rep
    avatar_url TEXT,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transcripts
CREATE TABLE IF NOT EXISTS core.transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    source VARCHAR(50),  -- avoma, zoom, gong, manual
    source_id VARCHAR(255),  -- External system ID
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    duration_seconds INTEGER,
    meeting_date TIMESTAMP WITH TIME ZONE,
    participants JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SPICED Analysis
CREATE TABLE IF NOT EXISTS core.spiced_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transcript_id UUID NOT NULL REFERENCES core.transcripts(id) ON DELETE CASCADE,
    situation TEXT,
    situation_score INTEGER CHECK (situation_score BETWEEN 1 AND 5),
    pain TEXT,
    pain_score INTEGER CHECK (pain_score BETWEEN 1 AND 5),
    impact TEXT,
    impact_score INTEGER CHECK (impact_score BETWEEN 1 AND 5),
    critical_event TEXT,
    critical_event_score INTEGER CHECK (critical_event_score BETWEEN 1 AND 5),
    expected_decision TEXT,
    expected_decision_score INTEGER CHECK (expected_decision_score BETWEEN 1 AND 5),
    decision_criteria TEXT,
    decision_criteria_score INTEGER CHECK (decision_criteria_score BETWEEN 1 AND 5),
    overall_score DECIMAL(3,2),
    call_notes TEXT,
    suggested_tasks JSONB DEFAULT '[]',
    coaching_feedback TEXT,
    raw_analysis JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated Content
CREATE TABLE IF NOT EXISTS core.content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,  -- deck, proposal, one-pager, battlecard
    title VARCHAR(500) NOT NULL,
    goal TEXT,
    product_info JSONB DEFAULT '{}',
    audience TEXT,
    content_data JSONB NOT NULL,
    rendered_url TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prospects
CREATE TABLE IF NOT EXISTS core.prospects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES core.users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    title VARCHAR(255),
    phone VARCHAR(50),
    linkedin_url TEXT,
    company_id UUID,
    enrichment_data JSONB DEFAULT '{}',
    crm_id VARCHAR(255),  -- HubSpot/Salesforce ID
    crm_type VARCHAR(50),  -- hubspot, salesforce
    status VARCHAR(50) DEFAULT 'new',
    last_enriched_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Companies
CREATE TABLE IF NOT EXISTS core.companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(100),
    size VARCHAR(50),
    funding VARCHAR(100),
    description TEXT,
    tech_stack JSONB DEFAULT '[]',
    enrichment_data JSONB DEFAULT '{}',
    crm_id VARCHAR(255),
    crm_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key for prospects to companies
ALTER TABLE core.prospects
    ADD CONSTRAINT fk_prospect_company
    FOREIGN KEY (company_id) REFERENCES core.companies(id) ON DELETE SET NULL;

-- Integration Tables

-- Integration Connections
CREATE TABLE IF NOT EXISTS integrations.connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES core.users(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL,  -- hubspot, salesforce, avoma, zoom, gong, slack, etc.
    status VARCHAR(50) DEFAULT 'active',
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, provider)
);

-- Sync Log
CREATE TABLE IF NOT EXISTS integrations.sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL REFERENCES integrations.connections(id) ON DELETE CASCADE,
    sync_type VARCHAR(50),  -- full, incremental
    status VARCHAR(50),  -- started, completed, failed
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Analytics Tables

-- Activity Log
CREATE TABLE IF NOT EXISTS analytics.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES core.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Coaching Scores (for trending)
CREATE TABLE IF NOT EXISTS analytics.coaching_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    transcript_id UUID NOT NULL REFERENCES core.transcripts(id) ON DELETE CASCADE,
    overall_score DECIMAL(3,2),
    situation_score INTEGER,
    pain_score INTEGER,
    impact_score INTEGER,
    critical_event_score INTEGER,
    expected_decision_score INTEGER,
    decision_criteria_score INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_org ON core.users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON core.users(email);
CREATE INDEX IF NOT EXISTS idx_transcripts_org ON core.transcripts(organization_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_user ON core.transcripts(user_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_status ON core.transcripts(status);
CREATE INDEX IF NOT EXISTS idx_content_org ON core.content(organization_id);
CREATE INDEX IF NOT EXISTS idx_prospects_org ON core.prospects(organization_id);
CREATE INDEX IF NOT EXISTS idx_prospects_email ON core.prospects(email);
CREATE INDEX IF NOT EXISTS idx_companies_org ON core.companies(organization_id);
CREATE INDEX IF NOT EXISTS idx_companies_domain ON core.companies(domain);
CREATE INDEX IF NOT EXISTS idx_activity_org ON analytics.activity_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_activity_user ON analytics.activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_created ON analytics.activity_log(created_at);

-- Full text search indexes
CREATE INDEX IF NOT EXISTS idx_transcripts_content_search ON core.transcripts USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_prospects_name_search ON core.prospects USING gin((first_name || ' ' || last_name) gin_trgm_ops);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON core.organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON core.teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON core.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_transcripts_updated_at BEFORE UPDATE ON core.transcripts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_updated_at BEFORE UPDATE ON core.content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_prospects_updated_at BEFORE UPDATE ON core.prospects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON core.companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_connections_updated_at BEFORE UPDATE ON integrations.connections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default organization for development
INSERT INTO core.organizations (id, name, slug)
VALUES ('00000000-0000-0000-0000-000000000001', 'Development Org', 'dev')
ON CONFLICT (slug) DO NOTHING;

-- Insert default admin user (password: admin123)
INSERT INTO core.users (id, organization_id, email, password_hash, first_name, last_name, role)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'admin@salesos.dev',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYg1C1C1C1C1',  -- admin123
    'Admin',
    'User',
    'admin'
)
ON CONFLICT (email) DO NOTHING;

COMMENT ON SCHEMA core IS 'Core application tables';
COMMENT ON SCHEMA integrations IS 'External integration connections and sync logs';
COMMENT ON SCHEMA analytics IS 'Analytics and activity tracking';
