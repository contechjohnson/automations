# Make.com-First Architecture Plan

This document outlines the pivot from Python-first v2 implementation to a Make.com-first approach.

## Overview

Pivot from the over-engineered Python-first v2 implementation to a Make.com-first approach that leverages existing Make.com infrastructure for orchestration while using Supabase as the backend and our custom API server as middleware for targeted interventions.

## Status: Implementation Complete

All Phase 1 tasks have been completed:

1. ✅ Created `columnline_app/v2_archive/` directory
2. ✅ Moved `columnline_app/v2/` to `columnline_app/v2_archive/v2/`
3. ✅ Moved `admin/` to `columnline_app/v2_archive/admin/`
4. ✅ Added README.md in archive explaining preservation
5. ✅ Commented out v2 router import in `api/main.py`
6. ✅ Created new API endpoints for Make.com integration:
   - `/v2/prompts/{prompt_id}` - Get prompt content
   - `/v2/prompts/{prompt_id}/version` - Get specific version
   - `/v2/clients/{client_id}/config` - Get all configs
   - `/v2/clients/{client_id}/icp` - Get ICP_CONFIG
   - `/v2/clients/{client_id}/industry` - Get INDUSTRY_RESEARCH
   - `/v2/clients/{client_id}/context` - Get RESEARCH_CONTEXT
   - `/v2/logs/step` - Log step execution
   - `/v2/logs/run/{run_id}` - Get run logs
   - `/v2/transform/claims-extract` - Extract claims from narrative
   - `/v2/transform/context-pack` - Build context pack

## Next Steps

1. **Prompt Migration** - Migrate prompts from CSV/docs to Supabase v2_prompts table
2. **Client Config Migration** - Migrate client configs to Supabase v2_clients table
3. **Make.com Integration** - Update Make.com scenarios to use new API endpoints
4. **Testing** - End-to-end testing with Make.com scenarios

## Architecture

- **Make.com**: Orchestration, polling, long-running steps
- **Supabase**: Prompt storage, client configs, execution logging
- **Custom API**: Thin middleware for prompt retrieval, logging, transformations

See the full plan document in `~/.cursor/plans/make.com_first_architecture_43532a45.plan.md` for complete details.

