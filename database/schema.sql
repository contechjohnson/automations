-- =============================================================================
-- AUTOMATIONS REGISTRY SCHEMA
-- Run this in Supabase SQL Editor
-- =============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- CLIENTS TABLE
-- Who you're building automations for
-- =============================================================================
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,  -- "span-construction"
    name VARCHAR(255) NOT NULL,          -- "Span Construction"
    
    -- ICP Classification
    icp_type VARCHAR(50) NOT NULL,       -- "gc", "trades", "developer", "broker"
    industry VARCHAR(100),               -- "data_center_electrical"
    
    -- Targeting
    target_geography JSONB DEFAULT '{}', -- {states: ["VA", "TX"], regions: [...]}
    target_signals JSONB DEFAULT '[]',   -- ["permits", "interconnections", "jobs"]
    target_personas JSONB DEFAULT '[]',  -- ["Pre-Construction Director", ...]
    
    -- Config
    config JSONB DEFAULT '{}',           -- Client-specific settings
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, paused, churned
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

-- =============================================================================
-- AUTOMATIONS TABLE
-- The main registry - every automation you build
-- =============================================================================
CREATE TABLE automations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(200) UNIQUE NOT NULL,   -- "maricopa-az-permits", "ferc-pjm-queue"
    name VARCHAR(255) NOT NULL,          -- "Maricopa County AZ Building Permits"
    description TEXT,                    -- What this automation does
    
    -- Classification
    type VARCHAR(50) NOT NULL,           -- "scraper", "enrichment", "research", "workflow", "notification"
    category VARCHAR(100),               -- "permits", "llc_filings", "job_postings", "utility_filings"
    template VARCHAR(100),               -- "arcgis_permits", "state_portal", "public_api"
    
    -- Geography (for location-based automations)
    geography JSONB DEFAULT '{}',        -- {country: "US", state: "AZ", county: "Maricopa", city: null}
    
    -- ICP Targeting (who benefits from this data)
    icp_types TEXT[] DEFAULT '{}',       -- ["gc", "trades", "developer"]
    signal_types TEXT[] DEFAULT '{}',    -- ["building_permit", "site_plan", "commercial"]
    
    -- Client Assignment (optional - some automations serve multiple clients)
    client_id UUID REFERENCES clients(id),
    
    -- Technical Config
    worker_path VARCHAR(255),            -- "workers/templates/arcgis_permits.py"
    config JSONB DEFAULT '{}',           -- Template-specific config (endpoints, filters, etc.)
    schedule VARCHAR(50),                -- Cron expression: "0 2 * * *" (daily 2am)
    timeout_seconds INT DEFAULT 900,     -- 15 min default
    
    -- Runtime Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, active, paused, deprecated, broken
    last_run_at TIMESTAMPTZ,
    last_run_status VARCHAR(50),         -- success, failed, timeout
    last_run_result JSONB,               -- Summary of last run
    run_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    fail_count INT DEFAULT 0,
    
    -- Quality/Priority
    priority INT DEFAULT 50,             -- 1-100, higher = more important
    data_quality VARCHAR(20),            -- "high", "medium", "low"
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',            -- Freeform tags for searching
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    notes TEXT
);

-- =============================================================================
-- AUTOMATION RUNS TABLE
-- History of every run (for debugging, analytics)
-- =============================================================================
CREATE TABLE automation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    automation_id UUID REFERENCES automations(id) ON DELETE CASCADE,
    
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds FLOAT,
    
    -- Status
    status VARCHAR(50) NOT NULL,         -- queued, running, success, failed, timeout
    
    -- Results
    records_found INT,
    records_new INT,
    records_updated INT,
    
    -- Errors
    error_message TEXT,
    error_traceback TEXT,
    
    -- Cost
    cost_usd DECIMAL(10, 4),
    api_calls INT,
    
    -- Full result (optional - can be large)
    result JSONB,
    
    -- RQ Job ID (for linking to queue system)
    rq_job_id VARCHAR(100)
);

-- =============================================================================
-- TEMPLATES TABLE
-- Available templates that automations can use
-- =============================================================================
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,   -- "arcgis_permits"
    name VARCHAR(255) NOT NULL,          -- "ArcGIS Permit Scraper"
    description TEXT,
    
    -- Classification
    type VARCHAR(50) NOT NULL,           -- "scraper", "enrichment", etc.
    category VARCHAR(100),               -- "permits", "utility", etc.
    
    -- Technical
    worker_path VARCHAR(255) NOT NULL,   -- "workers/templates/arcgis_permits.py"
    config_schema JSONB,                 -- JSON Schema for config validation
    
    -- Capabilities
    supports_geography BOOLEAN DEFAULT TRUE,
    supports_scheduling BOOLEAN DEFAULT TRUE,
    estimated_runtime_seconds INT,
    estimated_cost_usd DECIMAL(10, 4),
    
    -- Usage
    automation_count INT DEFAULT 0,      -- How many automations use this
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

-- =============================================================================
-- INDEXES for fast querying
-- =============================================================================

-- Automations
CREATE INDEX idx_automations_type ON automations(type);
CREATE INDEX idx_automations_category ON automations(category);
CREATE INDEX idx_automations_template ON automations(template);
CREATE INDEX idx_automations_status ON automations(status);
CREATE INDEX idx_automations_client ON automations(client_id);
CREATE INDEX idx_automations_geography ON automations USING GIN(geography);
CREATE INDEX idx_automations_icp_types ON automations USING GIN(icp_types);
CREATE INDEX idx_automations_tags ON automations USING GIN(tags);

-- Runs
CREATE INDEX idx_runs_automation ON automation_runs(automation_id);
CREATE INDEX idx_runs_status ON automation_runs(status);
CREATE INDEX idx_runs_started ON automation_runs(started_at DESC);

-- =============================================================================
-- VIEWS for common queries
-- =============================================================================

-- All active scrapers with their last run status
CREATE VIEW v_active_scrapers AS
SELECT 
    a.slug,
    a.name,
    a.category,
    a.template,
    a.geography->>'state' as state,
    a.geography->>'county' as county,
    a.icp_types,
    a.status,
    a.last_run_at,
    a.last_run_status,
    a.run_count,
    a.success_count,
    c.name as client_name
FROM automations a
LEFT JOIN clients c ON a.client_id = c.id
WHERE a.type = 'scraper' AND a.status = 'active';

-- Automations by state (for geographic queries)
CREATE VIEW v_automations_by_state AS
SELECT 
    geography->>'state' as state,
    COUNT(*) as automation_count,
    COUNT(*) FILTER (WHERE status = 'active') as active_count,
    array_agg(DISTINCT category) as categories
FROM automations
WHERE geography->>'state' IS NOT NULL
GROUP BY geography->>'state'
ORDER BY automation_count DESC;

-- Failed automations (need attention)
CREATE VIEW v_failed_automations AS
SELECT 
    a.slug,
    a.name,
    a.last_run_at,
    a.last_run_status,
    r.error_message,
    a.fail_count
FROM automations a
LEFT JOIN automation_runs r ON r.automation_id = a.id 
    AND r.started_at = a.last_run_at
WHERE a.last_run_status = 'failed'
ORDER BY a.last_run_at DESC;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Update automation stats after a run
CREATE OR REPLACE FUNCTION update_automation_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE automations SET
        last_run_at = NEW.started_at,
        last_run_status = NEW.status,
        last_run_result = NEW.result,
        run_count = run_count + 1,
        success_count = success_count + CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
        fail_count = fail_count + CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
        updated_at = NOW()
    WHERE id = NEW.automation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_automation_stats
AFTER INSERT ON automation_runs
FOR EACH ROW
EXECUTE FUNCTION update_automation_stats();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_automations_updated
BEFORE UPDATE ON automations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_clients_updated
BEFORE UPDATE ON clients
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- SEED DATA: Templates
-- =============================================================================

INSERT INTO templates (slug, name, description, type, category, worker_path, config_schema) VALUES
('arcgis_permits', 'ArcGIS Permit Scraper', 
 'Scrapes building permits from ArcGIS-based permit systems. Supports 750+ jurisdictions using Accela/Tyler backends. Includes 2-hop parcel enrichment.',
 'scraper', 'permits', 'workers/templates/arcgis_permits.py',
 '{"type": "object", "properties": {"permit_endpoint": {"type": "string"}, "parcel_endpoint": {"type": "string"}, "case_types": {"type": "array"}, "min_date": {"type": "string"}, "keywords": {"type": "array"}}}'
),

('state_portal', 'State Portal Scraper',
 'Scrapes state government portals using Firecrawl. For CON applications, licensing boards, mining commissions, etc.',
 'scraper', 'regulatory', 'workers/templates/state_portal.py',
 '{"type": "object", "properties": {"portal_url": {"type": "string"}, "extraction_schema": {"type": "object"}, "pagination": {"type": "object"}}}'
),

('public_api', 'Public API Scraper',
 'Fetches data from public APIs like FERC, SAM.gov, SAMHSA, USAspending. No scraping needed.',
 'scraper', 'regulatory', 'workers/templates/public_api.py',
 '{"type": "object", "properties": {"api_endpoint": {"type": "string"}, "auth": {"type": "object"}, "query_params": {"type": "object"}, "field_mapping": {"type": "object"}}}'
),

('job_board', 'Job Board Scraper',
 'Scrapes job postings from LinkedIn, Indeed, etc. using Apify actors.',
 'scraper', 'jobs', 'workers/templates/job_board.py',
 '{"type": "object", "properties": {"platform": {"type": "string"}, "search_terms": {"type": "array"}, "locations": {"type": "array"}}}'
),

('google_maps', 'Google Maps Scraper',
 'Scrapes business listings from Google Maps. For facility discovery, vendor mapping.',
 'scraper', 'business', 'workers/templates/google_maps.py',
 '{"type": "object", "properties": {"categories": {"type": "array"}, "locations": {"type": "array"}, "filters": {"type": "object"}}}'
),

('entity_research', 'Entity Research',
 'Deep investigative research on companies using OpenAI o4-mini-deep-research. Finds corporate structure, domains, key people.',
 'research', 'intelligence', 'workers/research/entity_research.py',
 '{"type": "object", "properties": {"client_info": {"type": "string"}, "target_info": {"type": "string"}}}'
),

('lead_enrichment', 'Lead Enrichment',
 'Enriches leads with contact info, company data, and AI-generated icebreakers.',
 'enrichment', 'contacts', 'workers/enrichment/lead_enrichment.py',
 '{"type": "object", "properties": {"leads": {"type": "array"}, "enrich_contacts": {"type": "boolean"}, "generate_icebreakers": {"type": "boolean"}}}'
);

-- =============================================================================
-- EXAMPLE DATA: A few automations to show the pattern
-- =============================================================================

INSERT INTO automations (slug, name, description, type, category, template, geography, icp_types, signal_types, worker_path, config, status, tags) VALUES

('maricopa-az-permits', 
 'Maricopa County AZ Building Permits',
 'Commercial building permits from Maricopa County. Includes parcel enrichment for owner info.',
 'scraper', 'permits', 'arcgis_permits',
 '{"country": "US", "state": "AZ", "county": "Maricopa", "city": null}',
 ARRAY['gc', 'trades', 'developer'],
 ARRAY['building_permit', 'commercial', 'industrial'],
 'workers/templates/arcgis_permits.py',
 '{"permit_endpoint": "https://gis.maricopa.gov/...", "parcel_endpoint": "https://gis.maricopa.gov/...", "case_types": ["Building Commercial", "Site Development"], "keywords": ["INDUSTRIAL", "WAREHOUSE", "DATA CENTER"]}',
 'active',
 ARRAY['permits', 'arizona', 'data-centers']
),

('ferc-pjm-interconnection',
 'FERC PJM Interconnection Queue',
 'Utility interconnection applications in PJM region. 50MW+ often indicates data centers.',
 'scraper', 'utility', 'public_api',
 '{"country": "US", "region": "PJM"}',
 ARRAY['developer', 'gc'],
 ARRAY['interconnection', 'utility', 'data_center'],
 'workers/templates/public_api.py',
 '{"api_endpoint": "https://www.eia.gov/...", "query_params": {"region": "PJM", "min_capacity_mw": 50}}',
 'active',
 ARRAY['utility', 'ferc', 'data-centers', 'early-signal']
),

('loudoun-va-permits',
 'Loudoun County VA Building Permits',
 'Commercial permits in Loudoun County - the data center capital of the US.',
 'scraper', 'permits', 'arcgis_permits',
 '{"country": "US", "state": "VA", "county": "Loudoun"}',
 ARRAY['gc', 'trades', 'developer'],
 ARRAY['building_permit', 'data_center', 'commercial'],
 'workers/templates/arcgis_permits.py',
 '{"permit_endpoint": "https://gis.loudoun.gov/...", "case_types": ["Building Commercial", "Site Development"]}',
 'draft',
 ARRAY['permits', 'virginia', 'data-centers', 'priority']
);
