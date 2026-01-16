-- Migration: V2 Production Integration
-- Purpose: Add columns needed for v2 → production dossier publishing
-- Date: 2026-01-15

-- =============================================================================
-- PART 1: Add production_client_id to v2_clients
-- =============================================================================
-- This allows mapping v2 pipeline clients to production app client UUIDs

ALTER TABLE v2_clients
ADD COLUMN IF NOT EXISTS production_client_id UUID;

COMMENT ON COLUMN v2_clients.production_client_id IS
    'Maps to production clients.id for dossier publishing';

-- =============================================================================
-- PART 2: Add pipeline_version to dossiers
-- =============================================================================
-- This tracks whether a dossier was created by v1 (TypeScript) or v2 (Make.com)

ALTER TABLE dossiers
ADD COLUMN IF NOT EXISTS pipeline_version TEXT DEFAULT 'v1';

CREATE INDEX IF NOT EXISTS idx_dossiers_pipeline_version
ON dossiers(pipeline_version);

COMMENT ON COLUMN dossiers.pipeline_version IS
    'v1 = TypeScript pipeline (original), v2 = Make.com pipeline';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these to verify the migration succeeded:

-- Check v2_clients has new column:
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'v2_clients' AND column_name = 'production_client_id';

-- Check dossiers has new column:
-- SELECT column_name, data_type, column_default FROM information_schema.columns
-- WHERE table_name = 'dossiers' AND column_name = 'pipeline_version';

-- Check index exists:
-- SELECT indexname FROM pg_indexes WHERE indexname = 'idx_dossiers_pipeline_version';
