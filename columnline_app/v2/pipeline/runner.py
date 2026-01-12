"""
Pipeline runner - orchestrates the full dossier generation pipeline
"""
import asyncio
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..config import (
    PIPELINE_STEPS, STAGE_ORDER, Stage,
    get_steps_for_stage, get_parallel_groups_for_stage,
    StepConfig, ExecutionMode
)
from ..db.models import (
    PipelineRun, PipelineStatus, StepStatus,
    Dossier, Contact, ContextPack, Claim
)
from ..db.repository import V2Repository
from .state import PipelineState
from .step_executor import StepExecutor


class PipelineRunner:
    """
    Orchestrates the full dossier generation pipeline.

    Execution flow:
    1. FIND_LEAD: search_builder -> signal_discovery -> entity_research -> contact_discovery
    2. ENRICH_LEAD: [5a, 5b, 5c in parallel]
    3. ENRICH_CONTACTS: 6-enrich-contacts -> [6.2-enrich-contact per contact]
    4. COPY: 7a-copy -> 7.2-copy-client-override
    5. INSIGHT: 7b-insight (merge claims)
    6. MEDIA: 8-media
    7. DOSSIER_PLAN: 9-dossier-plan
    """

    def __init__(self, repo: Optional[V2Repository] = None):
        self.repo = repo or V2Repository()
        self.executor = StepExecutor(self.repo)

    async def run_pipeline(
        self,
        client_id: str,
        seed: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> PipelineRun:
        """
        Run the full pipeline for a client.

        Args:
            client_id: The client to run for
            seed: Seed data (company name, domain, etc.)
            config: Optional runtime configuration overrides

        Returns:
            The completed PipelineRun
        """
        config = config or {}

        # Get client
        client = self.repo.get_client(client_id)
        if not client:
            raise ValueError(f"Client not found: {client_id}")

        # Create pipeline run
        pipeline_run = self.repo.create_pipeline_run(PipelineRun(
            client_id=client_id,
            seed=seed,
            config=config,
            status=PipelineStatus.RUNNING,
            started_at=datetime.utcnow(),
        ))

        # Initialize state
        state = PipelineState(
            pipeline_run_id=pipeline_run.id,
            client=client,
            seed=seed,
            started_at=datetime.utcnow(),
        )

        try:
            # Execute stages in order
            for stage in STAGE_ORDER:
                await self._execute_stage(stage, state, pipeline_run.id)

            # Create dossier from results
            dossier = await self._create_dossier(state)

            # Mark complete
            pipeline_run = self.repo.update_pipeline_run(pipeline_run.id, {
                "status": PipelineStatus.COMPLETED.value,
                "dossier_id": dossier.id if dossier else None,
                "steps_completed": state.steps_completed,
                "completed_at": datetime.utcnow().isoformat(),
            })

            return pipeline_run

        except Exception as e:
            # Mark failed
            pipeline_run = self.repo.update_pipeline_run(pipeline_run.id, {
                "status": PipelineStatus.FAILED.value,
                "error_message": str(e),
                "error_step": state.current_step,
                "error_traceback": traceback.format_exc(),
                "steps_completed": state.steps_completed,
                "completed_at": datetime.utcnow().isoformat(),
            })
            raise

    async def _execute_stage(
        self,
        stage: Stage,
        state: PipelineState,
        pipeline_run_id: str
    ):
        """Execute all steps in a stage"""
        groups = get_parallel_groups_for_stage(stage)

        # Execute sequential steps first
        for step_config in groups.get("sequential", []):
            await self._execute_single_step(step_config, state, pipeline_run_id)

        # Execute parallel groups
        for group_name, steps in groups.items():
            if group_name == "sequential":
                continue
            if len(steps) > 1:
                # Run in parallel
                await self._execute_parallel_steps(steps, state, pipeline_run_id)
            elif len(steps) == 1:
                await self._execute_single_step(steps[0], state, pipeline_run_id)

    async def _execute_single_step(
        self,
        step_config: StepConfig,
        state: PipelineState,
        pipeline_run_id: str
    ):
        """Execute a single step"""
        step_id = step_config.prompt_id

        # Update current step
        state.current_step = step_id
        self.repo.update_pipeline_run(pipeline_run_id, {"current_step": step_id})

        # Special handling for contact enrichment (runs per contact)
        if step_id == "6.2-enrich-contact":
            await self._execute_contact_enrichment(step_config, state, pipeline_run_id)
            return

        # Execute step
        step_run, output, claims = await self.executor.execute_step(step_config, state)

        # Update state
        if output:
            state.add_step_output(step_id, output)

        # Store claims
        if claims:
            saved_claims = self.repo.create_claims_batch(claims)
            state.add_claims(saved_claims)

        # Create context pack if applicable
        if step_config.produces_context_pack and step_config.context_pack_type:
            pack_data = self._build_context_pack(step_config.context_pack_type, state, output)
            pack = self.repo.create_context_pack(ContextPack(
                pipeline_run_id=pipeline_run_id,
                step_run_id=step_run.id,
                pack_type=step_config.context_pack_type,
                pack_data=pack_data,
                anchor_claim_ids=[c.claim_id for c in claims] if claims else [],
            ))
            state.add_context_pack(pack)

        # Update pipeline run
        self.repo.update_pipeline_run(pipeline_run_id, {
            "steps_completed": state.steps_completed,
        })

    async def _execute_parallel_steps(
        self,
        steps: List[StepConfig],
        state: PipelineState,
        pipeline_run_id: str
    ):
        """Execute multiple steps in parallel"""
        tasks = []
        for step_config in steps:
            task = self._execute_single_step(step_config, state, pipeline_run_id)
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _execute_contact_enrichment(
        self,
        step_config: StepConfig,
        state: PipelineState,
        pipeline_run_id: str
    ):
        """
        Execute contact enrichment for each discovered contact.
        This runs in parallel for efficiency.
        """
        # Get contacts from previous step output
        contacts_output = state.step_outputs.get("6-enrich-contacts", {})
        contacts_to_enrich = contacts_output.get("contacts", [])

        if not contacts_to_enrich:
            return

        # Limit concurrent enrichments
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_one(contact_data: Dict[str, Any]):
            async with semaphore:
                # Add contact-specific variables to state temporarily
                contact_state = PipelineState(
                    pipeline_run_id=state.pipeline_run_id,
                    client=state.client,
                    seed={**state.seed, **contact_data},
                    step_outputs=state.step_outputs.copy(),
                    claims=state.claims.copy(),
                    context_packs=state.context_packs.copy(),
                )

                try:
                    step_run, output, claims = await self.executor.execute_step(
                        step_config, contact_state
                    )

                    # Create contact record
                    if output:
                        contact = Contact(
                            dossier_id=state.dossier.id if state.dossier else None,
                            pipeline_run_id=pipeline_run_id,
                            first_name=output.get("first_name", contact_data.get("first_name", "")),
                            last_name=output.get("last_name", contact_data.get("last_name", "")),
                            email=output.get("email"),
                            phone=output.get("phone"),
                            title=output.get("title", contact_data.get("title")),
                            organization=output.get("organization", contact_data.get("organization")),
                            linkedin_url=output.get("linkedin_url"),
                            bio=output.get("bio"),
                            why_they_matter=output.get("why_they_matter"),
                            relation_to_signal=output.get("relation_to_signal"),
                            email_copy=output.get("email_copy"),
                            linkedin_copy=output.get("linkedin_copy"),
                            is_primary=contact_data.get("is_primary", False),
                            source="research",
                            enrichment_step_run_id=step_run.id,
                        )
                        state.contacts.append(contact)

                except Exception as e:
                    print(f"Warning: Failed to enrich contact {contact_data}: {e}")

        # Run all enrichments in parallel (with semaphore limit)
        tasks = [enrich_one(c) for c in contacts_to_enrich[:15]]  # Cap at 15 contacts
        await asyncio.gather(*tasks)

        state.steps_completed.append(step_config.prompt_id)

    def _build_context_pack(
        self,
        pack_type: str,
        state: PipelineState,
        latest_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a context pack from state"""
        if pack_type == "signal_to_entity":
            return {
                "signal": latest_output.get("primary_signal"),
                "company_name": latest_output.get("company_name"),
                "domain": latest_output.get("domain"),
                "signal_summary": latest_output.get("signal_summary"),
                "key_facts": latest_output.get("key_facts", []),
            }
        elif pack_type == "entity_to_contacts":
            return {
                "company_name": latest_output.get("company_name") or state.get_variable("company_name"),
                "domain": latest_output.get("domain") or state.get_variable("domain"),
                "key_contacts": latest_output.get("contacts", []),
                "corporate_structure": latest_output.get("corporate_structure"),
                "partner_organizations": latest_output.get("partner_organizations", []),
            }
        elif pack_type == "contacts_to_enrichment":
            return {
                "company_name": state.get_variable("company_name"),
                "merged_claims_count": len(state.merged_claims),
                "contacts_count": len(state.contacts),
                "insights": latest_output.get("insights", {}),
            }
        return latest_output

    async def _create_dossier(self, state: PipelineState) -> Optional[Dossier]:
        """Create dossier from pipeline state"""
        # Get company info from state
        company_name = state.get_variable("company_name")
        if not company_name:
            return None

        dossier = self.repo.create_dossier(Dossier(
            pipeline_run_id=state.pipeline_run_id,
            client_id=state.client.id,
            company_name=company_name,
            company_domain=state.get_variable("domain"),
            lead_score=state.step_outputs.get("9-dossier-plan", {}).get("lead_score"),
            timing_urgency=state.get_variable("timing_urgency"),
            primary_signal=state.get_variable("primary_signal"),
            status="ready",
            sections_completed=list(state.step_outputs.keys()),
        ))

        state.dossier = dossier

        # Save contacts
        for contact in state.contacts:
            contact.dossier_id = dossier.id
            self.repo.create_contact(contact)

        return dossier

    async def run_single_step(
        self,
        pipeline_run_id: str,
        step_id: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a single step in isolation (for testing/debugging).

        Args:
            pipeline_run_id: Existing pipeline run to add step to
            step_id: The step to run
            variables: Override variables (optional)

        Returns:
            Step execution result
        """
        step_config = PIPELINE_STEPS.get(step_id)
        if not step_config:
            raise ValueError(f"Unknown step: {step_id}")

        pipeline_run = self.repo.get_pipeline_run(pipeline_run_id)
        if not pipeline_run:
            raise ValueError(f"Pipeline run not found: {pipeline_run_id}")

        client = self.repo.get_client(pipeline_run.client_id)
        if not client:
            raise ValueError(f"Client not found: {pipeline_run.client_id}")

        # Build state from existing run
        state = PipelineState(
            pipeline_run_id=pipeline_run_id,
            client=client,
            seed=pipeline_run.seed or {},
        )

        # Load existing step outputs
        existing_steps = self.repo.get_step_runs(pipeline_run_id)
        for step_run in existing_steps:
            if step_run.status == StepStatus.COMPLETED and step_run.parsed_output:
                state.add_step_output(step_run.step, step_run.parsed_output)

        # Override with provided variables
        if variables:
            state.seed.update(variables)

        # Execute
        step_run, output, claims = await self.executor.execute_step(step_config, state)

        return {
            "step_run_id": step_run.id,
            "status": step_run.status.value,
            "output": output,
            "claims_count": len(claims),
            "duration_ms": step_run.duration_ms,
        }


# Convenience function for running pipeline
async def run_pipeline(
    client_id: str,
    seed: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> PipelineRun:
    """Run the full pipeline"""
    runner = PipelineRunner()
    return await runner.run_pipeline(client_id, seed, config)


# Sync wrapper for non-async contexts
def run_pipeline_sync(
    client_id: str,
    seed: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> PipelineRun:
    """Sync wrapper for run_pipeline"""
    return asyncio.run(run_pipeline(client_id, seed, config))
