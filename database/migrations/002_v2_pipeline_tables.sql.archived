-- =============================================================================
-- V2 COLUMNLINE PIPELINE SCHEMA
-- Migration: 002_v2_pipeline_tables.sql
--
-- Run this in Supabase SQL Editor
-- All tables use v2_ prefix to avoid conflicts with existing tables
-- =============================================================================

-- Enable UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- FOUNDATION TABLES (must be created first due to FK dependencies)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- V2_CLIENTS - Client configuration with ICP, Industry, Research Context
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,

    -- ICP Configuration (JSON)
    -- {signals: [{name, tier, weight}], disqualifiers: [], target_titles: [],
    --  excluded_titles: [], scoring_weights: {}, geography: {tier_1: [], tier_2: [], tier_3: []}}
    icp_config JSONB NOT NULL DEFAULT '{}',

    -- Industry Research (JSON)
    -- {buying_signals: [], personas: [], industries: [], timing_constraints: [], sources_to_check: []}
    industry_research JSONB NOT NULL DEFAULT '{}',

    -- Research Context (JSON)
    -- {client: {name, domain, tagline}, differentiators: [], notable_projects: [],
    --  competitors: [], goals: {}, brand_voice: {}}
    research_context JSONB NOT NULL DEFAULT '{}',

    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_v2_clients_slug ON v2_clients(slug);
CREATE INDEX IF NOT EXISTS idx_v2_clients_status ON v2_clients(status);

-- -----------------------------------------------------------------------------
-- V2_PROMPTS - Prompt registry (replaces Google Sheets Prompts tab)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT UNIQUE NOT NULL,        -- "search-builder", "signal-discovery"
    name TEXT NOT NULL,                     -- "Search Builder"
    stage TEXT NOT NULL,                    -- "FIND_LEAD", "DEEP_RESEARCH", "ENRICH", "INSIGHT", "WRITE"
    step_order INTEGER NOT NULL,            -- 1, 2, 3... for ordering

    -- Behavior flags
    produces_claims BOOLEAN DEFAULT false,
    merges_claims BOOLEAN DEFAULT false,
    produces_context_pack BOOLEAN DEFAULT false,
    context_pack_type TEXT CHECK (context_pack_type IN ('signal_to_entity', 'entity_to_contacts', 'contacts_to_enrichment', NULL)),

    -- LLM Configuration
    model TEXT DEFAULT 'gpt-4.1',
    temperature NUMERIC(3,2) DEFAULT 0.7,
    max_tokens INTEGER,
    uses_tools TEXT[],                      -- ["web_search"], ["firecrawl_scrape"], etc.

    -- Execution mode
    execution_mode TEXT DEFAULT 'sync' CHECK (execution_mode IN ('sync', 'async_poll', 'background', 'agent')),
    timeout_seconds INTEGER DEFAULT 300,

    -- Status
    current_version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_prompts_stage ON v2_prompts(stage);
CREATE INDEX IF NOT EXISTS idx_v2_prompts_active ON v2_prompts(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_v2_prompts_order ON v2_prompts(step_order);

-- -----------------------------------------------------------------------------
-- V2_PROMPT_VERSIONS - Full version history for prompts
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL REFERENCES v2_prompts(prompt_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,

    -- Content
    content TEXT NOT NULL,                  -- Full prompt with {{variables}}
    system_prompt TEXT,                     -- Optional system prompt

    -- Change tracking
    change_notes TEXT,
    created_by TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(prompt_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_v2_prompt_versions_prompt ON v2_prompt_versions(prompt_id);

-- -----------------------------------------------------------------------------
-- V2_PIPELINE_RUNS - Top-level job tracking
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    client_id UUID REFERENCES v2_clients(id) ON DELETE SET NULL,
    dossier_id UUID,                        -- Populated when dossier is created

    -- Input
    seed JSONB,                             -- Seed data (company name, domain, etc.)

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    current_step TEXT,                      -- Which step is currently running
    steps_completed TEXT[] DEFAULT '{}',    -- Steps that have finished

    -- Configuration
    config JSONB DEFAULT '{}',              -- Runtime overrides

    -- Error handling
    error_message TEXT,
    error_step TEXT,
    error_traceback TEXT,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- RQ integration
    rq_job_id TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_pipeline_runs_client ON v2_pipeline_runs(client_id);
CREATE INDEX IF NOT EXISTS idx_v2_pipeline_runs_status ON v2_pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_v2_pipeline_runs_created ON v2_pipeline_runs(created_at DESC);

-- -----------------------------------------------------------------------------
-- V2_STEP_RUNS - Per-step I/O capture (THE KEY TABLE for observability)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_step_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,

    -- Step identification
    step TEXT NOT NULL,                     -- "search_builder", "signal_discovery"
    prompt_id TEXT REFERENCES v2_prompts(prompt_id) ON DELETE SET NULL,
    prompt_version INTEGER,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),

    -- Input capture
    input_variables JSONB DEFAULT '{}',     -- Variables passed to prompt
    interpolated_prompt TEXT,               -- Prompt after {{variable}} substitution

    -- Output capture
    raw_output TEXT,                        -- Raw LLM response (string)
    parsed_output JSONB,                    -- Parsed JSON output

    -- LLM details
    model TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,

    -- Timing
    duration_ms INTEGER,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Error handling
    error_message TEXT,
    error_traceback TEXT,

    -- Async tracking
    response_id TEXT,                       -- For OpenAI Responses API polling

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_step_runs_pipeline ON v2_step_runs(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_v2_step_runs_step ON v2_step_runs(step);
CREATE INDEX IF NOT EXISTS idx_v2_step_runs_status ON v2_step_runs(status);
CREATE INDEX IF NOT EXISTS idx_v2_step_runs_prompt ON v2_step_runs(prompt_id);

-- =============================================================================
-- CLAIMS SYSTEM TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- V2_CLAIMS - Raw claims extracted from research steps (before merge)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Claim identification
    claim_id TEXT NOT NULL,                 -- "search_001", "entity_003"
    claim_type TEXT NOT NULL CHECK (claim_type IN ('SIGNAL', 'CONTACT', 'ENTITY', 'RELATIONSHIP', 'OPPORTUNITY', 'METRIC', 'ATTRIBUTE', 'NOTE')),

    -- Content
    statement TEXT NOT NULL,                -- One atomic fact, max 500 chars
    entities TEXT[] DEFAULT '{}',           -- Entity names mentioned
    date_in_claim DATE,                     -- Date referenced (YYYY-MM-DD)

    -- Source attribution
    source_url TEXT,
    source_name TEXT,
    source_tier TEXT NOT NULL CHECK (source_tier IN ('GOV', 'PRIMARY', 'NEWS', 'OTHER')),
    confidence TEXT NOT NULL CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    source_step TEXT NOT NULL,              -- Step that produced this claim

    -- Merge tracking
    is_merged BOOLEAN DEFAULT false,
    merged_into TEXT,                       -- MERGED_xxx claim ID

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_claims_pipeline ON v2_claims(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_v2_claims_step ON v2_claims(step_run_id);
CREATE INDEX IF NOT EXISTS idx_v2_claims_type ON v2_claims(claim_type);
CREATE INDEX IF NOT EXISTS idx_v2_claims_source_step ON v2_claims(source_step);
CREATE INDEX IF NOT EXISTS idx_v2_claims_unmerged ON v2_claims(is_merged) WHERE is_merged = false;

-- -----------------------------------------------------------------------------
-- V2_MERGED_CLAIMS - Deduplicated claims after 07B Insight
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_merged_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    insight_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Merged claim identification
    merged_claim_id TEXT NOT NULL,          -- "MERGED_001"
    claim_type TEXT NOT NULL CHECK (claim_type IN ('SIGNAL', 'CONTACT', 'ENTITY', 'RELATIONSHIP', 'OPPORTUNITY', 'METRIC', 'ATTRIBUTE', 'NOTE')),

    -- Content (canonical version)
    statement TEXT NOT NULL,
    entities TEXT[] DEFAULT '{}',
    date_in_claim DATE,

    -- Source aggregation
    original_claim_ids TEXT[] NOT NULL,     -- ["entity_003", "lead_001"]
    sources JSONB NOT NULL DEFAULT '[]',    -- [{url, name, tier, original_claim_id}]
    confidence TEXT NOT NULL CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),

    -- Reconciliation metadata
    reconciliation_type TEXT CHECK (reconciliation_type IN ('DUPLICATE', 'CONFLICT', 'TIMELINE', 'PASS_THROUGH', NULL)),
    conflicts_resolved JSONB,
    supersedes JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_merged_claims_pipeline ON v2_merged_claims(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_v2_merged_claims_type ON v2_merged_claims(claim_type);
CREATE INDEX IF NOT EXISTS idx_v2_merged_claims_insight ON v2_merged_claims(insight_step_run_id);

-- -----------------------------------------------------------------------------
-- V2_RESOLVED_OBJECTS - Contacts, timelines, conflicts from merge
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_resolved_objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,

    -- Object type and identification
    object_type TEXT NOT NULL CHECK (object_type IN ('CONTACT', 'TIMELINE', 'CONFLICT', 'AMBIGUOUS')),
    object_id TEXT NOT NULL,                -- "contact_001", "timeline_001"

    -- Resolution data (structure varies by type)
    data JSONB NOT NULL,

    -- Evidence
    evidence_claim_ids TEXT[] NOT NULL,
    confidence TEXT NOT NULL,
    resolution TEXT,                        -- SAME_PERSON | DIFFERENT_PERSON | UNSURE | etc.

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_resolved_objects_pipeline ON v2_resolved_objects(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_v2_resolved_objects_type ON v2_resolved_objects(object_type);

-- -----------------------------------------------------------------------------
-- V2_CONTEXT_PACKS - Efficiency summaries for downstream steps
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_context_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Pack type and content
    pack_type TEXT NOT NULL CHECK (pack_type IN ('signal_to_entity', 'entity_to_contacts', 'contacts_to_enrichment')),
    pack_data JSONB NOT NULL,

    -- Lineage
    anchor_claim_ids TEXT[] DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_context_packs_pipeline ON v2_context_packs(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_v2_context_packs_type ON v2_context_packs(pack_type);

-- -----------------------------------------------------------------------------
-- V2_CLAIM_ASSIGNMENTS - Routes claims to dossier sections
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_claim_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    dossier_plan_step_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Assignment
    section_key TEXT NOT NULL CHECK (section_key IN ('INTRO', 'SCORE', 'SIGNALS', 'CONTACTS', 'LEAD_INTELLIGENCE', 'STRATEGY', 'OPPORTUNITY', 'CLIENT_SPECIFIC')),
    merged_claim_id TEXT NOT NULL,

    -- Routing metadata
    priority INTEGER DEFAULT 0,
    coverage_notes TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_claim_assignments_pipeline ON v2_claim_assignments(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_v2_claim_assignments_section ON v2_claim_assignments(section_key);
CREATE INDEX IF NOT EXISTS idx_v2_claim_assignments_claim ON v2_claim_assignments(merged_claim_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_v2_claim_assignments_unique ON v2_claim_assignments(pipeline_run_id, section_key, merged_claim_id);

-- -----------------------------------------------------------------------------
-- V2_MERGE_STATS - Observability for merge process
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_merge_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    insight_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Counts
    input_claims_count INTEGER NOT NULL,
    output_claims_count INTEGER NOT NULL,
    duplicates_merged INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    timelines_resolved INTEGER DEFAULT 0,
    contacts_resolved INTEGER DEFAULT 0,
    ambiguous_items INTEGER DEFAULT 0,
    passed_through INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_merge_stats_pipeline ON v2_merge_stats(pipeline_run_id);

-- =============================================================================
-- OUTPUT TABLES (Dossiers, Sections, Contacts)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- V2_DOSSIERS - Completed dossier metadata
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_dossiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID UNIQUE REFERENCES v2_pipeline_runs(id) ON DELETE SET NULL,
    client_id UUID REFERENCES v2_clients(id) ON DELETE SET NULL,

    -- Core fields (denormalized for quick access)
    company_name TEXT NOT NULL,
    company_domain TEXT,
    lead_score INTEGER,
    timing_urgency TEXT,
    primary_signal TEXT,

    -- Status
    status TEXT DEFAULT 'skeleton' CHECK (status IN ('skeleton', 'enriching', 'ready', 'archived', 'superseded')),
    sections_completed TEXT[] DEFAULT '{}',

    -- Timing
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    released_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_v2_dossiers_client ON v2_dossiers(client_id);
CREATE INDEX IF NOT EXISTS idx_v2_dossiers_status ON v2_dossiers(status);
CREATE INDEX IF NOT EXISTS idx_v2_dossiers_created ON v2_dossiers(created_at DESC);

-- -----------------------------------------------------------------------------
-- V2_DOSSIER_SECTIONS - Section content (generated by writers)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_dossier_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES v2_dossiers(id) ON DELETE CASCADE,
    pipeline_run_id UUID REFERENCES v2_pipeline_runs(id) ON DELETE SET NULL,

    -- Section identification
    section_key TEXT NOT NULL CHECK (section_key IN ('intro', 'signals', 'contacts', 'lead_intelligence', 'strategy', 'opportunity', 'client_specific')),
    writer_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Content
    content JSONB NOT NULL,                 -- Full section content
    sources JSONB DEFAULT '[]',             -- [{url, name, accessed}]

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(dossier_id, section_key)
);

CREATE INDEX IF NOT EXISTS idx_v2_dossier_sections_dossier ON v2_dossier_sections(dossier_id);

-- -----------------------------------------------------------------------------
-- V2_CONTACTS - Enriched contacts per dossier
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES v2_dossiers(id) ON DELETE CASCADE,
    pipeline_run_id UUID REFERENCES v2_pipeline_runs(id) ON DELETE SET NULL,

    -- Basic info
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    title TEXT,
    organization TEXT,
    linkedin_url TEXT,

    -- Enriched data
    bio TEXT,
    tenure TEXT,
    why_they_matter TEXT,
    relation_to_signal TEXT,
    interesting_facts TEXT,

    -- Outreach copy
    email_copy TEXT,
    linkedin_copy TEXT,
    client_email_copy TEXT,
    client_linkedin_copy TEXT,

    -- Status
    is_primary BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    confidence TEXT CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    source TEXT,                            -- apollo | linkedin | research | manual
    enrichment_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_contacts_dossier ON v2_contacts(dossier_id);
CREATE INDEX IF NOT EXISTS idx_v2_contacts_email ON v2_contacts(email) WHERE email IS NOT NULL;

-- =============================================================================
-- LINEAGE TRACKING
-- =============================================================================

-- -----------------------------------------------------------------------------
-- V2_VARIABLE_LINEAGE - Trace where each input variable came from
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS v2_variable_lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step_run_id UUID NOT NULL REFERENCES v2_step_runs(id) ON DELETE CASCADE,

    -- Variable tracking
    variable_name TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('client_config', 'previous_step', 'seed', 'static', 'computed', 'context_pack')),
    source_step TEXT,                       -- Which step produced this value
    source_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Preview for display
    value_preview TEXT,                     -- First 500 chars

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v2_variable_lineage_step ON v2_variable_lineage(step_run_id);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Claims summary by pipeline run
CREATE OR REPLACE VIEW v2_claims_summary AS
SELECT
    pipeline_run_id,
    claim_type,
    COUNT(*) as total_claims,
    COUNT(*) FILTER (WHERE is_merged = false) as active_claims,
    COUNT(*) FILTER (WHERE is_merged = true) as merged_claims,
    COUNT(*) FILTER (WHERE confidence = 'HIGH') as high_confidence,
    COUNT(*) FILTER (WHERE confidence = 'MEDIUM') as medium_confidence,
    COUNT(*) FILTER (WHERE confidence = 'LOW') as low_confidence
FROM v2_claims
GROUP BY pipeline_run_id, claim_type;

-- Section claims (for writers) - joins assignments with merged claims
CREATE OR REPLACE VIEW v2_section_claims AS
SELECT
    ca.pipeline_run_id,
    ca.section_key,
    mc.merged_claim_id,
    mc.claim_type,
    mc.statement,
    mc.confidence,
    mc.sources,
    ca.priority,
    ca.coverage_notes
FROM v2_claim_assignments ca
JOIN v2_merged_claims mc ON mc.pipeline_run_id = ca.pipeline_run_id
    AND mc.merged_claim_id = ca.merged_claim_id
ORDER BY ca.section_key, ca.priority DESC;

-- Last run per prompt (for dashboard)
CREATE OR REPLACE VIEW v2_prompt_last_runs AS
SELECT DISTINCT ON (sr.prompt_id, pr.client_id)
    sr.prompt_id,
    pr.client_id,
    sr.id AS step_run_id,
    sr.status,
    sr.input_variables,
    sr.parsed_output AS output,
    sr.interpolated_prompt,
    sr.started_at,
    sr.duration_ms,
    sr.tokens_in,
    sr.tokens_out,
    sr.error_message
FROM v2_step_runs sr
JOIN v2_pipeline_runs pr ON pr.id = sr.pipeline_run_id
WHERE sr.status IN ('completed', 'failed')
ORDER BY sr.prompt_id, pr.client_id, sr.started_at DESC;

-- Pipeline run summary
CREATE OR REPLACE VIEW v2_pipeline_run_summary AS
SELECT
    pr.id,
    pr.client_id,
    c.name AS client_name,
    c.slug AS client_slug,
    pr.status,
    pr.current_step,
    COALESCE(array_length(pr.steps_completed, 1), 0) AS steps_completed_count,
    (SELECT COUNT(*) FROM v2_prompts WHERE is_active = true) AS total_steps,
    EXTRACT(EPOCH FROM (pr.completed_at - pr.started_at)) AS duration_seconds,
    COALESCE(SUM(sr.tokens_in), 0) AS total_tokens_in,
    COALESCE(SUM(sr.tokens_out), 0) AS total_tokens_out,
    pr.seed,
    pr.error_message,
    pr.created_at,
    pr.started_at,
    pr.completed_at
FROM v2_pipeline_runs pr
LEFT JOIN v2_clients c ON c.id = pr.client_id
LEFT JOIN v2_step_runs sr ON sr.pipeline_run_id = pr.id
GROUP BY pr.id, c.name, c.slug
ORDER BY pr.created_at DESC;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION v2_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables with updated_at
CREATE TRIGGER trigger_v2_clients_updated
BEFORE UPDATE ON v2_clients
FOR EACH ROW EXECUTE FUNCTION v2_update_timestamp();

CREATE TRIGGER trigger_v2_prompts_updated
BEFORE UPDATE ON v2_prompts
FOR EACH ROW EXECUTE FUNCTION v2_update_timestamp();

CREATE TRIGGER trigger_v2_dossiers_updated
BEFORE UPDATE ON v2_dossiers
FOR EACH ROW EXECUTE FUNCTION v2_update_timestamp();

CREATE TRIGGER trigger_v2_dossier_sections_updated
BEFORE UPDATE ON v2_dossier_sections
FOR EACH ROW EXECUTE FUNCTION v2_update_timestamp();

CREATE TRIGGER trigger_v2_contacts_updated
BEFORE UPDATE ON v2_contacts
FOR EACH ROW EXECUTE FUNCTION v2_update_timestamp();

-- =============================================================================
-- COMMENTS (for documentation)
-- =============================================================================

COMMENT ON TABLE v2_clients IS 'Client configurations with ICP, industry research, and research context';
COMMENT ON TABLE v2_prompts IS 'Registry of all pipeline prompts with metadata';
COMMENT ON TABLE v2_prompt_versions IS 'Version history for prompts with full content';
COMMENT ON TABLE v2_pipeline_runs IS 'Top-level pipeline execution tracking';
COMMENT ON TABLE v2_step_runs IS 'Per-step I/O capture - THE KEY TABLE for observability';
COMMENT ON TABLE v2_claims IS 'Raw atomic claims extracted before merge (step 07B)';
COMMENT ON TABLE v2_merged_claims IS 'Deduplicated claims after 07B Insight merge';
COMMENT ON TABLE v2_resolved_objects IS 'Contact, timeline, and conflict resolutions from merge';
COMMENT ON TABLE v2_context_packs IS 'Efficiency summaries passed between pipeline stages';
COMMENT ON TABLE v2_claim_assignments IS 'Routes merged claims to dossier sections';
COMMENT ON TABLE v2_merge_stats IS 'Statistics from the claims merge process';
COMMENT ON TABLE v2_dossiers IS 'Completed dossier metadata';
COMMENT ON TABLE v2_dossier_sections IS 'Section content generated by writers';
COMMENT ON TABLE v2_contacts IS 'Enriched contacts with outreach copy';
COMMENT ON TABLE v2_variable_lineage IS 'Tracks where each input variable originated';
