"""
Registry API
============
Claude's interface for managing the automation catalog.

Query, create, update, and run automations from a single API.
"""

import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from supabase import create_client, Client

router = APIRouter(prefix="/registry", tags=["Registry"])

# Supabase client
def get_supabase() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )


# =============================================================================
# Models
# =============================================================================

class AutomationCreate(BaseModel):
    """Create a new automation."""
    slug: str
    name: str
    description: Optional[str] = None
    type: str  # scraper, enrichment, research, workflow, notification
    category: Optional[str] = None
    template: Optional[str] = None
    geography: Optional[dict] = {}
    icp_types: List[str] = []
    signal_types: List[str] = []
    client_id: Optional[str] = None
    worker_path: Optional[str] = None
    config: dict = {}
    schedule: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None


class AutomationUpdate(BaseModel):
    """Update an automation."""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None
    status: Optional[str] = None
    schedule: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    priority: Optional[int] = None


class AutomationQuery(BaseModel):
    """Query automations."""
    type: Optional[str] = None
    category: Optional[str] = None
    template: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    icp_type: Optional[str] = None
    client_id: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[str] = None
    search: Optional[str] = None  # Full-text search in name/description
    limit: int = 50


class ClientCreate(BaseModel):
    """Create a client."""
    slug: str
    name: str
    icp_type: str
    industry: Optional[str] = None
    target_geography: dict = {}
    target_signals: List[str] = []
    config: dict = {}
    notes: Optional[str] = None


# =============================================================================
# Automation Endpoints
# =============================================================================

@router.get("/automations")
def list_automations(
    type: Optional[str] = None,
    category: Optional[str] = None,
    template: Optional[str] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    icp_type: Optional[str] = None,
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50
):
    """
    Query automations with filters.
    
    Examples:
    - All Virginia scrapers: ?state=VA&type=scraper
    - All data center permits: ?category=permits&tag=data-centers
    - Failed automations: ?status=failed
    - For client: ?client_id=xxx
    """
    supabase = get_supabase()
    
    query = supabase.table("automations").select(
        "slug, name, description, type, category, template, geography, "
        "icp_types, status, last_run_at, last_run_status, tags, priority"
    )
    
    # Apply filters
    if type:
        query = query.eq("type", type)
    if category:
        query = query.eq("category", category)
    if template:
        query = query.eq("template", template)
    if state:
        query = query.eq("geography->state", state)
    if county:
        query = query.eq("geography->county", county)
    if icp_type:
        query = query.contains("icp_types", [icp_type])
    if client_id:
        query = query.eq("client_id", client_id)
    if status:
        query = query.eq("status", status)
    if tag:
        query = query.contains("tags", [tag])
    if search:
        query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
    
    query = query.order("priority", desc=True).limit(limit)
    
    result = query.execute()
    return {"automations": result.data, "count": len(result.data)}


@router.get("/automations/{slug}")
def get_automation(slug: str):
    """Get full details of an automation by slug."""
    supabase = get_supabase()
    
    result = supabase.table("automations").select("*").eq("slug", slug).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Automation not found: {slug}")
    
    automation = result.data[0]
    
    # Get recent runs
    runs = supabase.table("automation_runs").select(
        "started_at, completed_at, status, records_found, error_message"
    ).eq("automation_id", automation["id"]).order(
        "started_at", desc=True
    ).limit(10).execute()
    
    automation["recent_runs"] = runs.data
    
    return automation


@router.post("/automations")
def create_automation(automation: AutomationCreate):
    """
    Create a new automation.
    
    If template is specified, worker_path will be auto-filled from template.
    """
    supabase = get_supabase()
    
    # Check if slug exists
    existing = supabase.table("automations").select("slug").eq("slug", automation.slug).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail=f"Automation already exists: {automation.slug}")
    
    # If template specified, get worker_path
    data = automation.dict()
    if automation.template and not automation.worker_path:
        template = supabase.table("templates").select("worker_path").eq("slug", automation.template).execute()
        if template.data:
            data["worker_path"] = template.data[0]["worker_path"]
    
    # Set defaults
    data["status"] = "draft"
    data["created_at"] = datetime.utcnow().isoformat()
    
    result = supabase.table("automations").insert(data).execute()
    
    return {"created": True, "automation": result.data[0] if result.data else None}


@router.patch("/automations/{slug}")
def update_automation(slug: str, updates: AutomationUpdate):
    """Update an automation."""
    supabase = get_supabase()
    
    data = {k: v for k, v in updates.dict().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = supabase.table("automations").update(data).eq("slug", slug).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Automation not found: {slug}")
    
    return {"updated": True, "automation": result.data[0]}


@router.delete("/automations/{slug}")
def delete_automation(slug: str):
    """Delete an automation (soft delete - sets status to 'deleted')."""
    supabase = get_supabase()
    
    result = supabase.table("automations").update(
        {"status": "deleted"}
    ).eq("slug", slug).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Automation not found: {slug}")
    
    return {"deleted": True, "slug": slug}


# =============================================================================
# Geographic Queries
# =============================================================================

@router.get("/geography/states")
def list_states():
    """List all states with automation counts."""
    supabase = get_supabase()
    
    result = supabase.rpc("get_states_with_counts").execute()
    
    # Fallback if RPC not set up
    if not result.data:
        result = supabase.table("automations").select(
            "geography->state"
        ).not_.is_("geography->state", "null").execute()
        
        states = {}
        for r in result.data:
            state = r.get("state")
            if state:
                states[state] = states.get(state, 0) + 1
        
        return {"states": [{"state": k, "count": v} for k, v in sorted(states.items())]}
    
    return {"states": result.data}


@router.get("/geography/counties/{state}")
def list_counties(state: str):
    """List all counties in a state with automation counts."""
    supabase = get_supabase()
    
    result = supabase.table("automations").select(
        "geography->county, slug, name, status"
    ).eq("geography->state", state).execute()
    
    counties = {}
    for r in result.data:
        county = r.get("county")
        if county:
            if county not in counties:
                counties[county] = {"county": county, "automations": []}
            counties[county]["automations"].append({
                "slug": r["slug"],
                "name": r["name"],
                "status": r["status"]
            })
    
    return {
        "state": state,
        "counties": list(counties.values()),
        "count": len(counties)
    }


# =============================================================================
# Templates
# =============================================================================

@router.get("/templates")
def list_templates():
    """List all available templates."""
    supabase = get_supabase()
    
    result = supabase.table("templates").select(
        "slug, name, description, type, category, config_schema"
    ).execute()
    
    return {"templates": result.data}


@router.get("/templates/{slug}")
def get_template(slug: str):
    """Get template details including config schema."""
    supabase = get_supabase()
    
    result = supabase.table("templates").select("*").eq("slug", slug).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Template not found: {slug}")
    
    # Get automations using this template
    automations = supabase.table("automations").select(
        "slug, name, status, geography->state"
    ).eq("template", slug).limit(20).execute()
    
    template = result.data[0]
    template["automations_using"] = automations.data
    
    return template


# =============================================================================
# Clients
# =============================================================================

@router.get("/clients")
def list_clients():
    """List all clients."""
    supabase = get_supabase()
    
    result = supabase.table("clients").select(
        "id, slug, name, icp_type, industry, status"
    ).execute()
    
    return {"clients": result.data}


@router.get("/clients/{slug}")
def get_client(slug: str):
    """Get client details with their automations."""
    supabase = get_supabase()
    
    result = supabase.table("clients").select("*").eq("slug", slug).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Client not found: {slug}")
    
    client = result.data[0]
    
    # Get client's automations
    automations = supabase.table("automations").select(
        "slug, name, type, category, status, last_run_status"
    ).eq("client_id", client["id"]).execute()
    
    client["automations"] = automations.data
    
    return client


@router.post("/clients")
def create_client(client: ClientCreate):
    """Create a new client."""
    supabase = get_supabase()
    
    existing = supabase.table("clients").select("slug").eq("slug", client.slug).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail=f"Client already exists: {client.slug}")
    
    data = client.dict()
    data["created_at"] = datetime.utcnow().isoformat()
    
    result = supabase.table("clients").insert(data).execute()
    
    return {"created": True, "client": result.data[0] if result.data else None}


# =============================================================================
# Stats & Health
# =============================================================================

@router.get("/stats")
def get_stats():
    """Get overall registry statistics."""
    supabase = get_supabase()
    
    # Count by type
    automations = supabase.table("automations").select("type, status").execute()
    
    by_type = {}
    by_status = {}
    for a in automations.data:
        by_type[a["type"]] = by_type.get(a["type"], 0) + 1
        by_status[a["status"]] = by_status.get(a["status"], 0) + 1
    
    # Count clients
    clients = supabase.table("clients").select("id").execute()
    
    # Count templates
    templates = supabase.table("templates").select("id").execute()
    
    # Recent failures
    failures = supabase.table("automations").select(
        "slug, name, last_run_at"
    ).eq("last_run_status", "failed").order(
        "last_run_at", desc=True
    ).limit(5).execute()
    
    return {
        "total_automations": len(automations.data),
        "by_type": by_type,
        "by_status": by_status,
        "total_clients": len(clients.data),
        "total_templates": len(templates.data),
        "recent_failures": failures.data
    }


@router.get("/health")
def registry_health():
    """Check registry database connection."""
    try:
        supabase = get_supabase()
        result = supabase.table("automations").select("slug").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
