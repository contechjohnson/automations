"""
Dynamic Automation Runner
=========================
Runs any automation from the registry by loading its config and executing the template.

Instead of 3000 files, you have:
- 1 runner
- Templates for each scraper type
- Configs stored in the registry

Usage:
    run_automation("maricopa-az-permits")
    run_automation("ferc-pjm-interconnection")
"""

import os
import importlib
from datetime import datetime
from typing import Optional
from rq import get_current_job
from supabase import create_client


def get_supabase():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )


def run_automation(
    slug: str,
    override_config: Optional[dict] = None
) -> dict:
    """
    Run an automation by slug.
    
    1. Loads automation config from registry
    2. Finds the template
    3. Executes with config
    4. Logs the run
    
    Args:
        slug: Automation slug (e.g., "maricopa-az-permits")
        override_config: Optional config overrides
    
    Returns:
        Automation result
    """
    job = get_current_job()
    supabase = get_supabase()
    
    def update_progress(message: str, percent: int):
        if job:
            job.meta = {"message": message, "percent": percent, "timestamp": datetime.utcnow().isoformat()}
            job.save_meta()
        print(f"[{percent}%] {message}")
    
    update_progress(f"Loading automation: {slug}", 5)
    
    # Load automation from registry
    result = supabase.table("automations").select("*").eq("slug", slug).execute()
    if not result.data:
        raise ValueError(f"Automation not found: {slug}")
    
    automation = result.data[0]
    
    # Check status
    if automation["status"] not in ["active", "draft"]:
        raise ValueError(f"Automation is {automation['status']}, cannot run")
    
    # Merge config with overrides
    config = automation.get("config", {})
    if override_config:
        config.update(override_config)
    
    update_progress(f"Loading template: {automation['template']}", 10)
    
    # Map template to runner function
    template_runners = {
        "arcgis_permits": "workers.templates.arcgis_permits:run",
        "state_portal": "workers.templates.state_portal:run",
        "public_api": "workers.templates.public_api:run",
        "job_board": "workers.templates.job_board:run",
        "google_maps": "workers.templates.google_maps:run",
        "entity_research": "workers.research.entity_research:run_entity_research",
    }
    
    template = automation.get("template")
    if not template or template not in template_runners:
        raise ValueError(f"Unknown template: {template}")
    
    # Import and run the template
    module_path, func_name = template_runners[template].rsplit(":", 1)
    
    try:
        module = importlib.import_module(module_path)
        runner = getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Cannot load template {template}: {e}")
    
    update_progress(f"Running {automation['name']}...", 20)
    
    # Create run record
    run_id = supabase.table("automation_runs").insert({
        "automation_id": automation["id"],
        "status": "running",
        "rq_job_id": job.id if job else None
    }).execute().data[0]["id"]
    
    start_time = datetime.utcnow()
    
    try:
        # Execute the template with config
        # Pass job for progress updates
        result = runner(
            config=config,
            geography=automation.get("geography", {}),
            job=job
        )
        
        # Update run record
        duration = (datetime.utcnow() - start_time).total_seconds()
        supabase.table("automation_runs").update({
            "status": "success",
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": duration,
            "records_found": result.get("records_found", 0),
            "records_new": result.get("records_new", 0),
            "result": result
        }).eq("id", run_id).execute()
        
        update_progress("Complete!", 100)
        
        return {
            "status": "success",
            "automation": slug,
            "duration_seconds": duration,
            "result": result
        }
        
    except Exception as e:
        # Update run record with error
        duration = (datetime.utcnow() - start_time).total_seconds()
        supabase.table("automation_runs").update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": duration,
            "error_message": str(e),
            "error_traceback": str(e.__traceback__)
        }).eq("id", run_id).execute()
        
        update_progress(f"Failed: {e}", 100)
        
        raise


def run_batch(
    slugs: list[str],
    parallel: bool = False
) -> dict:
    """
    Run multiple automations.
    
    Args:
        slugs: List of automation slugs
        parallel: If True, queue all at once. If False, run sequentially.
    
    Returns:
        Summary of runs
    """
    results = []
    
    for slug in slugs:
        try:
            result = run_automation(slug)
            results.append({"slug": slug, "status": "success", "result": result})
        except Exception as e:
            results.append({"slug": slug, "status": "failed", "error": str(e)})
    
    return {
        "total": len(slugs),
        "success": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "failed"]),
        "results": results
    }


def run_by_filter(
    type: Optional[str] = None,
    category: Optional[str] = None,
    state: Optional[str] = None,
    template: Optional[str] = None,
    client_id: Optional[str] = None,
    limit: int = 10
) -> dict:
    """
    Run all automations matching a filter.
    
    Examples:
        run_by_filter(state="VA")  # All Virginia automations
        run_by_filter(template="arcgis_permits", limit=5)  # First 5 permit scrapers
    """
    supabase = get_supabase()
    
    query = supabase.table("automations").select("slug").eq("status", "active")
    
    if type:
        query = query.eq("type", type)
    if category:
        query = query.eq("category", category)
    if state:
        query = query.eq("geography->state", state)
    if template:
        query = query.eq("template", template)
    if client_id:
        query = query.eq("client_id", client_id)
    
    result = query.limit(limit).execute()
    slugs = [r["slug"] for r in result.data]
    
    return run_batch(slugs)
