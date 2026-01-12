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
        Run the full pipeline for a client (creates new pipeline run).

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

        return await self._execute_pipeline(pipeline_run, client, seed, config)

    async def run_pipeline_with_id(
        self,
        pipeline_run_id: str,
        client_id: str,
        seed: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> PipelineRun:
        """
        Run the pipeline using an existing pipeline run ID.

        Args:
            pipeline_run_id: Existing pipeline run to update
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

        # Get existing pipeline run
        pipeline_run = self.repo.get_pipeline_run(pipeline_run_id)
        if not pipeline_run:
            raise ValueError(f"Pipeline run not found: {pipeline_run_id}")

        # Update to running status
        pipeline_run = self.repo.update_pipeline_run(pipeline_run_id, {
            "status": PipelineStatus.RUNNING.value,
            "started_at": datetime.utcnow().isoformat(),
        })

        return await self._execute_pipeline(pipeline_run, client, seed, config)

    async def _execute_pipeline(
        self,
        pipeline_run: PipelineRun,
        client,
        seed: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PipelineRun:
        """
        Execute the pipeline stages.

        Args:
            pipeline_run: The pipeline run record
            client: The client config
            seed: Seed data
            config: Runtime configuration

        Returns:
            The completed PipelineRun
        """
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

        # Special handling for copy generation (runs per contact)
        if step_config.per_contact and step_id in ["7a-copy", "7.2-copy-client-override"]:
            await self._execute_per_contact_copy(step_config, state, pipeline_run_id)
            return

        # Special handling for claims merge at insight step
        if step_config.merges_claims and step_id == "7b-insight":
            await self._execute_claims_merge(step_config, state, pipeline_run_id)
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

        # Create context pack via LLM if applicable
        if step_config.produces_context_pack and step_config.context_pack_type:
            # Use LLM-generated context pack
            pack_data = await self.executor.generate_context_pack(
                state,
                step_config.context_pack_type,
                self._get_next_step(step_id)
            )
            if pack_data:
                pack = self.repo.create_context_pack(ContextPack(
                    pipeline_run_id=pipeline_run_id,
                    step_run_id=step_run.id,
                    pack_type=step_config.context_pack_type,
                    pack_data=pack_data,
                    anchor_claim_ids=pack_data.get("anchor_claim_ids", []),
                ))
                state.add_context_pack(pack)

        # Mark step completed
        state.steps_completed.append(step_id)

        # Update pipeline run
        self.repo.update_pipeline_run(pipeline_run_id, {
            "steps_completed": state.steps_completed,
        })

    def _get_next_step(self, current_step: str) -> str:
        """Get the next step in the pipeline for context pack targeting"""
        step_order = list(PIPELINE_STEPS.keys())
        try:
            idx = step_order.index(current_step)
            if idx + 1 < len(step_order):
                return step_order[idx + 1]
        except ValueError:
            pass
        return "next"

    async def _execute_claims_merge(
        self,
        step_config: StepConfig,
        state: PipelineState,
        pipeline_run_id: str
    ):
        """Execute claims merge at the insight step"""
        step_id = step_config.prompt_id
        print(f"Executing claims merge at {step_id}...")

        # Run claims merge LLM
        merge_result, merged_claims = await self.executor.execute_claims_merge(state)

        if merge_result:
            state.add_step_output(step_id, merge_result)

            # Store merged claims
            if merged_claims:
                saved_claims = self.repo.create_claims_batch(merged_claims)
                state.merged_claims = saved_claims

            # Store merge stats
            merge_stats = merge_result.get("merge_stats", {})
            if merge_stats:
                self.repo.create_merge_stats(
                    pipeline_run_id=pipeline_run_id,
                    input_claims_count=merge_stats.get("input_claims", 0),
                    output_claims_count=merge_stats.get("output_claims", 0),
                    duplicates_merged=merge_stats.get("duplicates_merged", 0),
                    conflicts_resolved=merge_stats.get("conflicts_resolved", 0),
                )

        # Generate context pack after merge
        if step_config.produces_context_pack and step_config.context_pack_type:
            pack_data = await self.executor.generate_context_pack(
                state,
                step_config.context_pack_type,
                "writers"
            )
            if pack_data:
                pack = self.repo.create_context_pack(ContextPack(
                    pipeline_run_id=pipeline_run_id,
                    pack_type=step_config.context_pack_type,
                    pack_data=pack_data,
                    anchor_claim_ids=pack_data.get("anchor_claim_ids", []),
                ))
                state.add_context_pack(pack)

        state.steps_completed.append(step_id)
        self.repo.update_pipeline_run(pipeline_run_id, {
            "steps_completed": state.steps_completed,
        })

    async def _execute_per_contact_copy(
        self,
        step_config: StepConfig,
        state: PipelineState,
        pipeline_run_id: str
    ):
        """Execute copy generation for each contact"""
        step_id = step_config.prompt_id
        print(f"Executing per-contact copy at {step_id}...")

        # Get contacts from state
        contacts = state.contacts
        if not contacts:
            print("No contacts for copy generation")
            state.steps_completed.append(step_id)
            return

        # Limit concurrent copy generations
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_copy_for_contact(contact):
            async with semaphore:
                # Build contact-specific state
                contact_vars = {
                    "contact_first_name": contact.first_name,
                    "contact_last_name": contact.last_name,
                    "contact_name": f"{contact.first_name} {contact.last_name}",
                    "contact_title": contact.title or "",
                    "contact_org": contact.organization or "",
                    "contact_bio": contact.bio or "",
                    "contact_why_they_matter": contact.why_they_matter or "",
                }
                contact_state = PipelineState(
                    pipeline_run_id=state.pipeline_run_id,
                    client=state.client,
                    seed={**state.seed, **contact_vars},
                    step_outputs=state.step_outputs.copy(),
                    claims=state.claims.copy(),
                    merged_claims=state.merged_claims.copy(),
                    context_packs=state.context_packs.copy(),
                )

                try:
                    step_run, output, _ = await self.executor.execute_step(
                        step_config, contact_state
                    )

                    # Update contact with generated copy
                    if output:
                        contact.email_copy = output.get("email_copy", contact.email_copy)
                        contact.linkedin_copy = output.get("linkedin_copy", contact.linkedin_copy)
                        # Save updated contact
                        self.repo.update_contact(contact.id, {
                            "email_copy": contact.email_copy,
                            "linkedin_copy": contact.linkedin_copy,
                        })

                except Exception as e:
                    print(f"Warning: Copy generation failed for {contact.first_name}: {e}")

        # Run copy generation for all contacts in parallel
        tasks = [generate_copy_for_contact(c) for c in contacts[:15]]  # Cap at 15
        await asyncio.gather(*tasks)

        state.steps_completed.append(step_id)
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
        latest_output: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build a context pack from state"""
        # Handle None output gracefully
        output = latest_output or {}

        if pack_type == "signal_to_entity":
            return {
                "signal": output.get("primary_signal") or state.get_variable("signal_type"),
                "company_name": output.get("company_name") or state.get_variable("company_name"),
                "domain": output.get("domain") or state.get_variable("company_domain"),
                "signal_summary": output.get("signal_summary") or state.get_variable("signal_summary"),
                "key_facts": output.get("key_facts", []),
            }
        elif pack_type == "entity_to_contacts":
            return {
                "company_name": output.get("company_name") or state.get_variable("company_name"),
                "domain": output.get("domain") or state.get_variable("company_domain"),
                "key_contacts": output.get("contacts", []),
                "corporate_structure": output.get("corporate_structure"),
                "partner_organizations": output.get("partner_organizations", []),
            }
        elif pack_type == "contacts_to_enrichment":
            return {
                "company_name": state.get_variable("company_name"),
                "merged_claims_count": len(state.merged_claims),
                "contacts_count": len(state.contacts),
                "insights": output.get("insights", {}),
            }
        return output or {}

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
