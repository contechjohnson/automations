"""
Pipeline runner - orchestrates the full dossier generation pipeline

Architecture (aligned with Make.com flow):
- FIND_LEAD: 1-search-builder -> 2-signal-discovery -> 3-entity-research -> 4-contact-discovery
- ENRICH_LEAD: [5a, 5b, 5c, 8-media in parallel]
- INSIGHT: 7b-insight (merge all claims, create context pack for writers)
- FINAL: 9-dossier-plan, then [6 writers + contact enrichment in parallel]
"""
import asyncio
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..config import (
    PIPELINE_STEPS, STAGE_ORDER, Stage,
    get_steps_for_stage, get_parallel_groups_for_stage,
    get_writer_steps, get_writer_section_keys,
    StepConfig, ExecutionMode
)
from ..db.models import (
    PipelineRun, PipelineStatus, StepStatus, StepRun,
    Dossier, Contact, ContextPack, Claim
)
from ..db.repository import V2Repository
from .state import PipelineState
from .step_executor import StepExecutor


class PipelineRunner:
    """
    Orchestrates the full dossier generation pipeline.

    Execution flow (aligned with Make.com):
    1. FIND_LEAD: search_builder -> signal_discovery -> entity_research -> contact_discovery
    2. ENRICH_LEAD: [5a, 5b, 5c, 8-media in parallel]
    3. INSIGHT: 7b-insight (merge claims, build context pack)
    4. FINAL: 9-dossier-plan, then [6 writers + 6-enrich-contacts + 6.2 per-contact in parallel]
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

        # Special handling for writer steps - need to inject routed claims
        if step_config.is_writer:
            await self._execute_writer_step(step_config, state, pipeline_run_id)
            return

        # Execute step
        step_run, output, claims = await self.executor.execute_step(step_config, state)

        # Update state
        if output:
            state.add_step_output(step_id, output)

        # Store claims
        if claims:
            print(f"  Extracted {len(claims)} claims from {step_id}")
            saved_claims = self.repo.create_claims_batch(claims)
            state.add_claims(saved_claims)
            print(f"  Total claims in state: {len(state.claims)}")

        # Create context pack if applicable
        if step_config.produces_context_pack and step_config.context_pack_type:
            pack_type = step_config.context_pack_type

            # For signal_to_entity pack from step 2, extract directly from step output (no LLM needed)
            if pack_type == "signal_to_entity" and step_id == "2-signal-discovery":
                pack_data = self._build_context_pack(pack_type, state, output)
                print(f"Built signal_to_entity pack from step 2: {list(pack_data.keys()) if pack_data else 'None'}")
            else:
                # Use LLM-generated context pack for other types
                pack_data = await self.executor.generate_context_pack(
                    state,
                    pack_type,
                    self._get_next_step(step_id)
                )

            if pack_data:
                pack = self.repo.create_context_pack(ContextPack(
                    pipeline_run_id=pipeline_run_id,
                    step_run_id=step_run.id,
                    pack_type=pack_type,
                    pack_data=pack_data,
                    anchor_claim_ids=pack_data.get("anchor_claim_ids", []) if isinstance(pack_data, dict) else [],
                ))
                state.add_context_pack(pack)
                print(f"Added context pack '{pack_type}' to state")

        # Mark step completed (avoid duplicates)
        if step_id not in state.steps_completed:
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
        import time
        step_id = step_config.prompt_id
        print(f"Executing claims merge at {step_id}...")
        print(f"  Claims in state: {len(state.claims)}")
        print(f"  Steps completed: {state.steps_completed}")

        start_time = time.time()

        # Create step run record FIRST
        step_run = self.repo.create_step_run(StepRun(
            pipeline_run_id=pipeline_run_id,
            step=step_id,
            prompt_id=step_id,
            status=StepStatus.RUNNING,
            model=step_config.model,
            started_at=datetime.utcnow(),
        ))

        try:
            # Capture input claims as input_variables for visibility
            input_claims_preview = [
                {
                    "claim_id": c.claim_id,
                    "claim_type": c.claim_type.value if hasattr(c.claim_type, 'value') else c.claim_type,
                    "statement": c.statement[:100] + "..." if len(c.statement) > 100 else c.statement,
                    "source_step": c.source_step,
                }
                for c in state.claims[:20]  # Preview first 20
            ]
            input_vars = {
                "company_name": state.get_variable("company_name"),
                "total_claims_to_merge": len(state.claims),
                "claims_preview": input_claims_preview,
                "claims_by_step": self._count_claims_by_step(state.claims),
            }

            self.repo.update_step_run(step_run.id, {
                "input_variables": input_vars,
            })

            # Run claims merge LLM
            merge_result, merged_claims = await self.executor.execute_claims_merge(state)

            duration_ms = int((time.time() - start_time) * 1000)

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

                # Update step run with success
                self.repo.update_step_run(step_run.id, {
                    "status": StepStatus.COMPLETED.value,
                    "parsed_output": merge_result,
                    "duration_ms": duration_ms,
                    "completed_at": datetime.utcnow().isoformat(),
                })

            else:
                # No result - still mark completed but note it
                self.repo.update_step_run(step_run.id, {
                    "status": StepStatus.COMPLETED.value,
                    "parsed_output": {"warning": "No claims to merge or merge returned empty"},
                    "duration_ms": duration_ms,
                    "completed_at": datetime.utcnow().isoformat(),
                })

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
                        step_run_id=step_run.id,
                        pack_type=step_config.context_pack_type,
                        pack_data=pack_data,
                        anchor_claim_ids=pack_data.get("anchor_claim_ids", []),
                    ))
                    state.add_context_pack(pack)

            if step_id not in state.steps_completed:
                state.steps_completed.append(step_id)
            self.repo.update_pipeline_run(pipeline_run_id, {
                "steps_completed": state.steps_completed,
            })

        except Exception as e:
            # Record failure
            duration_ms = int((time.time() - start_time) * 1000)
            self.repo.update_step_run(step_run.id, {
                "status": StepStatus.FAILED.value,
                "error_message": str(e),
                "error_traceback": traceback.format_exc(),
                "duration_ms": duration_ms,
                "completed_at": datetime.utcnow().isoformat(),
            })
            raise

    def _count_claims_by_step(self, claims: List[Claim]) -> Dict[str, int]:
        """Count claims by source step for visibility"""
        counts = {}
        for claim in claims:
            step = claim.source_step or "unknown"
            counts[step] = counts.get(step, 0) + 1
        return counts

    async def _execute_writer_step(
        self,
        step_config: StepConfig,
        state: PipelineState,
        pipeline_run_id: str
    ):
        """
        Execute a dossier section writer step.

        Writers receive:
        - claims: Routed claims for this section from dossier plan
        - resolved_contacts: Merged contacts from insight step
        - resolved_signals: Merged signals from insight step
        - Client context (name, services, differentiators, etc.)
        """
        import time
        import json
        step_id = step_config.prompt_id
        section_key = step_config.section_key

        print(f"Executing writer step: {step_id} (section: {section_key})")
        start_time = time.time()

        # Create step run record
        step_run = self.repo.create_step_run(StepRun(
            pipeline_run_id=pipeline_run_id,
            step=step_id,
            prompt_id=step_id,
            status=StepStatus.RUNNING,
            model=step_config.model,
            started_at=datetime.utcnow(),
        ))

        try:
            # Get dossier plan output for routing
            dossier_plan = state.step_outputs.get("9-dossier-plan", {})
            section_routing = dossier_plan.get("section_routing", {})

            # Get routing guidance from dossier plan (used as hints, not filters)
            section_info = section_routing.get(section_key.upper(), {}) if section_key else {}
            routed_claim_ids = section_info.get("claim_ids", [])

            # Use merged claims if available, otherwise raw claims
            claims_pool = state.merged_claims if state.merged_claims else state.claims

            # Helper to serialize a claim
            def serialize_claim(c):
                return {
                    "claim_id": c.claim_id,
                    "claim_type": c.claim_type.value if hasattr(c.claim_type, 'value') else c.claim_type,
                    "statement": c.statement,
                    "entities": c.entities,
                    "source_url": c.source_url,
                    "source_name": c.source_name,
                    "confidence": c.confidence.value if hasattr(c.confidence, 'value') else c.confidence,
                }

            # ALL claims for the writer (Option A: full context)
            all_claims = [serialize_claim(c) for c in claims_pool]

            # Routed claims as guidance (subset most relevant to this section)
            routed_claims = [serialize_claim(c) for c in claims_pool if c.claim_id in routed_claim_ids] if routed_claim_ids else []

            # Get resolved contacts and signals from insight
            insight_output = state.step_outputs.get("7b-insight", {})
            resolved_contacts = insight_output.get("resolved_contacts", [])
            resolved_signals = insight_output.get("resolved_signals", [])

            # Build writer-specific variables - writers get BOTH all claims and routed claims
            writer_vars = {
                "claims": json.dumps(all_claims, indent=2),  # ALL claims for full context
                "all_claims": json.dumps(all_claims, indent=2),  # Explicit all claims variable
                "routed_claims": json.dumps(routed_claims, indent=2),  # Routed as guidance
                "resolved_contacts": json.dumps(resolved_contacts, indent=2),
                "resolved_signals": json.dumps(resolved_signals, indent=2),
                "section_key": section_key,
                "coverage_notes": section_info.get("coverage_notes", ""),
            }

            # Add to state seed for interpolation
            writer_state = PipelineState(
                pipeline_run_id=state.pipeline_run_id,
                client=state.client,
                seed={**state.seed, **writer_vars},
                step_outputs=state.step_outputs.copy(),
                claims=state.claims.copy(),
                merged_claims=state.merged_claims.copy(),
                context_packs=state.context_packs.copy(),
            )

            # Update step run with input
            self.repo.update_step_run(step_run.id, {
                "input_variables": {
                    "section_key": section_key,
                    "all_claims_count": len(all_claims),
                    "routed_claims_count": len(routed_claims),
                    "resolved_contacts_count": len(resolved_contacts),
                    "resolved_signals_count": len(resolved_signals),
                },
            })

            # Execute the step
            step_run, output, _ = await self.executor.execute_step(step_config, writer_state)

            # Store writer output in state
            if output:
                state.add_step_output(step_id, output)

                # Also store in writer_sections for dossier assembly
                if not hasattr(state, 'writer_sections'):
                    state.writer_sections = {}
                state.writer_sections[section_key] = output

            duration_ms = int((time.time() - start_time) * 1000)

            # Mark step completed (avoid duplicates)
            if step_id not in state.steps_completed:
                state.steps_completed.append(step_id)
            self.repo.update_pipeline_run(pipeline_run_id, {
                "steps_completed": state.steps_completed,
            })

            print(f"  Writer {section_key} completed in {duration_ms}ms")

        except Exception as e:
            # Record failure
            duration_ms = int((time.time() - start_time) * 1000)
            self.repo.update_step_run(step_run.id, {
                "status": StepStatus.FAILED.value,
                "error_message": str(e),
                "error_traceback": traceback.format_exc(),
                "duration_ms": duration_ms,
                "completed_at": datetime.utcnow().isoformat(),
            })
            raise

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
            if step_id not in state.steps_completed:
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

        if step_id not in state.steps_completed:
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
        Execute full contact enrichment pipeline for each discovered contact.
        Per contact flow: Enrich (6.2) -> Copy (7a) -> Client Copy (7.2)
        All contacts process in parallel with semaphore limit.
        """
        import json

        # Get contacts from previous step output
        contacts_output = state.step_outputs.get("6-enrich-contacts", {})
        contacts_to_enrich = contacts_output.get("contacts", [])

        if not contacts_to_enrich:
            print("No contacts to enrich")
            return

        print(f"Starting contact enrichment for {len(contacts_to_enrich)} contacts...")

        # Get copy generation step configs
        copy_config = PIPELINE_STEPS.get("7a-copy")
        client_copy_config = PIPELINE_STEPS.get("7.2-copy-client-override")

        # Limit concurrent enrichments
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_one(contact_data: Dict[str, Any]):
            async with semaphore:
                contact_name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}"
                print(f"  Enriching contact: {contact_name}")

                # Build contact-specific state for enrichment
                contact_state = PipelineState(
                    pipeline_run_id=state.pipeline_run_id,
                    client=state.client,
                    seed={**state.seed, **contact_data},
                    step_outputs=state.step_outputs.copy(),
                    claims=state.claims.copy(),
                    merged_claims=state.merged_claims.copy() if state.merged_claims else [],
                    context_packs=state.context_packs.copy(),
                )

                contact = None
                try:
                    # Step 1: Enrich contact (6.2-enrich-contact)
                    step_run, enrich_output, _ = await self.executor.execute_step(
                        step_config, contact_state
                    )

                    if not enrich_output:
                        print(f"    No enrichment output for {contact_name}")
                        return

                    # Create contact record with enrichment data
                    contact = Contact(
                        dossier_id=state.dossier.id if state.dossier else None,
                        pipeline_run_id=pipeline_run_id,
                        first_name=enrich_output.get("first_name", contact_data.get("first_name", "")),
                        last_name=enrich_output.get("last_name", contact_data.get("last_name", "")),
                        email=enrich_output.get("email"),
                        phone=enrich_output.get("phone"),
                        title=enrich_output.get("title", contact_data.get("title")),
                        organization=enrich_output.get("organization", contact_data.get("organization")),
                        linkedin_url=enrich_output.get("linkedin_url"),
                        bio=enrich_output.get("bio"),
                        tenure=enrich_output.get("tenure"),
                        why_they_matter=enrich_output.get("why_they_matter"),
                        relation_to_signal=enrich_output.get("relation_to_signal"),
                        interesting_facts=enrich_output.get("interesting_facts"),
                        is_primary=contact_data.get("is_primary", False),
                        source="research",
                        enrichment_step_run_id=step_run.id,
                    )

                    # Step 2: Generate copy (7a-copy) if config exists
                    if copy_config:
                        # Build copy state with enriched contact info
                        copy_vars = {
                            "contact_first_name": contact.first_name,
                            "contact_last_name": contact.last_name,
                            "contact_name": f"{contact.first_name} {contact.last_name}",
                            "contact_title": contact.title or "",
                            "contact_org": contact.organization or "",
                            "contact_bio": contact.bio or "",
                            "contact_email": contact.email or "",
                            "contact_linkedin": contact.linkedin_url or "",
                            "contact_why_they_matter": contact.why_they_matter or "",
                            "contact_relation_to_signal": contact.relation_to_signal or "",
                            "contact_interesting_facts": contact.interesting_facts or "",
                        }
                        copy_state = PipelineState(
                            pipeline_run_id=state.pipeline_run_id,
                            client=state.client,
                            seed={**state.seed, **copy_vars},
                            step_outputs=state.step_outputs.copy(),
                            claims=state.claims.copy(),
                            merged_claims=state.merged_claims.copy() if state.merged_claims else [],
                            context_packs=state.context_packs.copy(),
                        )

                        try:
                            _, copy_output, _ = await self.executor.execute_step(copy_config, copy_state)
                            if copy_output:
                                # Extract copy from output (may be nested in outreach array)
                                outreach = copy_output.get("outreach", [])
                                if outreach and len(outreach) > 0:
                                    first_outreach = outreach[0]
                                    email_data = first_outreach.get("email", {})
                                    linkedin_data = first_outreach.get("linkedin", {})
                                    contact.email_copy = f"Subject: {email_data.get('subject', '')}\n\n{email_data.get('body', '')}"
                                    contact.linkedin_copy = linkedin_data.get("message", "")
                                else:
                                    contact.email_copy = copy_output.get("email_copy")
                                    contact.linkedin_copy = copy_output.get("linkedin_copy")
                                print(f"    Generated copy for {contact_name}")
                        except Exception as e:
                            print(f"    Warning: Copy generation failed for {contact_name}: {e}")

                    # Step 3: Client copy override (7.2-copy-client-override) if config exists
                    if client_copy_config and (contact.email_copy or contact.linkedin_copy):
                        # Build state with generated copy
                        override_vars = {
                            **copy_vars,
                            "generated_copy": json.dumps({
                                "email_copy": contact.email_copy,
                                "linkedin_copy": contact.linkedin_copy,
                            }),
                        }
                        override_state = PipelineState(
                            pipeline_run_id=state.pipeline_run_id,
                            client=state.client,
                            seed={**state.seed, **override_vars},
                            step_outputs=state.step_outputs.copy(),
                            claims=state.claims.copy(),
                            merged_claims=state.merged_claims.copy() if state.merged_claims else [],
                            context_packs=state.context_packs.copy(),
                        )

                        try:
                            _, override_output, _ = await self.executor.execute_step(client_copy_config, override_state)
                            if override_output:
                                adjusted = override_output.get("adjusted_outreach", [])
                                if adjusted and len(adjusted) > 0:
                                    first_adjusted = adjusted[0]
                                    email_data = first_adjusted.get("email", {})
                                    linkedin_data = first_adjusted.get("linkedin", {})
                                    contact.client_email_copy = f"Subject: {email_data.get('subject', '')}\n\n{email_data.get('body', '')}"
                                    contact.client_linkedin_copy = linkedin_data.get("message", "")
                                else:
                                    contact.client_email_copy = override_output.get("client_email_copy")
                                    contact.client_linkedin_copy = override_output.get("client_linkedin_copy")
                                print(f"    Generated client copy for {contact_name}")
                        except Exception as e:
                            print(f"    Warning: Client copy override failed for {contact_name}: {e}")

                    # Add to state contacts
                    state.contacts.append(contact)

                    # Save contact to database
                    if self.repo:
                        saved_contact = self.repo.create_contact(contact)
                        if saved_contact:
                            contact.id = saved_contact.id

                except Exception as e:
                    print(f"Warning: Failed to enrich contact {contact_name}: {e}")

        # Run all contact pipelines in parallel (with semaphore limit)
        tasks = [enrich_one(c) for c in contacts_to_enrich[:15]]  # Cap at 15 contacts
        await asyncio.gather(*tasks)

        print(f"Contact enrichment complete. {len(state.contacts)} contacts enriched.")
        if step_config.prompt_id not in state.steps_completed:
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
            # Pack from step 2 (signal discovery) to step 3 (entity research)
            # OR from step 3 to step 4 if step 3 also produces this type
            # Check if this is from step 2 (has "lead" object) or step 3 (has more details)
            lead = output.get("lead", {})
            if lead:
                # This is from step 2 (signal discovery) - extract lead info
                return {
                    "company_name": lead.get("company_name") or output.get("company_name"),
                    "company_domain": lead.get("company_domain") or output.get("domain"),
                    "primary_signal": lead.get("primary_signal") or output.get("primary_signal"),
                    "initial_assessment": lead.get("initial_assessment", {}),
                    "research_questions": lead.get("next_research_questions", []),
                    "sources": output.get("sources", []),
                }
            else:
                # This is from step 3 (entity research) - richer company details
                return {
                    "company_name": output.get("company_name") or state.get_variable("company_name"),
                    "company_domain": output.get("domain") or output.get("company_domain") or state.get_variable("company_domain"),
                    "corporate_structure": output.get("corporate_structure"),
                    "partner_organizations": output.get("partner_organizations", []),
                    "project_details": output.get("project_details"),
                    "primary_signal": output.get("primary_signal") or state.get_variable("primary_signal"),
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

        # Collect writer sections
        writer_sections = getattr(state, 'writer_sections', {})
        sections_completed = get_writer_section_keys() if writer_sections else []

        # Get intro section data for lead score
        intro_section = writer_sections.get("intro", {})

        dossier = self.repo.create_dossier(Dossier(
            pipeline_run_id=state.pipeline_run_id,
            client_id=state.client.id,
            company_name=company_name,
            company_domain=state.get_variable("domain"),
            lead_score=intro_section.get("lead_score") or state.step_outputs.get("9-dossier-plan", {}).get("lead_score"),
            timing_urgency=intro_section.get("timing_urgency") or state.get_variable("timing_urgency"),
            primary_signal=state.get_variable("primary_signal"),
            status="ready",
            sections_completed=sections_completed,
            sections=writer_sections,  # Store all writer outputs
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
