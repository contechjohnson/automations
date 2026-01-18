-- Columnline V2 Dossier Pipeline Schema
-- 8 tables: 2 config layer, 2 execution layer, 4 future features
-- Updated: 2026-01-15 (Schema cleanup - dropped 14 unused tables)

-- ============================================================================
-- CONFIG LAYER (2 tables)
-- ============================================================================

-- 1. CLIENTS
-- Stores client configurations and compressed context
CREATE TABLE IF NOT EXISTS v2_clients (
    client_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    status TEXT DEFAULT 'active',

    -- Full and compressed configs (JSONB for queryability)
    icp_config JSONB,
    icp_config_compressed JSONB,
    industry_research JSONB,
    industry_research_compressed JSONB,
    research_context JSONB,
    research_context_compressed JSONB,
    client_specific_research JSONB,

    -- Drip schedule config
    drip_schedule JSONB,

    -- Production mapping
    production_client_id UUID,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. PROMPTS
-- Template storage for all 31 pipeline prompts
CREATE TABLE IF NOT EXISTS v2_prompts (
    prompt_id TEXT PRIMARY KEY,
    prompt_slug TEXT UNIQUE NOT NULL,
    stage TEXT,
    step TEXT,
    prompt_template TEXT NOT NULL,

    -- Flags
    produce_claims BOOLEAN DEFAULT FALSE,
    context_pack_produced BOOLEAN DEFAULT FALSE,

    -- Variables (arrays stored as JSONB)
    variables_used JSONB,
    variables_produced JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- EXECUTION LAYER (2 tables)
-- ============================================================================

-- 3. RUNS
-- Individual dossier run tracking
CREATE TABLE IF NOT EXISTS v2_runs (
    run_id TEXT PRIMARY KEY,
    client_id TEXT REFERENCES v2_clients(client_id),
    status TEXT DEFAULT 'running',

    seed_data JSONB,
    dossier_id TEXT,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    triggered_by TEXT,
    config_snapshot JSONB
);

-- 4. PIPELINE STEPS (THE KEY TABLE)
-- Detailed logging of each pipeline step execution
-- All claims, sections, dossier data stored in output JSONB
CREATE TABLE IF NOT EXISTS v2_pipeline_logs (
    step_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES v2_runs(run_id),
    prompt_id TEXT REFERENCES v2_prompts(prompt_id),
    step_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',

    -- Denormalized for visibility
    input JSONB,
    output JSONB,

    -- Execution metadata
    model_used TEXT,
    tokens_used INTEGER,
    runtime_seconds NUMERIC,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

-- ============================================================================
-- CONTACT OBSERVABILITY (1 table)
-- ============================================================================

-- 5. CONTACTS
-- Contact records for observability (populated via /publish dual-write)
CREATE TABLE IF NOT EXISTS v2_contacts (
    id TEXT PRIMARY KEY,
    dossier_id TEXT,
    run_id TEXT REFERENCES v2_runs(run_id),

    -- Basic info
    name TEXT,
    first_name TEXT,
    last_name TEXT,
    title TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    linkedin_connections INTEGER,
    bio_paragraph TEXT,
    tenure_months INTEGER,

    -- Enrichment fields
    previous_companies JSONB,
    education JSONB,
    skills JSONB,
    recent_post_quote TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    source TEXT,
    tier TEXT,
    bio_summary TEXT,
    why_they_matter TEXT,
    signal_relevance TEXT,
    interesting_facts JSONB,

    -- Copy fields
    linkedin_summary TEXT,
    web_summary TEXT,
    email_copy TEXT,
    linkedin_copy TEXT,
    client_email_copy TEXT,
    client_linkedin_copy TEXT,

    confidence NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- FUTURE FEATURES (3 tables)
-- ============================================================================

-- 6. ONBOARDING
-- Client onboarding conversations and config generation
CREATE TABLE IF NOT EXISTS v2_onboarding (
    onboarding_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    status TEXT DEFAULT 'in_progress',

    -- Inputs
    client_info JSONB,
    transcripts JSONB,
    client_material JSONB,
    pre_research JSONB,

    -- Generation
    onboarding_system_prompt TEXT,
    generated_icp_config JSONB,
    generated_industry_research JSONB,
    generated_research_context JSONB,
    generated_batch_strategy JSONB,

    client_id TEXT REFERENCES v2_clients(client_id),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 7. PREP INPUTS
-- Config compression for token savings
CREATE TABLE IF NOT EXISTS v2_prep_inputs (
    prep_id TEXT PRIMARY KEY,
    client_id TEXT REFERENCES v2_clients(client_id),
    status TEXT DEFAULT 'pending',

    -- Original configs
    original_icp_config JSONB,
    original_industry_research JSONB,
    original_research_context JSONB,

    -- Compressed versions
    compressed_icp_config JSONB,
    compressed_industry_research JSONB,
    compressed_research_context JSONB,

    compression_prompt TEXT,
    token_savings JSONB,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 8. BATCH COMPOSER
-- Weekly batch planning and seed generation
CREATE TABLE IF NOT EXISTS v2_batch_composer (
    batch_id TEXT PRIMARY KEY,
    client_id TEXT REFERENCES v2_clients(client_id),
    status TEXT DEFAULT 'pending',

    batch_strategy JSONB,
    seed_pool_input JSONB,
    last_batch_hints JSONB,
    recent_feedback JSONB,
    run_ids_created JSONB,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Run queries
CREATE INDEX IF NOT EXISTS idx_v2_runs_client_id ON v2_runs(client_id);
CREATE INDEX IF NOT EXISTS idx_v2_runs_status ON v2_runs(status);
CREATE INDEX IF NOT EXISTS idx_v2_runs_dossier_id ON v2_runs(dossier_id);

-- Pipeline steps queries (most frequent)
CREATE INDEX IF NOT EXISTS idx_v2_pipeline_logs_run_id ON v2_pipeline_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_v2_pipeline_logs_status ON v2_pipeline_logs(run_id, status);
CREATE INDEX IF NOT EXISTS idx_v2_pipeline_logs_step_name ON v2_pipeline_logs(run_id, step_name);
CREATE INDEX IF NOT EXISTS idx_v2_pipeline_logs_completed ON v2_pipeline_logs(run_id, step_name, status)
    WHERE status = 'completed';

-- Contacts queries
CREATE INDEX IF NOT EXISTS idx_v2_contacts_dossier_id ON v2_contacts(dossier_id);
CREATE INDEX IF NOT EXISTS idx_v2_contacts_run_id ON v2_contacts(run_id);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE v2_clients IS 'Client configurations and compressed context for dossier generation';
COMMENT ON TABLE v2_prompts IS 'Template storage for all 31 pipeline prompts (model selection handled by Make.com)';
COMMENT ON TABLE v2_runs IS 'Individual dossier run tracking with per-run isolation';
COMMENT ON TABLE v2_pipeline_logs IS 'THE KEY TABLE - All step inputs/outputs stored here (claims, sections, dossier data)';
COMMENT ON TABLE v2_contacts IS 'Contact records for observability (dual-write from /publish)';
COMMENT ON TABLE v2_onboarding IS 'Future: Client onboarding conversations and config generation';
COMMENT ON TABLE v2_prep_inputs IS 'Future: Config compression for token savings';
COMMENT ON TABLE v2_batch_composer IS 'Future: Weekly batch planning and seed generation';

-- ============================================================================
-- COMPLETE
-- ============================================================================
-- Total: 8 tables (2 config + 2 execution + 1 observability + 3 future)
-- Indexes: 9 performance indexes
-- Cleaned up from original 22 tables on 2026-01-15
