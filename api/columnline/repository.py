"""
Columnline Repository

Database operations for Columnline API endpoints.
All queries return clean JSON - no nested arrays, no wrapper hell.
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client


class ColumnlineRepository:
    """Database repository for Columnline operations"""

    def __init__(self):
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.client: Client = create_client(supabase_url, supabase_key)

    # ========================================================================
    # CLIENT & PROMPTS (Config Fetch)
    # ========================================================================

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Fetch client configuration"""
        result = self.client.table('v2_clients').select('*').eq('client_id', client_id).execute()

        if result.data:
            return result.data[0]
        return None

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Fetch all 31 prompts"""
        result = self.client.table('v2_prompts').select('*').order('prompt_id').execute()
        return result.data

    def get_prompt_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetch specific prompt by slug"""
        result = self.client.table('v2_prompts').select('*').eq('prompt_slug', slug).execute()

        if result.data:
            return result.data[0]
        return None

    # ========================================================================
    # RUNS (Run Management)
    # ========================================================================

    def create_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new run"""
        result = self.client.table('v2_runs').insert(run_data).execute()
        return result.data[0]

    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update run status/completion"""
        result = self.client.table('v2_runs').update(updates).eq('run_id', run_id).execute()
        return result.data[0]

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run details"""
        result = self.client.table('v2_runs').select('*').eq('run_id', run_id).execute()

        if result.data:
            return result.data[0]
        return None

    def get_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get run status with completed steps

        Returns:
            {
                "run_id": "...",
                "status": "running",
                "completed_steps": ["1_SEARCH_BUILDER", "2_SIGNAL_DISCOVERY"],
                "current_step": "3_ENTITY_RESEARCH",
                "started_at": "...",
                "completed_at": None
            }
        """
        run = self.get_run(run_id)
        if not run:
            return None

        # Get completed steps
        completed = self.client.table('v2_pipeline_steps').select('step_name').eq('run_id', run_id).eq('status', 'completed').execute()

        completed_steps = [s['step_name'] for s in completed.data]

        # Get current step (running)
        running = self.client.table('v2_pipeline_steps').select('step_name').eq('run_id', run_id).eq('status', 'running').execute()

        current_step = running.data[0]['step_name'] if running.data else None

        return {
            "run_id": run_id,
            "status": run['status'],
            "completed_steps": completed_steps,
            "current_step": current_step,
            "started_at": run['started_at'],
            "completed_at": run.get('completed_at'),
            "error_message": run.get('error_message')
        }

    # ========================================================================
    # PIPELINE STEPS (Logging & Polling)
    # ========================================================================

    def create_pipeline_step(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a pipeline step (dual-write: running, then completed)"""
        result = self.client.table('v2_pipeline_steps').insert(step_data).execute()
        return result.data[0]

    def update_pipeline_step(self, step_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update pipeline step (for dual-write pattern)"""
        result = self.client.table('v2_pipeline_steps').update(updates).eq('step_id', step_id).execute()
        return result.data[0]

    def get_completed_step(self, run_id: str, step_name: str) -> Optional[Dict[str, Any]]:
        """
        Check if specific step completed (for polling)

        Returns step data if completed, None if not found or not completed
        """
        result = self.client.table('v2_pipeline_steps').select('*').eq('run_id', run_id).eq('step_name', step_name).eq('status', 'completed').execute()

        if result.data:
            return result.data[0]
        return None

    def get_completed_outputs(self, run_id: str, step_names: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get completed step outputs for a run

        Args:
            run_id: Run ID
            step_names: Optional list of specific step names to fetch

        Returns:
            {
                "1_SEARCH_BUILDER": {
                    "step_id": "...",
                    "output": {...},
                    "completed_at": "...",
                    "tokens_used": 1234,
                    "runtime_seconds": 45.2
                },
                ...
            }
        """
        query = self.client.table('v2_pipeline_steps').select('step_name, step_id, output, completed_at, tokens_used, runtime_seconds').eq('run_id', run_id).eq('status', 'completed')

        if step_names:
            query = query.in_('step_name', step_names)

        result = query.execute()

        outputs = {}
        for step in result.data:
            outputs[step['step_name']] = {
                "step_id": step['step_id'],
                "output": step['output'],
                "completed_at": step['completed_at'],
                "tokens_used": step.get('tokens_used'),
                "runtime_seconds": step.get('runtime_seconds')
            }

        return outputs

    # ========================================================================
    # CLAIMS (Claims Storage)
    # ========================================================================

    def create_claims(self, claims_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store claims from a research step"""
        result = self.client.table('v2_claims').insert(claims_data).execute()
        return result.data[0]

    def get_claims(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all claims for a run"""
        result = self.client.table('v2_claims').select('*').eq('run_id', run_id).execute()
        return result.data

    # ========================================================================
    # SECTIONS (Section Storage)
    # ========================================================================

    def create_section(self, section_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store a dossier section"""
        result = self.client.table('v2_sections').insert(section_data).execute()
        return result.data[0]

    def get_sections(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all sections for a run"""
        result = self.client.table('v2_sections').select('*').eq('run_id', run_id).execute()
        return result.data

    # ========================================================================
    # DOSSIERS (Dossier Assembly)
    # ========================================================================

    def create_dossier(self, dossier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a dossier"""
        result = self.client.table('v2_dossiers').insert(dossier_data).execute()
        return result.data[0]

    def update_dossier(self, dossier_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update dossier"""
        result = self.client.table('v2_dossiers').update(updates).eq('dossier_id', dossier_id).execute()
        return result.data[0]

    def get_dossier(self, dossier_id: str) -> Optional[Dict[str, Any]]:
        """Get dossier by ID"""
        result = self.client.table('v2_dossiers').select('*').eq('dossier_id', dossier_id).execute()

        if result.data:
            return result.data[0]
        return None

    def get_dossier_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get dossier by run ID"""
        result = self.client.table('v2_dossiers').select('*').eq('run_id', run_id).execute()

        if result.data:
            return result.data[0]
        return None

    # ========================================================================
    # CONTACTS (Contact Storage)
    # ========================================================================

    def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store a discovered contact"""
        result = self.client.table('v2_contacts').insert(contact_data).execute()
        return result.data[0]

    def get_contacts(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all contacts for a run"""
        result = self.client.table('v2_contacts').select('*').eq('run_id', run_id).execute()
        return result.data

    def get_contacts_by_dossier(self, dossier_id: str) -> List[Dict[str, Any]]:
        """Get all contacts for a dossier"""
        result = self.client.table('v2_contacts').select('*').eq('dossier_id', dossier_id).execute()
        return result.data
