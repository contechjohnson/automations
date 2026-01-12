-- =============================================================================
-- ADD signal_discovery PACK TYPE
-- Migration: 003_add_signal_discovery_pack_type.sql
--
-- This adds the signal_discovery pack type to v2_context_packs constraint
-- and v2_prompts context_pack_type constraint
-- =============================================================================

-- Drop the existing constraint on v2_context_packs
ALTER TABLE v2_context_packs DROP CONSTRAINT IF EXISTS v2_context_packs_pack_type_check;

-- Add the updated constraint with signal_discovery
ALTER TABLE v2_context_packs ADD CONSTRAINT v2_context_packs_pack_type_check
    CHECK (pack_type IN ('signal_discovery', 'signal_to_entity', 'entity_to_contacts', 'contacts_to_enrichment'));

-- Also update the v2_prompts constraint for context_pack_type
ALTER TABLE v2_prompts DROP CONSTRAINT IF EXISTS v2_prompts_context_pack_type_check;

ALTER TABLE v2_prompts ADD CONSTRAINT v2_prompts_context_pack_type_check
    CHECK (context_pack_type IN ('signal_discovery', 'signal_to_entity', 'entity_to_contacts', 'contacts_to_enrichment', NULL));

-- Verify the changes
COMMENT ON TABLE v2_context_packs IS 'Efficiency summaries passed between pipeline stages. Pack types: signal_discovery (step 2->3), signal_to_entity (step 3->4), entity_to_contacts (step 4->5/6), contacts_to_enrichment (step 6->7)';
