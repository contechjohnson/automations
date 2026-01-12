"""
Pipeline state management
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..db.models import (
    PipelineRun, StepRun, Claim, MergedClaim, ContextPack,
    ClientConfig, Dossier, Contact
)


@dataclass
class PipelineState:
    """
    Holds all state for a pipeline run.
    This is the single source of truth during execution.
    """
    # Core identifiers
    pipeline_run_id: str
    client: ClientConfig

    # Seed input
    seed: Dict[str, Any] = field(default_factory=dict)

    # Accumulated data from steps
    step_outputs: Dict[str, Any] = field(default_factory=dict)  # step -> parsed output
    claims: List[Claim] = field(default_factory=list)
    merged_claims: List[MergedClaim] = field(default_factory=list)
    context_packs: Dict[str, ContextPack] = field(default_factory=dict)  # pack_type -> pack

    # Contacts discovered and enriched
    contacts: List[Contact] = field(default_factory=list)

    # Dossier being built
    dossier: Optional[Dossier] = None

    # Current execution state
    current_step: Optional[str] = None
    steps_completed: List[str] = field(default_factory=list)

    # Timing
    started_at: Optional[datetime] = None

    def get_variable(self, name: str) -> Any:
        """
        Get a variable by name, searching through all sources.
        Order: step_outputs -> context_packs -> client config -> seed
        """
        # Check step outputs (most recent first)
        for step in reversed(self.steps_completed):
            if step in self.step_outputs:
                output = self.step_outputs[step]
                if isinstance(output, dict) and name in output:
                    return output[name]

        # Check context packs
        for pack_type, pack in self.context_packs.items():
            if isinstance(pack.pack_data, dict) and name in pack.pack_data:
                return pack.pack_data[name]

        # Check client config
        if name == "icp_config":
            return self.client.icp_config
        if name == "industry_research":
            return self.client.industry_research
        if name == "research_context":
            return self.client.research_context
        if name == "client_name":
            return self.client.research_context.get("client", {}).get("name", self.client.name)
        if name == "client_services":
            return self.client.research_context.get("differentiators", [])
        if name == "client_differentiators":
            return self.client.research_context.get("differentiators", [])
        if name == "target_titles":
            return self.client.icp_config.get("target_titles", [])

        # Check seed
        if name in self.seed:
            return self.seed[name]

        # Special computed variables
        if name == "current_date":
            return datetime.now().strftime("%Y-%m-%d")
        if name == "all_claims":
            return [c.model_dump() for c in self.claims]
        if name == "resolved_contacts":
            return [c.model_dump() for c in self.contacts]

        # context_pack is a special variable that resolves to the most recent context pack
        if name == "context_pack":
            # Return the most relevant context pack data
            # Priority: signal_to_entity -> entity_to_contacts -> contacts_to_enrichment
            for pack_type in ["signal_to_entity", "entity_to_contacts", "contacts_to_enrichment"]:
                if pack_type in self.context_packs:
                    return self.context_packs[pack_type].pack_data
            return None

        # domain is an alias for company_domain
        if name == "domain":
            return self.get_variable("company_domain")

        return None

    def add_step_output(self, step: str, output: Any):
        """Add output from a completed step"""
        self.step_outputs[step] = output
        if step not in self.steps_completed:
            self.steps_completed.append(step)

    def add_claims(self, new_claims: List[Claim]):
        """Add claims from a step"""
        self.claims.extend(new_claims)

    def add_context_pack(self, pack: ContextPack):
        """Add a context pack"""
        self.context_packs[pack.pack_type] = pack

    def get_context_pack(self, pack_type: str) -> Optional[Dict[str, Any]]:
        """Get context pack data by type"""
        pack = self.context_packs.get(pack_type)
        return pack.pack_data if pack else None

    def build_variables(self, required_vars: List[str]) -> Dict[str, Any]:
        """
        Build a variables dict for prompt interpolation.
        Includes lineage info for tracking.
        """
        variables = {}
        lineage = {}

        for var_name in required_vars:
            value = self.get_variable(var_name)
            if value is not None:
                variables[var_name] = value

                # Track lineage
                if var_name in self.seed:
                    lineage[var_name] = {"source_type": "seed", "source_step": None}
                elif var_name in ["icp_config", "industry_research", "research_context", "client_name", "client_services"]:
                    lineage[var_name] = {"source_type": "client_config", "source_step": None}
                elif var_name == "current_date":
                    lineage[var_name] = {"source_type": "computed", "source_step": None}
                else:
                    # Find which step produced it
                    for step in reversed(self.steps_completed):
                        if step in self.step_outputs:
                            output = self.step_outputs[step]
                            if isinstance(output, dict) and var_name in output:
                                lineage[var_name] = {"source_type": "previous_step", "source_step": step}
                                break
                    else:
                        # Check context packs
                        for pack_type, pack in self.context_packs.items():
                            if isinstance(pack.pack_data, dict) and var_name in pack.pack_data:
                                lineage[var_name] = {"source_type": "context_pack", "source_step": pack_type}
                                break

        return variables, lineage
