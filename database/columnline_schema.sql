-- Columnline Dossier Pipeline Schema
-- 14 tables: 3 config layer, 11 execution layer
-- Created: 2026-01-13

-- ============================================================================
-- CONFIG LAYER (3 tables)
-- ============================================================================

-- 1. CLIENTS
-- Stores client configurations and compressed context
CREATE TABLE IF NOT EXISTS clients (
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

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. PROMPTS
-- Template storage for all 31 pipeline prompts
-- REMOVED: model (Make.com handles this), version (Supabase handles this)
CREATE TABLE IF NOT EXISTS prompts (
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

-- 3. SECTION DEFINITIONS
-- Defines expected structure for dossier sections
CREATE TABLE IF NOT EXISTS section_definitions (
    section_name TEXT PRIMARY KEY,
    expected_variables JSONB,
    variable_types JSONB,
    validation_rules JSONB,
    description TEXT,
    example_output JSONB
);

-- ============================================================================
-- EXECUTION LAYER (11 tables)
-- ============================================================================

-- 4. ONBOARDING
-- Client onboarding conversations and config generation
CREATE TABLE IF NOT EXISTS onboarding (
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

    client_id TEXT REFERENCES clients(client_id),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 5. PREP INPUTS
-- Config compression for token savings
CREATE TABLE IF NOT EXISTS prep_inputs (
    prep_id TEXT PRIMARY KEY,
    client_id TEXT REFERENCES clients(client_id),
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

-- 6. BATCH COMPOSER
-- Weekly batch planning and seed generation
CREATE TABLE IF NOT EXISTS batch_composer (
    batch_id TEXT PRIMARY KEY,
    client_id TEXT REFERENCES clients(client_id),
    status TEXT DEFAULT 'pending',

    batch_strategy JSONB,
    seed_pool_input JSONB,
    last_batch_hints JSONB,
    recent_feedback JSONB,
    run_ids_created JSONB,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 7. RUNS
-- Individual dossier run tracking
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    client_id TEXT REFERENCES clients(client_id),
    status TEXT DEFAULT 'running',

    seed_data JSONB,
    dossier_id TEXT,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    triggered_by TEXT,
    config_snapshot JSONB
);

-- 8. PIPELINE STEPS
-- Detailed logging of each pipeline step execution
-- Input/output denormalized for debugging visibility
CREATE TABLE IF NOT EXISTS pipeline_steps (
    step_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(run_id),
    prompt_id TEXT REFERENCES prompts(prompt_id),
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

-- 9. CLAIMS
-- Atomic facts extracted from research steps
CREATE TABLE IF NOT EXISTS claims (
    run_id TEXT REFERENCES runs(run_id),
    step_id TEXT REFERENCES pipeline_steps(step_id),
    step_name TEXT,
    claims_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (run_id, step_id)
);

-- 10. MERGED CLAIMS
-- Claims after deduplication and merging
CREATE TABLE IF NOT EXISTS merged_claims (
    merge_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(run_id),
    step_id TEXT REFERENCES pipeline_steps(step_id),
    merged_claims_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. CONTEXT PACKS
-- Compressed context passed between steps
CREATE TABLE IF NOT EXISTS context_packs (
    pack_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(run_id),
    context_type TEXT,
    pack_content JSONB NOT NULL,
    produced_by_step TEXT,
    consumed_by_steps JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. CONTACTS
-- Discovered contacts with generation + renderable fields
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    dossier_id TEXT,
    run_id TEXT REFERENCES runs(run_id),

    -- Generation fields (LLM outputs)
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

    -- Renderable fields (for dossier display)
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

-- 13. SECTIONS
-- Individual dossier sections (INTRO, SIGNALS, etc.)
CREATE TABLE IF NOT EXISTS sections (
    section_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(run_id),
    section_name TEXT NOT NULL,
    section_data JSONB,
    claim_ids_used JSONB,
    produced_by_step TEXT,
    status TEXT DEFAULT 'pending',
    variables_produced JSONB,
    target_column TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. DOSSIERS
-- Final assembled dossiers ready for delivery
CREATE TABLE IF NOT EXISTS dossiers (
    dossier_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(run_id) UNIQUE,
    client_id TEXT REFERENCES clients(client_id),

    company_name TEXT,
    lead_score INTEGER,
    timing_urgency TEXT,
    primary_signal TEXT,

    -- Section content columns
    find_lead JSONB,
    enrich_lead JSONB,
    copy JSONB,
    insight JSONB,
    media JSONB,

    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Run queries
CREATE INDEX IF NOT EXISTS idx_runs_client_id ON runs(client_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_dossier_id ON runs(dossier_id);

-- Pipeline steps queries (most frequent)
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_run_id ON pipeline_steps(run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_status ON pipeline_steps(run_id, status);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_step_name ON pipeline_steps(run_id, step_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_completed ON pipeline_steps(run_id, step_name, status)
    WHERE status = 'completed';

-- Claims queries
CREATE INDEX IF NOT EXISTS idx_claims_run_id ON claims(run_id);
CREATE INDEX IF NOT EXISTS idx_merged_claims_run_id ON merged_claims(run_id);

-- Contacts queries
CREATE INDEX IF NOT EXISTS idx_contacts_dossier_id ON contacts(dossier_id);
CREATE INDEX IF NOT EXISTS idx_contacts_run_id ON contacts(run_id);

-- Sections queries
CREATE INDEX IF NOT EXISTS idx_sections_run_id ON sections(run_id);
CREATE INDEX IF NOT EXISTS idx_sections_section_name ON sections(run_id, section_name);

-- Dossiers queries
CREATE INDEX IF NOT EXISTS idx_dossiers_client_id ON dossiers(client_id);
CREATE INDEX IF NOT EXISTS idx_dossiers_status ON dossiers(status);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE clients IS 'Client configurations and compressed context for dossier generation';
COMMENT ON TABLE prompts IS 'Template storage for all 31 pipeline prompts (model selection handled by Make.com)';
COMMENT ON TABLE section_definitions IS 'Expected structure and validation rules for dossier sections';
COMMENT ON TABLE runs IS 'Individual dossier run tracking with per-run isolation';
COMMENT ON TABLE pipeline_steps IS 'Detailed logging of each pipeline step (dual-write: running + completed)';
COMMENT ON TABLE claims IS 'Atomic facts extracted from research steps';
COMMENT ON TABLE dossiers IS 'Final assembled dossiers with all sections';

-- ============================================================================
-- COMPLETE
-- ============================================================================
-- Total: 14 tables (3 config + 11 execution)
-- Indexes: 15 performance indexes
-- Ready for CSV import and API integration
