-- =============================================================================
-- Migration: 004_batch_composer_and_prep_inputs.sql
-- Purpose: Add fields for batch composer, prep inputs, and onboarding flows
-- Run this in Supabase SQL Editor
-- =============================================================================

-- 1. Add batch_strategy columns to v2_clients
-- (Currently only has drip_schedule, but batch_strategy is the content for batch composer)
ALTER TABLE v2_clients
ADD COLUMN IF NOT EXISTS batch_strategy JSONB,
ADD COLUMN IF NOT EXISTS batch_strategy_compressed TEXT;

COMMENT ON COLUMN v2_clients.batch_strategy IS 'Full batch strategy config (distribution, seed rules, quality thresholds)';
COMMENT ON COLUMN v2_clients.batch_strategy_compressed IS 'LLM-compressed batch strategy for token efficiency';

-- 2. Add target_entity and target_project to v2_dossiers if not present
-- (These are needed for existing_leads lookup in batch composer)
ALTER TABLE v2_dossiers
ADD COLUMN IF NOT EXISTS target_entity TEXT,
ADD COLUMN IF NOT EXISTS target_project TEXT;

COMMENT ON COLUMN v2_dossiers.target_entity IS 'Company name being researched (for duplicate avoidance)';
COMMENT ON COLUMN v2_dossiers.target_project IS 'Specific project name (for duplicate avoidance)';

-- 3. Update v2_batch_composer to add thread memory fields
ALTER TABLE v2_batch_composer
ADD COLUMN IF NOT EXISTS thread_id TEXT,
ADD COLUMN IF NOT EXISTS batch_number INTEGER,
ADD COLUMN IF NOT EXISTS directions JSONB,
ADD COLUMN IF NOT EXISTS distribution_achieved JSONB,
ADD COLUMN IF NOT EXISTS existing_leads_snapshot JSONB,
ADD COLUMN IF NOT EXISTS recent_directions_snapshot JSONB;

CREATE INDEX IF NOT EXISTS idx_v2_batch_composer_thread ON v2_batch_composer(thread_id);
CREATE INDEX IF NOT EXISTS idx_v2_batch_composer_client_thread ON v2_batch_composer(client_id, thread_id);

COMMENT ON COLUMN v2_batch_composer.thread_id IS 'Groups batches for memory continuity (THREAD_{client_id}_v{version})';
COMMENT ON COLUMN v2_batch_composer.batch_number IS 'Sequence number within the thread';
COMMENT ON COLUMN v2_batch_composer.directions IS 'Output array of hints/directions for pipeline runs';
COMMENT ON COLUMN v2_batch_composer.distribution_achieved IS 'Actual distribution achieved vs target';
COMMENT ON COLUMN v2_batch_composer.existing_leads_snapshot IS 'Snapshot of existing leads at time of batch creation';
COMMENT ON COLUMN v2_batch_composer.recent_directions_snapshot IS 'Snapshot of recent directions at time of batch creation';

-- 4. Update v2_prep_inputs to add step tracking
ALTER TABLE v2_prep_inputs
ADD COLUMN IF NOT EXISTS current_step TEXT,
ADD COLUMN IF NOT EXISTS steps_completed TEXT[],
ADD COLUMN IF NOT EXISTS original_batch_strategy JSONB,
ADD COLUMN IF NOT EXISTS compressed_batch_strategy TEXT;

COMMENT ON COLUMN v2_prep_inputs.current_step IS 'Which compression step is in progress';
COMMENT ON COLUMN v2_prep_inputs.steps_completed IS 'Array of completed compression steps';
COMMENT ON COLUMN v2_prep_inputs.original_batch_strategy IS 'Original batch strategy before compression';
COMMENT ON COLUMN v2_prep_inputs.compressed_batch_strategy IS 'Compressed batch strategy output';

-- 5. Update v2_onboarding to match plan (add intake_data as single JSONB field)
ALTER TABLE v2_onboarding
ADD COLUMN IF NOT EXISTS intake_data JSONB,
ADD COLUMN IF NOT EXISTS current_step TEXT,
ADD COLUMN IF NOT EXISTS steps_completed TEXT[],
ADD COLUMN IF NOT EXISTS consolidated_info JSONB;

COMMENT ON COLUMN v2_onboarding.intake_data IS 'All raw inputs (transcripts, website, narrative, materials)';
COMMENT ON COLUMN v2_onboarding.current_step IS 'Current onboarding step in progress';
COMMENT ON COLUMN v2_onboarding.steps_completed IS 'Array of completed onboarding steps';
COMMENT ON COLUMN v2_onboarding.consolidated_info IS 'Consolidated info from step 1 (before config generation)';

-- 6. Create index for batch lead lookup
CREATE INDEX IF NOT EXISTS idx_v2_dossiers_client_created ON v2_dossiers(client_id, created_at DESC);

-- =============================================================================
-- COMPLETE
-- =============================================================================
-- Run this migration in Supabase SQL Editor
-- All changes are additive (ADD COLUMN IF NOT EXISTS) so safe to re-run
