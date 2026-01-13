"""
Pipeline Runs Page - SIMPLE VERSION

Shows every LLM step with full transparency:
- What prompt was used
- What inputs were provided
- What output was returned
- Narrative description of what each step does

No fancy dropdowns. Just clear, readable information.
"""
import streamlit as st
import os
import sys
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository
from columnline_app.v2.config import PIPELINE_STEPS

# Step descriptions - what each step does in plain English
STEP_DESCRIPTIONS = {
    "1-search-builder": "Generates search queries to find signals about the target company. Takes company name + hint, outputs search queries.",
    "2-signal-discovery": "Runs web searches to find buying signals (permits, expansions, funding). Uses agent with web_search tool.",
    "2-signal-discovery_claims_extraction": "Extracts atomic claims from signal discovery narrative. Converts unstructured text to structured claims.",
    "3-entity-research": "Deep research on the company - structure, financials, projects. Uses o4-mini-deep-research (5-10 min).",
    "3-entity-research_claims_extraction": "Extracts atomic claims from entity research. Converts deep research narrative to structured claims.",
    "4-contact-discovery": "Finds decision makers at the company. Uses o4-mini-deep-research.",
    "4-contact-discovery_claims_extraction": "Extracts contact claims from discovery output.",
    "5a-enrich-lead": "Enriches lead with network info, investors, board members. Uses agent with Firecrawl.",
    "5a-enrich-lead_claims_extraction": "Extracts claims from lead enrichment.",
    "5b-enrich-opportunity": "Enriches the opportunity - budget, timeline, scope. Uses agent with Firecrawl.",
    "5b-enrich-opportunity_claims_extraction": "Extracts claims from opportunity enrichment.",
    "5c-client-specific": "Client-specific research questions. Uses agent with Firecrawl.",
    "5c-client-specific_claims_extraction": "Extracts claims from client-specific research.",
    "6-enrich-contacts": "Orchestrates per-contact enrichment. Spawns 6.2 for each contact.",
    "6.2-enrich-contact": "Per-contact enrichment - finds email, bio, LinkedIn. Uses contact_enrichment agent.",
    "7a-copy": "Generates outreach copy for a contact. Email + LinkedIn message.",
    "7.2-copy-client-override": "Client-specific copy tweaks.",
    "7b-insight": "MERGE STEP: Combines all claims, resolves contacts, builds timeline, identifies signals.",
    "8-media": "Fetches logos and images for the dossier.",
    "9-dossier-plan": "Plans dossier sections and routes claims to writers.",
    "writer-executive-summary": "Writes the executive summary section.",
    "writer-company-overview": "Writes company overview section.",
    "writer-opportunity-analysis": "Writes opportunity analysis section.",
    "writer-contact-profiles": "Writes contact profiles section.",
    "writer-competitive-landscape": "Writes competitive landscape section.",
    "writer-recommended-approach": "Writes recommended approach section.",
    "context_pack_signal_to_entity": "Creates focused context summary from signal claims for entity research.",
    "context_pack_entity_to_contacts": "Creates focused context summary from entity claims for contact discovery.",
    "context_pack_for_writers": "Creates focused context summary from merged claims for section writers.",
}


def get_repo():
    return V2Repository()


def get_runs(limit: int = 20):
    """Fetch recent pipeline runs"""
    try:
        repo = get_repo()
        result = repo.client.table("v2_pipeline_runs").select("*").order("started_at", desc=True).limit(limit).execute()
        runs = result.data if result.data else []

        # Add client names
        for run in runs:
            if run.get("client_id"):
                client = repo.get_client(run["client_id"])
                run["client_name"] = client.name if client else "Unknown"
            else:
                run["client_name"] = "Unknown"
        return runs
    except Exception as e:
        st.error(f"Failed to fetch runs: {e}")
        return []


def get_steps_for_run(run_id: str):
    """Get all steps for a run, ordered by time"""
    try:
        repo = get_repo()
        result = repo.client.table("v2_step_runs").select("*").eq("pipeline_run_id", run_id).order("started_at").execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Failed to fetch steps: {e}")
        return []


def format_time_ago(timestamp_str: str) -> str:
    if not timestamp_str:
        return "-"
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        if diff.total_seconds() < 60:
            return "just now"
        elif diff.total_seconds() < 3600:
            return f"{int(diff.total_seconds() / 60)}m ago"
        elif diff.total_seconds() < 86400:
            return f"{int(diff.total_seconds() / 3600)}h ago"
        else:
            return f"{int(diff.total_seconds() / 86400)}d ago"
    except:
        return timestamp_str


def status_icon(status: str) -> str:
    return {"completed": "✅", "running": "🔵", "failed": "❌", "pending": "⏳"}.get(status, "❓")


def render_runs_page():
    """Main runs page - simple and clear"""
    st.subheader("Pipeline Runs")

    # Refresh button
    if st.button("🔄 Refresh", key="refresh_runs_main"):
        st.rerun()

    # Get runs
    runs = get_runs()

    if not runs:
        st.info("No pipeline runs yet.")
        st.code("python3 -m columnline_app.v2.test_pipeline", language="bash")
        return

    # Simple run selector
    st.markdown("---")
    st.markdown("### Select a Run")

    run_options = []
    for run in runs:
        seed = run.get("seed", {})
        company = seed.get("company_name", "Unknown") if isinstance(seed, dict) else "Unknown"
        status = run.get("status", "unknown")
        started = format_time_ago(run.get("started_at"))
        run_options.append(f"{status_icon(status)} {company} ({run.get('client_name', 'Unknown')}) - {started}")

    selected_idx = st.selectbox(
        "Run",
        range(len(run_options)),
        format_func=lambda i: run_options[i],
        key="run_selector"
    )

    if selected_idx is not None:
        selected_run = runs[selected_idx]
        render_run_detail(selected_run)


def render_run_detail(run: dict):
    """Show full run detail with ALL steps visible"""
    st.markdown("---")

    # Run header
    seed = run.get("seed", {})
    company = seed.get("company_name", "Unknown") if isinstance(seed, dict) else "Unknown"
    st.markdown(f"## {company}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write(f"**Status:** {run.get('status', 'unknown')}")
    with col2:
        st.write(f"**Client:** {run.get('client_name', 'Unknown')}")
    with col3:
        st.write(f"**Started:** {format_time_ago(run.get('started_at'))}")
    with col4:
        steps_done = len(run.get("steps_completed", []) or [])
        st.write(f"**Steps:** {steps_done}")

    # Error if failed
    if run.get("error_message"):
        st.error(f"**Error:** {run['error_message']}")

    # Show seed/input
    st.markdown("### Run Input (Seed)")
    st.json(run.get("seed", {}))

    # Get and show ALL steps
    st.markdown("---")
    st.markdown("### All LLM Steps")
    st.markdown("*Every step below is an LLM call. Click to see full prompt, input, and output.*")

    steps = get_steps_for_run(run["id"])

    if not steps:
        st.info("No steps recorded yet.")
        return

    # Show each step - simple and clear
    for i, step in enumerate(steps):
        render_step_card(step, i)


def get_claims_for_step(pipeline_run_id: str, step_id: str):
    """Fetch actual claims from database for a step"""
    try:
        repo = get_repo()
        result = repo.client.table("v2_claims").select("*").eq("pipeline_run_id", pipeline_run_id).eq("source_step", step_id).execute()
        return result.data if result.data else []
    except Exception as e:
        return []


def render_step_card(step: dict, index: int):
    """Render a single step with FULL transparency - shows EVERYTHING"""
    step_name = step.get("step", "unknown")
    step_id = step.get("id", "")
    pipeline_run_id = step.get("pipeline_run_id", "")
    status = step.get("status", "pending")
    duration_ms = step.get("duration_ms")
    duration_str = f"{duration_ms/1000:.1f}s" if duration_ms else "-"
    model = step.get("model", "-")

    # Get description
    description = STEP_DESCRIPTIONS.get(step_name, "No description available.")

    # Step header
    st.markdown(f"#### {index + 1}. {status_icon(status)} `{step_name}`")
    st.markdown(f"*{description}*")

    # Metadata row
    cols = st.columns(4)
    with cols[0]:
        st.write(f"**Model:** `{model}`")
    with cols[1]:
        st.write(f"**Duration:** {duration_str}")
    with cols[2]:
        tokens_in = step.get("tokens_in") or 0
        st.write(f"**Tokens In:** {tokens_in:,}")
    with cols[3]:
        tokens_out = step.get("tokens_out") or 0
        st.write(f"**Tokens Out:** {tokens_out:,}")

    # Error if present
    if step.get("error_message"):
        st.error(f"**Error:** {step['error_message']}")

    # Input section
    st.markdown("**INPUT (what was sent to the LLM):**")
    input_vars = step.get("input_variables", {})
    if input_vars:
        st.json(input_vars)
    else:
        st.info("No input variables recorded")

    # Output section - show EVERYTHING
    st.markdown("**OUTPUT:**")

    parsed = step.get("parsed_output") or {}
    raw = step.get("raw_output", "")

    # 1. Always show raw output first if it exists (the actual LLM response)
    if raw:
        st.markdown("**Raw LLM Response (narrative):**")
        st.text_area(
            "Raw output",
            value=raw[:10000] + ("..." if len(raw) > 10000 else ""),
            height=300,
            key=f"raw_{step_id or index}",
            label_visibility="collapsed"
        )

    # 2. Show parsed/structured output
    if parsed:
        # Handle old format: _claims_extraction contains just summary stats
        if "_claims_extraction" in parsed:
            extraction_stats = parsed.get("_claims_extraction", {})
            st.markdown("**Claims Extraction Stats:**")
            st.json(extraction_stats)

        # Handle new format: _claims_extraction_summary
        elif "_claims_extraction_summary" in parsed:
            summary = parsed.get("_claims_extraction_summary", {})
            st.write(f"**Claims extracted:** {summary.get('claims_count', 0)}")

        # Handle merged claims output
        elif "merged_claims" in parsed:
            merged = parsed.get("merged_claims", [])
            st.write(f"**Merged Claims:** {len(merged)}")
            for mc in merged[:10]:
                ctype = mc.get("claim_type", "NOTE")
                stmt = mc.get("statement", "")[:100]
                st.write(f"- `{ctype}`: {stmt}")
            if len(merged) > 10:
                st.write(f"... and {len(merged) - 10} more")

            # Show resolved contacts
            contacts = parsed.get("resolved_contacts", [])
            if contacts:
                st.markdown("**Resolved Contacts:**")
                for c in contacts[:10]:
                    st.write(f"- **{c.get('full_name', '?')}** - {c.get('title', '?')} at {c.get('organization', '?')}")

            # Show resolved signals
            signals = parsed.get("resolved_signals", [])
            if signals:
                st.markdown("**Resolved Signals:**")
                for s in signals[:10]:
                    st.write(f"- [{s.get('strength', '?')}] **{s.get('signal_type', '?')}**: {s.get('description', '')[:80]}")

            # Show stats
            stats = parsed.get("merge_stats", {})
            if stats:
                st.markdown("**Merge Stats:**")
                st.json(stats)

        # Handle direct claims in output (claims extraction step)
        elif "claims" in parsed:
            claims = parsed.get("claims", [])
            st.markdown(f"**Extracted Claims ({len(claims)}):**")
            for c in claims[:15]:
                ctype = c.get("claim_type", "NOTE")
                stmt = c.get("statement", "")[:100]
                conf = c.get("confidence", "-")
                st.write(f"- `{ctype}` [{conf}]: {stmt}")
            if len(claims) > 15:
                st.write(f"... and {len(claims) - 15} more claims")

        # Generic parsed output
        else:
            st.markdown("**Parsed Output:**")
            st.json(parsed)

    # 3. Fetch and show actual claims from database for this step
    if pipeline_run_id and step_name:
        claims_from_db = get_claims_for_step(pipeline_run_id, step_name)
        if claims_from_db:
            st.markdown(f"**Claims in Database ({len(claims_from_db)} from this step):**")
            # Group by type
            by_type = {}
            for c in claims_from_db:
                ctype = c.get("claim_type", "NOTE")
                if ctype not in by_type:
                    by_type[ctype] = []
                by_type[ctype].append(c)

            for ctype, type_claims in by_type.items():
                st.write(f"**{ctype}** ({len(type_claims)}):")
                for c in type_claims[:5]:
                    stmt = c.get("statement", "")[:100]
                    conf = c.get("confidence", "-")
                    st.write(f"  - [{conf}] {stmt}")
                if len(type_claims) > 5:
                    st.write(f"  ... and {len(type_claims) - 5} more {ctype} claims")

    elif not raw and not parsed:
        st.info("No output recorded")

    # Divider between steps
    st.markdown("---")
