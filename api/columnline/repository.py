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

    def get_prompt_by_step(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Fetch prompt by step name (e.g., '1_SEARCH_BUILDER')"""
        result = self.client.table('v2_prompts').select('*').eq('step', step_name).execute()

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
        completed = self.client.table('v2_pipeline_logs').select('step_name').eq('run_id', run_id).eq('status', 'completed').execute()

        completed_steps = [s['step_name'] for s in completed.data]

        # Get current step (running)
        running = self.client.table('v2_pipeline_logs').select('step_name').eq('run_id', run_id).eq('status', 'running').execute()

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
        result = self.client.table('v2_pipeline_logs').insert(step_data).execute()
        return result.data[0]

    def update_pipeline_step(self, step_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update pipeline step (for dual-write pattern)"""
        result = self.client.table('v2_pipeline_logs').update(updates).eq('step_id', step_id).execute()
        return result.data[0]

    def get_completed_step(self, run_id: str, step_name: str) -> Optional[Dict[str, Any]]:
        """
        Check if specific step completed (for polling)

        Returns step data if completed, None if not found or not completed
        """
        result = self.client.table('v2_pipeline_logs').select('*').eq('run_id', run_id).eq('step_name', step_name).eq('status', 'completed').execute()

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
        query = self.client.table('v2_pipeline_logs').select('step_name, step_id, output, completed_at, tokens_used, runtime_seconds').eq('run_id', run_id).eq('status', 'completed')

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
    # ========================================================================
    # REMOVED: CLAIMS, SECTIONS, DOSSIERS
    # These tables were dropped in v2 schema cleanup (2026-01-15)
    # Claims/Sections stored in v2_pipeline_logs.output
    # Dossiers go to production via /publish
    # ========================================================================

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

    # ========================================================================
    # BATCH COMPOSER
    # ========================================================================

    def create_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new batch record"""
        result = self.client.table('v2_batch_composer').insert(batch_data).execute()
        return result.data[0]

    def update_batch(self, batch_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update batch record"""
        result = self.client.table('v2_batch_composer').update(updates).eq('batch_id', batch_id).execute()
        return result.data[0]

    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch by ID"""
        result = self.client.table('v2_batch_composer').select('*').eq('batch_id', batch_id).execute()
        if result.data:
            return result.data[0]
        return None

    def get_client_thread(self, client_id: str) -> Optional[str]:
        """Get or determine the current thread_id for a client's batches"""
        # Get most recent batch for client to determine thread
        result = self.client.table('v2_batch_composer').select('thread_id, batch_number').eq('client_id', client_id).order('created_at', desc=True).limit(1).execute()

        if result.data and result.data[0].get('thread_id'):
            return result.data[0]['thread_id']
        return None

    def get_recent_batches(self, client_id: str, thread_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent batches in a thread for memory context"""
        result = self.client.table('v2_batch_composer').select('batch_id, directions, distribution_achieved, created_at').eq('client_id', client_id).eq('thread_id', thread_id).eq('status', 'completed').order('batch_number', desc=True).limit(limit).execute()
        return result.data

    def get_existing_leads(self, client_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get recent leads/dossiers for a client to avoid duplicates"""
        result = self.client.table('v2_dossiers').select('target_entity, target_project, lead_score, created_at').eq('client_id', client_id).order('created_at', desc=True).limit(limit).execute()
        return result.data

    def get_next_batch_number(self, client_id: str, thread_id: str) -> int:
        """Get the next batch number for a thread"""
        result = self.client.table('v2_batch_composer').select('batch_number').eq('client_id', client_id).eq('thread_id', thread_id).order('batch_number', desc=True).limit(1).execute()

        if result.data and result.data[0].get('batch_number'):
            return result.data[0]['batch_number'] + 1
        return 1

    # ========================================================================
    # PREP INPUTS (COMPRESSION)
    # ========================================================================

    def create_prep(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prep inputs record"""
        result = self.client.table('v2_prep_inputs').insert(prep_data).execute()
        return result.data[0]

    def update_prep(self, prep_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update prep inputs record"""
        result = self.client.table('v2_prep_inputs').update(updates).eq('prep_id', prep_id).execute()
        return result.data[0]

    def get_prep(self, prep_id: str) -> Optional[Dict[str, Any]]:
        """Get prep record by ID"""
        result = self.client.table('v2_prep_inputs').select('*').eq('prep_id', prep_id).execute()
        if result.data:
            return result.data[0]
        return None

    def update_client_compressed(self, client_id: str, field: str, value: Any) -> Dict[str, Any]:
        """Update a compressed field on v2_clients"""
        result = self.client.table('v2_clients').update({field: value, 'updated_at': datetime.now().isoformat()}).eq('client_id', client_id).execute()
        return result.data[0]

    # ========================================================================
    # CLIENT ONBOARDING
    # ========================================================================

    def create_onboarding(self, onboarding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new onboarding record"""
        result = self.client.table('v2_onboarding').insert(onboarding_data).execute()
        return result.data[0]

    def update_onboarding(self, onboarding_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update onboarding record"""
        result = self.client.table('v2_onboarding').update(updates).eq('onboarding_id', onboarding_id).execute()
        return result.data[0]

    def get_onboarding(self, onboarding_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding record by ID"""
        result = self.client.table('v2_onboarding').select('*').eq('onboarding_id', onboarding_id).execute()
        if result.data:
            return result.data[0]
        return None

    def create_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new client record"""
        result = self.client.table('v2_clients').insert(client_data).execute()
        return result.data[0]

    def update_client(self, client_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update client record"""
        updates['updated_at'] = datetime.now().isoformat()
        result = self.client.table('v2_clients').update(updates).eq('client_id', client_id).execute()
        return result.data[0]


# ============================================================================
# V2 REPOSITORY (Simplified endpoints for Make.com)
# Merged from api/v2/repository.py
# ============================================================================

class V2Repository:
    """Simplified repository for Make.com API endpoints"""

    def __init__(self, client: Optional[Client] = None):
        if client:
            self.client = client
        else:
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
            self.client = create_client(url, key)

    # ---------- Clients ----------

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get a client by ID"""
        result = self.client.table("v2_clients").select("*").eq("id", client_id).single().execute()
        return result.data if result.data else None

    def get_client_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a client by slug"""
        result = self.client.table("v2_clients").select("*").eq("slug", slug).single().execute()
        return result.data if result.data else None

    # ---------- Prompts ----------

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a prompt by prompt_id"""
        result = self.client.table("v2_prompts").select("*").eq("prompt_id", prompt_id).single().execute()
        return result.data if result.data else None

    def get_prompt_version(self, prompt_id: str, version_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a prompt version - if version_number is None, get current version"""
        if version_number is None:
            # Get current version from prompt record
            prompt = self.get_prompt(prompt_id)
            if not prompt:
                return None
            version_number = prompt.get("current_version", 1)

        result = self.client.table("v2_prompt_versions").select("*").eq("prompt_id", prompt_id).eq("version_number", version_number).single().execute()
        return result.data if result.data else None

    def get_prompt_with_content(self, prompt_id: str, version_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get prompt metadata with content from version"""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None

        version = self.get_prompt_version(prompt_id, version_number)
        if version:
            prompt["content"] = version["content"]
            prompt["system_prompt"] = version.get("system_prompt")

        return prompt
