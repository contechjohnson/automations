"""
Automation Registration Helper
==============================
Simple functions to register automations in Supabase.

Usage:
    from workers.register import register_automation, check_registration

    # Register a new automation
    register_automation(
        slug="entity-research",
        name="Entity Research",
        type="research",
        category="intelligence",
        worker_path="workers/research/entity.py",
        tags=["research", "gpt-4.1"]
    )

    # Check if registered
    status = check_registration("entity-research")
    print(status)  # {"registered": True, "automation": {...}}
"""

import os
from datetime import datetime
from supabase import create_client


def get_supabase():
    """Get Supabase client."""
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )


def register_automation(
    slug: str,
    name: str,
    type: str,
    category: str = None,
    description: str = None,
    worker_path: str = None,
    prompt_path: str = None,
    template: str = None,
    geography: dict = None,
    config: dict = None,
    tags: list = None,
    status: str = "active",
) -> dict:
    """
    Register an automation in Supabase.

    Args:
        slug: Unique identifier (kebab-case), should match prompt file name
        name: Human-readable name
        type: "scraper" | "research" | "enrichment" | "workflow"
        category: Sub-category (e.g., "permits", "intelligence")
        description: What this automation does
        worker_path: Path to worker file (e.g., "workers/research/entity.py")
        prompt_path: Path to prompt file (e.g., "prompts/entity-research.md")
        template: Template name if using registry runner
        geography: Location context (state, county, etc.)
        config: Runtime configuration
        tags: Searchable tags
        status: "draft" | "active" | "paused"

    Returns:
        Dict with created/updated automation data
    """
    supabase = get_supabase()

    # Check if already exists
    existing = supabase.table("automations").select("slug").eq("slug", slug).execute()

    # Build data dict with fields known to exist in the table
    # Based on database/schema.sql - these columns are guaranteed to exist
    data = {
        "name": name,
        "type": type,
    }

    # Add optional fields if provided - these should exist per schema.sql
    # but we add them conditionally to handle partial schema deployment
    optional_fields = {
        "description": description,
        "category": category,
        "worker_path": worker_path,
        "template": template,
        "geography": geography,
        "config": config,
        "tags": tags,
        "status": status if status != "active" else None,  # Only include if not default
    }

    for field, value in optional_fields.items():
        if value is not None:
            data[field] = value

    if existing.data:
        # Update existing
        result = supabase.table("automations").update(data).eq("slug", slug).execute()
        return {"updated": True, "automation": result.data[0] if result.data else None}

    # Create new
    data["slug"] = slug
    data["created_at"] = datetime.utcnow().isoformat()
    result = supabase.table("automations").insert(data).execute()

    return {"created": True, "automation": result.data[0] if result.data else None}


def check_registration(slug: str) -> dict:
    """
    Check if an automation is registered.

    Args:
        slug: Automation slug to check

    Returns:
        Dict with registered status and automation data if found
    """
    supabase = get_supabase()
    result = supabase.table("automations").select("*").eq("slug", slug).execute()
    return {
        "registered": bool(result.data),
        "automation": result.data[0] if result.data else None
    }


def list_automations(type: str = None, status: str = None, category: str = None) -> list:
    """
    List automations with optional filters.

    Args:
        type: Filter by type (scraper, research, etc.)
        status: Filter by status (active, draft, paused)
        category: Filter by category

    Returns:
        List of automation records
    """
    supabase = get_supabase()
    query = supabase.table("automations").select("*")

    if type:
        query = query.eq("type", type)
    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category)

    result = query.order("created_at", desc=True).execute()
    return result.data or []
