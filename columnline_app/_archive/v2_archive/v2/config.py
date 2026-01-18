"""
Pipeline configuration - step definitions, execution modes, stage ordering

Architecture Notes (aligned with Make.com flow):
- FIND_LEAD: Search, Signal, Entity, Contact Discovery (sequential deep research)
- ENRICH_LEAD: 5a/5b/5c + Media run in parallel
- INSIGHT: Claims merge, context pack for writers
- FINAL: Dossier Plan + 6 Writers (parallel) + Contact Enrichment (parallel)
- Contact enrichment runs 6.2 per contact, writes to v2_contacts table
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ExecutionMode(str, Enum):
    SYNC = "sync"           # Direct call, wait for response
    AGENT = "agent"         # Agent SDK with tools
    BACKGROUND = "background"  # Deep research, returns response_id for polling
    ASYNC_POLL = "async_poll"  # Standard async with polling
    PER_CONTACT = "per_contact"  # Runs once per contact discovered


class Stage(str, Enum):
    FIND_LEAD = "FIND_LEAD"           # 1, 2, 3, 4 - Signal discovery and contact finding
    ENRICH_LEAD = "ENRICH_LEAD"       # 5a, 5b, 5c, 8-media (parallel)
    INSIGHT = "INSIGHT"               # 7b - Claims merge, context pack
    FINAL = "FINAL"                   # 9 + writers + 06 contact enrichment (parallel)


@dataclass
class StepConfig:
    prompt_id: str
    name: str
    stage: Stage
    step_order: int
    execution_mode: ExecutionMode
    model: str
    produces_claims: bool = False
    merges_claims: bool = False
    produces_context_pack: bool = False
    context_pack_type: Optional[str] = None
    parallel_group: Optional[str] = None  # Steps in same group run in parallel
    uses_tools: Optional[List[str]] = None
    timeout_seconds: int = 300
    # Agent config
    agent_type: Optional[str] = None  # "research" | "firecrawl" | "full" | "contact_enrichment"
    # Claims extraction config
    extract_claims_after: bool = False  # If True, run claims extraction prompt after this step
    # Per-contact config
    per_contact: bool = False  # If True, runs once per contact
    # Writer config
    is_writer: bool = False  # If True, this is a dossier section writer
    section_key: Optional[str] = None  # For writers: which section they produce


# Pipeline step definitions
PIPELINE_STEPS: Dict[str, StepConfig] = {
    # =========================================================================
    # STAGE 1: FIND_LEAD - Signal discovery and contact finding
    # =========================================================================
    "1-search-builder": StepConfig(
        prompt_id="1-search-builder",
        name="Search Builder",
        stage=Stage.FIND_LEAD,
        step_order=1,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
    ),
    "2-signal-discovery": StepConfig(
        prompt_id="2-signal-discovery",
        name="Signal Discovery",
        stage=Stage.FIND_LEAD,
        step_order=2,
        execution_mode=ExecutionMode.AGENT,
        model="gpt-4.1",
        produces_claims=True,
        extract_claims_after=True,
        uses_tools=["web_search"],
        timeout_seconds=300,
        produces_context_pack=True,
        context_pack_type="signal_to_entity",
    ),
    "3-entity-research": StepConfig(
        prompt_id="3-entity-research",
        name="Entity Research",
        stage=Stage.FIND_LEAD,
        step_order=3,
        execution_mode=ExecutionMode.BACKGROUND,
        model="o4-mini-deep-research",
        produces_claims=True,
        extract_claims_after=True,
        produces_context_pack=True,
        context_pack_type="signal_to_entity",
        timeout_seconds=900,
    ),
    "4-contact-discovery": StepConfig(
        prompt_id="4-contact-discovery",
        name="Contact Discovery",
        stage=Stage.FIND_LEAD,
        step_order=4,
        execution_mode=ExecutionMode.BACKGROUND,
        model="o4-mini-deep-research",
        produces_claims=True,
        extract_claims_after=True,
        produces_context_pack=True,
        context_pack_type="entity_to_contacts",
        timeout_seconds=900,
    ),

    # =========================================================================
    # STAGE 2: ENRICH_LEAD - Parallel enrichment (5a, 5b, 5c, 8-media)
    # =========================================================================
    "5a-enrich-lead": StepConfig(
        prompt_id="5a-enrich-lead",
        name="Enrich Lead",
        stage=Stage.ENRICH_LEAD,
        step_order=5,
        execution_mode=ExecutionMode.AGENT,
        model="gpt-4.1",
        produces_claims=True,
        extract_claims_after=True,
        parallel_group="enrich",
        uses_tools=["firecrawl_scrape", "firecrawl_search"],
        timeout_seconds=300,
    ),
    "5b-enrich-opportunity": StepConfig(
        prompt_id="5b-enrich-opportunity",
        name="Enrich Opportunity",
        stage=Stage.ENRICH_LEAD,
        step_order=5,
        execution_mode=ExecutionMode.AGENT,
        model="gpt-4.1",
        produces_claims=True,
        extract_claims_after=True,
        parallel_group="enrich",
        uses_tools=["firecrawl_scrape", "firecrawl_search"],
        timeout_seconds=300,
    ),
    "5c-client-specific": StepConfig(
        prompt_id="5c-client-specific",
        name="Client Specific Research",
        stage=Stage.ENRICH_LEAD,
        step_order=5,
        execution_mode=ExecutionMode.AGENT,
        model="gpt-4.1",
        produces_claims=True,
        extract_claims_after=True,
        parallel_group="enrich",
        uses_tools=["firecrawl_scrape", "firecrawl_search"],
        timeout_seconds=300,
    ),
    "8-media": StepConfig(
        prompt_id="8-media",
        name="Media Enrichment",
        stage=Stage.ENRICH_LEAD,  # Now in ENRICH_LEAD parallel group
        step_order=5,
        execution_mode=ExecutionMode.AGENT,
        model="gpt-4.1",
        produces_claims=True,
        extract_claims_after=True,
        parallel_group="enrich",  # Runs in parallel with 5a/5b/5c
        uses_tools=["firecrawl_scrape"],
        timeout_seconds=300,
    ),

    # =========================================================================
    # STAGE 3: INSIGHT - Claims merge and context pack generation
    # =========================================================================
    "7b-insight": StepConfig(
        prompt_id="7b-insight",
        name="Claims Merge & Insight",
        stage=Stage.INSIGHT,
        step_order=7,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        merges_claims=True,
        produces_context_pack=True,
        context_pack_type="contacts_to_enrichment",
    ),

    # =========================================================================
    # STAGE 4: FINAL - Dossier Plan, Writers (parallel), Contact Enrichment (parallel)
    # =========================================================================
    "9-dossier-plan": StepConfig(
        prompt_id="9-dossier-plan",
        name="Dossier Plan",
        stage=Stage.FINAL,
        step_order=9,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
    ),

    # 6 Writers - run in parallel after dossier plan
    "writer-intro": StepConfig(
        prompt_id="writer-intro",
        name="Writer: Intro",
        stage=Stage.FINAL,
        step_order=10,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        parallel_group="writers",
        is_writer=True,
        section_key="intro",
    ),
    "writer-signals": StepConfig(
        prompt_id="writer-signals",
        name="Writer: Signals",
        stage=Stage.FINAL,
        step_order=10,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        parallel_group="writers",
        is_writer=True,
        section_key="signals",
    ),
    "writer-lead-intelligence": StepConfig(
        prompt_id="writer-lead-intelligence",
        name="Writer: Lead Intelligence",
        stage=Stage.FINAL,
        step_order=10,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        parallel_group="writers",
        is_writer=True,
        section_key="lead_intelligence",
    ),
    "writer-strategy": StepConfig(
        prompt_id="writer-strategy",
        name="Writer: Strategy",
        stage=Stage.FINAL,
        step_order=10,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        parallel_group="writers",
        is_writer=True,
        section_key="strategy",
    ),
    "writer-opportunity": StepConfig(
        prompt_id="writer-opportunity",
        name="Writer: Opportunity",
        stage=Stage.FINAL,
        step_order=10,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        parallel_group="writers",
        is_writer=True,
        section_key="opportunity",
    ),
    "writer-client-specific": StepConfig(
        prompt_id="writer-client-specific",
        name="Writer: Client Specific",
        stage=Stage.FINAL,
        step_order=10,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        parallel_group="writers",
        is_writer=True,
        section_key="client_specific",
    ),

    # Contact Enrichment - runs in parallel with writers
    "6-enrich-contacts": StepConfig(
        prompt_id="6-enrich-contacts",
        name="Enrich Contacts (Parse)",
        stage=Stage.FINAL,  # Now in FINAL stage, parallel with writers
        step_order=10,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        parallel_group="final_parallel",  # Different group - runs alongside writers
    ),
    "6.2-enrich-contact": StepConfig(
        prompt_id="6.2-enrich-contact",
        name="Enrich Contact (Individual)",
        stage=Stage.FINAL,
        step_order=10,
        execution_mode=ExecutionMode.AGENT,
        model="gpt-4.1",
        per_contact=True,  # Runs per contact discovered
        agent_type="contact_enrichment",  # Uses AnyMailFinder + LinkedIn + Firecrawl + web search
        uses_tools=["web_search", "firecrawl_scrape", "firecrawl_search", "anymail_finder_lookup", "anymail_finder_linkedin", "linkedin_scraper"],
        timeout_seconds=180,  # 3 min per contact (increased for email verification)
    ),

    # Copy generation - per contact, after enrichment
    "7a-copy": StepConfig(
        prompt_id="7a-copy",
        name="Copy Generation",
        stage=Stage.FINAL,
        step_order=11,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        per_contact=True,
    ),
    "7.2-copy-client-override": StepConfig(
        prompt_id="7.2-copy-client-override",
        name="Copy Client Override",
        stage=Stage.FINAL,
        step_order=11,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1-mini",
        per_contact=True,
    ),
}


# Stage execution order (aligned with Make.com)
STAGE_ORDER = [
    Stage.FIND_LEAD,      # 1, 2, 3, 4 - Sequential deep research
    Stage.ENRICH_LEAD,    # 5a, 5b, 5c, 8-media - Parallel enrichment
    Stage.INSIGHT,        # 7b - Claims merge (sync, blocking)
    Stage.FINAL,          # 9-dossier-plan, writers, 06-contact-enrichment (parallel)
]


def get_steps_for_stage(stage: Stage) -> List[StepConfig]:
    """Get all steps for a given stage, ordered by step_order"""
    return sorted(
        [s for s in PIPELINE_STEPS.values() if s.stage == stage],
        key=lambda x: (x.step_order, x.prompt_id)
    )


def get_parallel_groups_for_stage(stage: Stage) -> Dict[str, List[StepConfig]]:
    """Group steps by their parallel_group within a stage"""
    groups: Dict[str, List[StepConfig]] = {"sequential": []}
    for step in get_steps_for_stage(stage):
        if step.parallel_group:
            if step.parallel_group not in groups:
                groups[step.parallel_group] = []
            groups[step.parallel_group].append(step)
        else:
            groups["sequential"].append(step)
    return groups


def get_writer_steps() -> List[StepConfig]:
    """Get all writer steps"""
    return [s for s in PIPELINE_STEPS.values() if s.is_writer]


def get_writer_section_keys() -> List[str]:
    """Get section keys for all writers"""
    return [s.section_key for s in get_writer_steps() if s.section_key]
