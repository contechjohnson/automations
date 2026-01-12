"""
Supabase repository for v2 pipeline
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client

from .models import (
    ClientConfig, PromptConfig, PromptVersion,
    PipelineRun, StepRun, Claim, MergedClaim, ContextPack,
    Dossier, DossierSection, Contact,
    PipelineStatus, StepStatus
)


def get_supabase() -> Client:
    """Get Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


class V2Repository:
    """Repository for v2 pipeline database operations"""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase()

    # ---------- Clients ----------

    def get_clients(self, status: Optional[str] = "active") -> List[ClientConfig]:
        """Get all clients, optionally filtered by status"""
        query = self.client.table("v2_clients").select("*")
        if status:
            query = query.eq("status", status)
        result = query.order("name").execute()
        return [ClientConfig(**row) for row in result.data]

    def get_client(self, client_id: str) -> Optional[ClientConfig]:
        """Get a client by ID"""
        result = self.client.table("v2_clients").select("*").eq("id", client_id).single().execute()
        return ClientConfig(**result.data) if result.data else None

    def get_client_by_slug(self, slug: str) -> Optional[ClientConfig]:
        """Get a client by slug"""
        result = self.client.table("v2_clients").select("*").eq("slug", slug).single().execute()
        return ClientConfig(**result.data) if result.data else None

    def create_client(self, client: ClientConfig) -> ClientConfig:
        """Create a new client"""
        data = client.model_dump(exclude={"id", "created_at", "updated_at"})
        result = self.client.table("v2_clients").insert(data).execute()
        return ClientConfig(**result.data[0])

    def update_client(self, client_id: str, updates: Dict[str, Any]) -> ClientConfig:
        """Update a client"""
        result = self.client.table("v2_clients").update(updates).eq("id", client_id).execute()
        return ClientConfig(**result.data[0])

    # ---------- Prompts ----------

    def get_prompts(self, is_active: bool = True) -> List[PromptConfig]:
        """Get all prompts"""
        query = self.client.table("v2_prompts").select("*")
        if is_active is not None:
            query = query.eq("is_active", is_active)
        result = query.order("step_order").execute()
        return [PromptConfig(**row) for row in result.data]

    def get_prompt(self, prompt_id: str) -> Optional[PromptConfig]:
        """Get a prompt by prompt_id"""
        result = self.client.table("v2_prompts").select("*").eq("prompt_id", prompt_id).single().execute()
        return PromptConfig(**result.data) if result.data else None

    def get_prompt_with_content(self, prompt_id: str) -> Optional[PromptConfig]:
        """Get prompt with current version content loaded"""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None

        # Try to load from file first
        prompt_file = f"prompts/v2/{prompt_id}.md"
        if os.path.exists(prompt_file):
            with open(prompt_file, "r") as f:
                prompt.content = f.read()
        else:
            # Fall back to database version
            version = self.get_prompt_version(prompt_id, prompt.current_version)
            if version:
                prompt.content = version.content

        return prompt

    def update_prompt(self, prompt_id: str, updates: Dict[str, Any]) -> PromptConfig:
        """Update prompt metadata"""
        result = self.client.table("v2_prompts").update(updates).eq("prompt_id", prompt_id).execute()
        return PromptConfig(**result.data[0])

    # ---------- Prompt Versions ----------

    def get_prompt_versions(self, prompt_id: str) -> List[PromptVersion]:
        """Get all versions of a prompt"""
        result = self.client.table("v2_prompt_versions").select("*").eq("prompt_id", prompt_id).order("version_number", desc=True).execute()
        return [PromptVersion(**row) for row in result.data]

    def get_prompt_version(self, prompt_id: str, version_number: int) -> Optional[PromptVersion]:
        """Get a specific version of a prompt"""
        result = self.client.table("v2_prompt_versions").select("*").eq("prompt_id", prompt_id).eq("version_number", version_number).single().execute()
        return PromptVersion(**result.data) if result.data else None

    def create_prompt_version(self, version: PromptVersion) -> PromptVersion:
        """Create a new prompt version"""
        data = version.model_dump(exclude={"id", "created_at"})
        result = self.client.table("v2_prompt_versions").insert(data).execute()

        # Update current_version on prompt
        self.client.table("v2_prompts").update({"current_version": version.version_number}).eq("prompt_id", version.prompt_id).execute()

        return PromptVersion(**result.data[0])

    # ---------- Pipeline Runs ----------

    def get_pipeline_runs(
        self,
        client_id: Optional[str] = None,
        status: Optional[PipelineStatus] = None,
        limit: int = 50
    ) -> List[PipelineRun]:
        """Get pipeline runs with optional filters"""
        query = self.client.table("v2_pipeline_runs").select("*")
        if client_id:
            query = query.eq("client_id", client_id)
        if status:
            query = query.eq("status", status.value)
        result = query.order("created_at", desc=True).limit(limit).execute()
        return [PipelineRun(**row) for row in result.data]

    def get_pipeline_run(self, run_id: str) -> Optional[PipelineRun]:
        """Get a pipeline run by ID"""
        result = self.client.table("v2_pipeline_runs").select("*").eq("id", run_id).single().execute()
        return PipelineRun(**result.data) if result.data else None

    def create_pipeline_run(self, run: PipelineRun) -> PipelineRun:
        """Create a new pipeline run"""
        data = run.model_dump(exclude={"id", "created_at"})
        # Convert enum to string
        data["status"] = data["status"].value if isinstance(data["status"], PipelineStatus) else data["status"]
        # Convert datetime to ISO string
        if data.get("started_at") and isinstance(data["started_at"], datetime):
            data["started_at"] = data["started_at"].isoformat()
        if data.get("completed_at") and isinstance(data["completed_at"], datetime):
            data["completed_at"] = data["completed_at"].isoformat()
        result = self.client.table("v2_pipeline_runs").insert(data).execute()
        return PipelineRun(**result.data[0])

    def update_pipeline_run(self, run_id: str, updates: Dict[str, Any]) -> PipelineRun:
        """Update a pipeline run"""
        # Convert enums
        if "status" in updates and isinstance(updates["status"], PipelineStatus):
            updates["status"] = updates["status"].value
        result = self.client.table("v2_pipeline_runs").update(updates).eq("id", run_id).execute()
        return PipelineRun(**result.data[0])

    # ---------- Step Runs ----------

    def get_step_runs(self, pipeline_run_id: str) -> List[StepRun]:
        """Get all steps for a pipeline run"""
        result = self.client.table("v2_step_runs").select("*").eq("pipeline_run_id", pipeline_run_id).order("created_at").execute()
        return [StepRun(**row) for row in result.data]

    def get_step_run(self, step_run_id: str) -> Optional[StepRun]:
        """Get a step run by ID"""
        result = self.client.table("v2_step_runs").select("*").eq("id", step_run_id).single().execute()
        return StepRun(**result.data) if result.data else None

    def get_step_run_by_step(self, pipeline_run_id: str, step: str) -> Optional[StepRun]:
        """Get a step run by pipeline_run_id and step name"""
        result = self.client.table("v2_step_runs").select("*").eq("pipeline_run_id", pipeline_run_id).eq("step", step).single().execute()
        return StepRun(**result.data) if result.data else None

    def create_step_run(self, step_run: StepRun) -> StepRun:
        """Create a new step run"""
        data = step_run.model_dump(exclude={"id", "created_at"})
        data["status"] = data["status"].value if isinstance(data["status"], StepStatus) else data["status"]
        # Convert datetime to ISO string
        if data.get("started_at") and isinstance(data["started_at"], datetime):
            data["started_at"] = data["started_at"].isoformat()
        if data.get("completed_at") and isinstance(data["completed_at"], datetime):
            data["completed_at"] = data["completed_at"].isoformat()
        result = self.client.table("v2_step_runs").insert(data).execute()
        return StepRun(**result.data[0])

    def update_step_run(self, step_run_id: str, updates: Dict[str, Any]) -> StepRun:
        """Update a step run"""
        if "status" in updates and isinstance(updates["status"], StepStatus):
            updates["status"] = updates["status"].value
        result = self.client.table("v2_step_runs").update(updates).eq("id", step_run_id).execute()
        return StepRun(**result.data[0])

    # ---------- Claims ----------

    def get_claims(self, pipeline_run_id: str, is_merged: Optional[bool] = None) -> List[Claim]:
        """Get claims for a pipeline run"""
        query = self.client.table("v2_claims").select("*").eq("pipeline_run_id", pipeline_run_id)
        if is_merged is not None:
            query = query.eq("is_merged", is_merged)
        result = query.order("created_at").execute()
        return [Claim(**row) for row in result.data]

    def create_claim(self, claim: Claim) -> Claim:
        """Create a new claim"""
        data = claim.model_dump(exclude={"id", "created_at"})
        # Convert enums
        data["claim_type"] = data["claim_type"].value if hasattr(data["claim_type"], "value") else data["claim_type"]
        data["source_tier"] = data["source_tier"].value if hasattr(data["source_tier"], "value") else data["source_tier"]
        data["confidence"] = data["confidence"].value if hasattr(data["confidence"], "value") else data["confidence"]
        result = self.client.table("v2_claims").insert(data).execute()
        return Claim(**result.data[0])

    def create_claims_batch(self, claims: List[Claim]) -> List[Claim]:
        """Create multiple claims"""
        from datetime import date as date_type
        data_list = []
        for claim in claims:
            data = claim.model_dump(exclude={"id", "created_at"})
            data["claim_type"] = data["claim_type"].value if hasattr(data["claim_type"], "value") else data["claim_type"]
            data["source_tier"] = data["source_tier"].value if hasattr(data["source_tier"], "value") else data["source_tier"]
            data["confidence"] = data["confidence"].value if hasattr(data["confidence"], "value") else data["confidence"]
            # Convert date objects to strings for JSON serialization
            if data.get("date_in_claim"):
                if isinstance(data["date_in_claim"], (date_type, datetime)):
                    data["date_in_claim"] = str(data["date_in_claim"])
            data_list.append(data)
        result = self.client.table("v2_claims").insert(data_list).execute()
        return [Claim(**row) for row in result.data]

    # ---------- Merged Claims ----------

    def get_merged_claims(self, pipeline_run_id: str) -> List[MergedClaim]:
        """Get merged claims for a pipeline run"""
        result = self.client.table("v2_merged_claims").select("*").eq("pipeline_run_id", pipeline_run_id).order("created_at").execute()
        return [MergedClaim(**row) for row in result.data]

    def create_merged_claim(self, claim: MergedClaim) -> MergedClaim:
        """Create a merged claim"""
        data = claim.model_dump(exclude={"id", "created_at"})
        data["claim_type"] = data["claim_type"].value if hasattr(data["claim_type"], "value") else data["claim_type"]
        data["confidence"] = data["confidence"].value if hasattr(data["confidence"], "value") else data["confidence"]
        result = self.client.table("v2_merged_claims").insert(data).execute()
        return MergedClaim(**result.data[0])

    # ---------- Context Packs ----------

    def get_context_pack(self, pipeline_run_id: str, pack_type: str) -> Optional[ContextPack]:
        """Get a context pack by type"""
        result = self.client.table("v2_context_packs").select("*").eq("pipeline_run_id", pipeline_run_id).eq("pack_type", pack_type).single().execute()
        return ContextPack(**result.data) if result.data else None

    def create_context_pack(self, pack: ContextPack) -> ContextPack:
        """Create a context pack"""
        data = pack.model_dump(exclude={"id", "created_at"})
        result = self.client.table("v2_context_packs").insert(data).execute()
        return ContextPack(**result.data[0])

    # ---------- Dossiers ----------

    def get_dossier(self, dossier_id: str) -> Optional[Dossier]:
        """Get a dossier by ID"""
        result = self.client.table("v2_dossiers").select("*").eq("id", dossier_id).single().execute()
        return Dossier(**result.data) if result.data else None

    def get_dossier_by_pipeline(self, pipeline_run_id: str) -> Optional[Dossier]:
        """Get dossier by pipeline run"""
        result = self.client.table("v2_dossiers").select("*").eq("pipeline_run_id", pipeline_run_id).single().execute()
        return Dossier(**result.data) if result.data else None

    def create_dossier(self, dossier: Dossier) -> Dossier:
        """Create a dossier"""
        data = dossier.model_dump(exclude={"id", "created_at", "updated_at"})
        result = self.client.table("v2_dossiers").insert(data).execute()
        return Dossier(**result.data[0])

    def update_dossier(self, dossier_id: str, updates: Dict[str, Any]) -> Dossier:
        """Update a dossier"""
        result = self.client.table("v2_dossiers").update(updates).eq("id", dossier_id).execute()
        return Dossier(**result.data[0])

    # ---------- Dossier Sections ----------

    def get_dossier_sections(self, dossier_id: str) -> List[DossierSection]:
        """Get all sections for a dossier"""
        result = self.client.table("v2_dossier_sections").select("*").eq("dossier_id", dossier_id).execute()
        return [DossierSection(**row) for row in result.data]

    def create_dossier_section(self, section: DossierSection) -> DossierSection:
        """Create a dossier section"""
        data = section.model_dump(exclude={"id", "created_at", "updated_at"})
        result = self.client.table("v2_dossier_sections").insert(data).execute()
        return DossierSection(**result.data[0])

    # ---------- Contacts ----------

    def get_contacts(self, dossier_id: str) -> List[Contact]:
        """Get all contacts for a dossier"""
        result = self.client.table("v2_contacts").select("*").eq("dossier_id", dossier_id).order("is_primary", desc=True).execute()
        return [Contact(**row) for row in result.data]

    def create_contact(self, contact: Contact) -> Contact:
        """Create a contact"""
        data = contact.model_dump(exclude={"id", "created_at", "updated_at"})
        if data.get("confidence"):
            data["confidence"] = data["confidence"].value if hasattr(data["confidence"], "value") else data["confidence"]
        result = self.client.table("v2_contacts").insert(data).execute()
        return Contact(**result.data[0])

    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Contact:
        """Update a contact"""
        if updates.get("confidence") and hasattr(updates["confidence"], "value"):
            updates["confidence"] = updates["confidence"].value
        result = self.client.table("v2_contacts").update(updates).eq("id", contact_id).execute()
        return Contact(**result.data[0])

    # ---------- Merge Stats ----------

    def create_merge_stats(
        self,
        pipeline_run_id: str,
        input_claims_count: int,
        output_claims_count: int,
        duplicates_merged: int,
        conflicts_resolved: int
    ) -> Dict[str, Any]:
        """Create merge stats record"""
        data = {
            "pipeline_run_id": pipeline_run_id,
            "input_claims_count": input_claims_count,
            "output_claims_count": output_claims_count,
            "duplicates_merged": duplicates_merged,
            "conflicts_resolved": conflicts_resolved,
        }
        result = self.client.table("v2_merge_stats").insert(data).execute()
        return result.data[0] if result.data else {}

    def get_merge_stats(self, pipeline_run_id: str) -> Optional[Dict[str, Any]]:
        """Get merge stats for a pipeline run"""
        result = self.client.table("v2_merge_stats").select("*").eq("pipeline_run_id", pipeline_run_id).single().execute()
        return result.data if result.data else None

    # ---------- Views / Aggregates ----------

    def get_pipeline_run_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline run with summary stats"""
        result = self.client.table("v2_pipeline_run_summary").select("*").eq("id", run_id).single().execute()
        return result.data if result.data else None

    def get_prompt_last_runs(self, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get last run for each prompt"""
        query = self.client.table("v2_prompt_last_runs").select("*")
        if client_id:
            query = query.eq("client_id", client_id)
        result = query.execute()
        return result.data

    def get_claims_summary(self, pipeline_run_id: str) -> List[Dict[str, Any]]:
        """Get claims summary by type"""
        result = self.client.table("v2_claims_summary").select("*").eq("pipeline_run_id", pipeline_run_id).execute()
        return result.data
