"""
Pydantic models for v2 pipeline
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ClaimType(str, Enum):
    SIGNAL = "SIGNAL"
    CONTACT = "CONTACT"
    ENTITY = "ENTITY"
    RELATIONSHIP = "RELATIONSHIP"
    OPPORTUNITY = "OPPORTUNITY"
    METRIC = "METRIC"
    ATTRIBUTE = "ATTRIBUTE"
    NOTE = "NOTE"


class SourceTier(str, Enum):
    GOV = "GOV"
    PRIMARY = "PRIMARY"
    NEWS = "NEWS"
    OTHER = "OTHER"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ---------- Client Models ----------

class ClientConfig(BaseModel):
    """Client configuration"""
    id: Optional[str] = None
    slug: str
    name: str
    icp_config: Dict[str, Any] = Field(default_factory=dict)
    industry_research: Dict[str, Any] = Field(default_factory=dict)
    research_context: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------- Prompt Models ----------

class PromptVersion(BaseModel):
    """A single version of a prompt"""
    id: Optional[str] = None
    prompt_id: str
    version_number: int
    content: str
    system_prompt: Optional[str] = None
    change_notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


class PromptConfig(BaseModel):
    """Prompt metadata and configuration"""
    id: Optional[str] = None
    prompt_id: str
    name: str
    stage: str
    step_order: int
    produces_claims: bool = False
    merges_claims: bool = False
    produces_context_pack: bool = False
    context_pack_type: Optional[str] = None
    model: str = "gpt-4.1"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    uses_tools: Optional[List[str]] = None
    execution_mode: str = "sync"
    timeout_seconds: int = 300
    current_version: int = 1
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Loaded at runtime
    content: Optional[str] = None


# ---------- Pipeline Models ----------

class PipelineRun(BaseModel):
    """A single pipeline execution"""
    id: Optional[str] = None
    client_id: Optional[str] = None
    dossier_id: Optional[str] = None
    seed: Optional[Dict[str, Any]] = None
    status: PipelineStatus = PipelineStatus.PENDING
    current_step: Optional[str] = None
    steps_completed: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_step: Optional[str] = None
    error_traceback: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rq_job_id: Optional[str] = None
    created_at: Optional[datetime] = None


class StepRun(BaseModel):
    """A single step execution within a pipeline"""
    id: Optional[str] = None
    pipeline_run_id: str
    step: str
    prompt_id: Optional[str] = None
    prompt_version: Optional[int] = None
    status: StepStatus = StepStatus.PENDING
    input_variables: Dict[str, Any] = Field(default_factory=dict)
    interpolated_prompt: Optional[str] = None
    raw_output: Optional[str] = None
    parsed_output: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    response_id: Optional[str] = None  # For async polling
    created_at: Optional[datetime] = None


# ---------- Claims Models ----------

class Claim(BaseModel):
    """An atomic fact extracted from research"""
    id: Optional[str] = None
    pipeline_run_id: str
    step_run_id: Optional[str] = None
    claim_id: str  # e.g., "entity_001"
    claim_type: ClaimType
    statement: str  # Max 500 chars
    entities: List[str] = Field(default_factory=list)
    date_in_claim: Optional[date] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    source_tier: SourceTier
    confidence: Confidence
    source_step: str
    is_merged: bool = False
    merged_into: Optional[str] = None
    created_at: Optional[datetime] = None


class MergedClaim(BaseModel):
    """Deduplicated claim after insight merge"""
    id: Optional[str] = None
    pipeline_run_id: str
    insight_step_run_id: Optional[str] = None
    merged_claim_id: str  # e.g., "MERGED_001"
    claim_type: ClaimType
    statement: str
    entities: List[str] = Field(default_factory=list)
    date_in_claim: Optional[date] = None
    original_claim_ids: List[str]
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: Confidence
    reconciliation_type: Optional[str] = None
    conflicts_resolved: Optional[Dict[str, Any]] = None
    supersedes: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class ContextPack(BaseModel):
    """Efficiency summary passed between stages"""
    id: Optional[str] = None
    pipeline_run_id: str
    step_run_id: Optional[str] = None
    pack_type: str  # signal_to_entity, entity_to_contacts, contacts_to_enrichment
    pack_data: Dict[str, Any]
    anchor_claim_ids: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


# ---------- Output Models ----------

class Dossier(BaseModel):
    """Generated dossier metadata"""
    id: Optional[str] = None
    pipeline_run_id: Optional[str] = None
    client_id: Optional[str] = None
    company_name: str
    company_domain: Optional[str] = None
    lead_score: Optional[int] = None
    timing_urgency: Optional[str] = None
    primary_signal: Optional[str] = None
    status: str = "skeleton"
    sections_completed: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    released_at: Optional[datetime] = None


class DossierSection(BaseModel):
    """A section of a dossier"""
    id: Optional[str] = None
    dossier_id: str
    pipeline_run_id: Optional[str] = None
    section_key: str
    writer_step_run_id: Optional[str] = None
    content: Dict[str, Any]
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Contact(BaseModel):
    """Enriched contact with outreach copy"""
    id: Optional[str] = None
    dossier_id: str
    pipeline_run_id: Optional[str] = None
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None
    tenure: Optional[str] = None
    why_they_matter: Optional[str] = None
    relation_to_signal: Optional[str] = None
    interesting_facts: Optional[str] = None
    email_copy: Optional[str] = None
    linkedin_copy: Optional[str] = None
    client_email_copy: Optional[str] = None
    client_linkedin_copy: Optional[str] = None
    is_primary: bool = False
    is_verified: bool = False
    confidence: Optional[Confidence] = None
    source: Optional[str] = None  # apollo | linkedin | research | manual
    enrichment_step_run_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------- Request/Response Models ----------

class StartPipelineRequest(BaseModel):
    """Request to start a new pipeline run"""
    client_id: str
    seed: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)


class PipelineRunResponse(BaseModel):
    """Response for pipeline status"""
    id: str
    client_id: Optional[str]
    client_name: Optional[str] = None
    status: PipelineStatus
    current_step: Optional[str]
    steps_completed: List[str]
    total_steps: int
    seed: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float] = None
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    created_at: Optional[datetime]


class StepRunResponse(BaseModel):
    """Response for step details"""
    id: str
    step: str
    prompt_id: Optional[str]
    status: StepStatus
    input_variables: Dict[str, Any]
    interpolated_prompt: Optional[str]
    raw_output: Optional[str]
    parsed_output: Optional[Dict[str, Any]]
    model: Optional[str]
    tokens_in: Optional[int]
    tokens_out: Optional[int]
    duration_ms: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
