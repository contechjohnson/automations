"""
Pipeline configuration - step definitions, execution modes, stage ordering

Architecture Notes:
- Claims extraction is an LLM step (same prompt for all extractors)
- Claims merge is an LLM step at 7b-insight
- Context packs are LLM-orchestrated outputs
- Copy generation runs PER CONTACT
- Writer steps run in parallel
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
    FIND_LEAD = "FIND_LEAD"
    ENRICH_LEAD = "ENRICH_LEAD"
    ENRICH_CONTACTS = "ENRICH_CONTACTS"
    COPY = "COPY"
    INSIGHT = "INSIGHT"
    MEDIA = "MEDIA"
    DOSSIER_PLAN = "DOSSIER_PLAN"


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
    # Claims extraction config
    extract_claims_after: bool = False  # If True, run claims extraction prompt after this step
    # Per-contact config
    per_contact: bool = False  # If True, runs once per contact


# Pipeline step definitions
# Note: extract_claims_after=True means we run claims-extraction.md after this step
PIPELINE_STEPS: Dict[str, StepConfig] = {
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
        extract_claims_after=True,  # LLM extracts claims from narrative
        uses_tools=["web_search"],
        timeout_seconds=300,  # 5 min for agent web search
        produces_context_pack=True,  # Creates lead context for step 3
        context_pack_type="signal_to_entity",  # Pack for step 3 (entity research)
    ),
    "3-entity-research": StepConfig(
        prompt_id="3-entity-research",
        name="Entity Research",
        stage=Stage.FIND_LEAD,
        step_order=3,
        execution_mode=ExecutionMode.BACKGROUND,
        model="o4-mini-deep-research",
        produces_claims=True,
        extract_claims_after=True,  # LLM extracts claims from narrative
        produces_context_pack=True,
        context_pack_type="signal_to_entity",
        timeout_seconds=600,
    ),
    "4-contact-discovery": StepConfig(
        prompt_id="4-contact-discovery",
        name="Contact Discovery",
        stage=Stage.FIND_LEAD,
        step_order=4,
        execution_mode=ExecutionMode.BACKGROUND,
        model="o4-mini-deep-research",
        produces_claims=True,
        extract_claims_after=True,  # LLM extracts claims from narrative
        produces_context_pack=True,
        context_pack_type="entity_to_contacts",
        timeout_seconds=600,
    ),
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
        timeout_seconds=300,  # 5 min for firecrawl agent
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
        timeout_seconds=300,  # 5 min for firecrawl agent
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
        timeout_seconds=300,  # 5 min for firecrawl agent
    ),
    "6-enrich-contacts": StepConfig(
        prompt_id="6-enrich-contacts",
        name="Enrich Contacts (Extract)",
        stage=Stage.ENRICH_CONTACTS,
        step_order=6,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
    ),
    "6.2-enrich-contact": StepConfig(
        prompt_id="6.2-enrich-contact",
        name="Enrich Contact (Individual)",
        stage=Stage.ENRICH_CONTACTS,
        step_order=6,
        execution_mode=ExecutionMode.AGENT,
        model="gpt-4.1",
        per_contact=True,  # Runs per contact discovered
        uses_tools=["web_search", "firecrawl_scrape"],
    ),
    "7a-copy": StepConfig(
        prompt_id="7a-copy",
        name="Copy Generation",
        stage=Stage.COPY,
        step_order=7,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        per_contact=True,  # Runs per contact for personalized copy
    ),
    "7.2-copy-client-override": StepConfig(
        prompt_id="7.2-copy-client-override",
        name="Copy Client Override",
        stage=Stage.COPY,
        step_order=7,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1-mini",
        per_contact=True,  # Runs per contact
    ),
    # Claims merge step - processes ALL accumulated claims
    "7b-insight": StepConfig(
        prompt_id="7b-insight",
        name="Claims Merge & Insight",
        stage=Stage.INSIGHT,
        step_order=7,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
        merges_claims=True,  # This is the merge point
        produces_context_pack=True,
        context_pack_type="contacts_to_enrichment",
    ),
    "8-media": StepConfig(
        prompt_id="8-media",
        name="Media Enrichment",
        stage=Stage.MEDIA,
        step_order=8,
        execution_mode=ExecutionMode.AGENT,
        model="gpt-4.1",
        produces_claims=True,
        extract_claims_after=True,
        uses_tools=["firecrawl_scrape"],
    ),
    "9-dossier-plan": StepConfig(
        prompt_id="9-dossier-plan",
        name="Dossier Plan",
        stage=Stage.DOSSIER_PLAN,
        step_order=9,
        execution_mode=ExecutionMode.SYNC,
        model="gpt-4.1",
    ),
}


# Stage execution order
STAGE_ORDER = [
    Stage.FIND_LEAD,
    Stage.ENRICH_LEAD,
    Stage.ENRICH_CONTACTS,
    Stage.COPY,
    Stage.INSIGHT,
    Stage.MEDIA,
    Stage.DOSSIER_PLAN,
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
