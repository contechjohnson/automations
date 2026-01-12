"""
Pipeline Runs Page

View and manage pipeline runs. Uses local database directly.
"""
import streamlit as st
import os
import sys
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository
from columnline_app.v2.db.models import PipelineRun, PipelineStatus


def get_repo():
    """Get repository instance"""
    return V2Repository()


def get_runs(limit: int = 20):
    """Fetch recent pipeline runs from local database"""
    try:
        repo = get_repo()
        result = repo.supabase.table("v2_pipeline_runs").select("*").order("started_at", desc=True).limit(limit).execute()
        runs = result.data if result.data else []

        # Enrich with client names
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


def get_run_detail(run_id: str):
    """Fetch full run detail with steps"""
    try:
        repo = get_repo()

        # Get run
        run_result = repo.supabase.table("v2_pipeline_runs").select("*").eq("id", run_id).single().execute()
        run = run_result.data if run_result.data else None

        if not run:
            return None

        # Enrich with client name
        if run.get("client_id"):
            client = repo.get_client(run["client_id"])
            run["client_name"] = client.name if client else "Unknown"

        # Get steps
        steps_result = repo.supabase.table("v2_step_runs").select("*").eq("pipeline_run_id", run_id).order("started_at").execute()
        steps = steps_result.data if steps_result.data else []

        return {"run": run, "steps": steps}
    except Exception as e:
        st.error(f"Failed to fetch run detail: {e}")
    return None


def get_clients():
    """Fetch available clients"""
    try:
        repo = get_repo()
        clients = repo.get_clients()
        return [{"id": c.id, "name": c.name, "slug": c.slug} for c in clients]
    except Exception as e:
        st.error(f"Failed to fetch clients: {e}")
    return []


def format_time_ago(timestamp_str: str) -> str:
    """Format timestamp as 'X ago'"""
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


def status_emoji(status: str) -> str:
    """Status to emoji"""
    return {
        "completed": "✅",
        "running": "🔵",
        "failed": "❌",
        "pending": "⏳"
    }.get(status, "❓")


def render_runs_page():
    """Main runs page"""
    # Header with refresh
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Pipeline Runs")
    with col2:
        if st.button("🔄 Refresh", key="refresh_runs"):
            st.rerun()

    # New run form
    with st.expander("➕ Start New Run", expanded=False):
        clients = get_clients()
        if clients:
            client_options = {c["name"]: c["id"] for c in clients}
            selected_client = st.selectbox("Client", list(client_options.keys()), key="new_run_client")
            company_name = st.text_input("Company Name", placeholder="e.g. Anthropic", key="new_run_company")
            hint = st.text_input("Search Hint (optional)", placeholder="e.g. AI company San Francisco", key="new_run_hint")

            if st.button("🚀 Start Pipeline", type="primary", key="start_pipeline_btn"):
                if company_name:
                    st.info("Pipeline start via dashboard not yet implemented. Use API or test script.")
                else:
                    st.warning("Enter a company name")
        else:
            st.warning("No clients configured")

    # Runs table
    runs = get_runs()

    if not runs:
        st.info("No pipeline runs yet. Run the test script or API to create some.")
        st.code("python3 -m columnline_app.v2.test_pipeline", language="bash")
        return

    # Display as expandable rows
    for i, run in enumerate(runs):
        status = run.get("status", "unknown")
        seed = run.get("seed", {})
        company = seed.get("company_name", "Unknown") if isinstance(seed, dict) else "Unknown"
        client_name = run.get("client_name", "Unknown")
        started = format_time_ago(run.get("started_at"))
        steps_completed = run.get("steps_completed", [])
        steps_count = len(steps_completed) if isinstance(steps_completed, list) else 0

        # Header row
        header = f"{status_emoji(status)} **{company}** | {client_name} | {started} | {steps_count} steps"

        with st.expander(header, expanded=(status == "running")):
            run_detail = get_run_detail(run["id"])

            if run_detail:
                render_run_detail(run_detail, i)
            else:
                st.error("Could not load run details")


def render_run_detail(run_detail: dict, run_index: int):
    """Render detailed view of a run"""
    run = run_detail.get("run", {})
    steps = run_detail.get("steps", [])

    # Run info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", run.get("status", "unknown"))
    with col2:
        st.metric("Current Step", run.get("current_step", "-") or "-")
    with col3:
        steps_completed = run.get("steps_completed", [])
        st.metric("Steps Completed", len(steps_completed) if isinstance(steps_completed, list) else 0)

    # Error message if failed
    if run.get("error_message"):
        st.error(f"**Error:** {run['error_message']}")
        if run.get("error_traceback"):
            with st.expander("Full Traceback"):
                st.code(run["error_traceback"])

    # Steps table
    if steps:
        st.markdown("### Steps")
        for step_idx, step in enumerate(steps):
            step_status = step.get("status", "pending")
            step_name = step.get("step", "unknown")
            duration = step.get("duration_ms")
            duration_str = f"{duration/1000:.1f}s" if duration else "-"

            # Step row
            cols = st.columns([3, 1, 1, 1])
            with cols[0]:
                st.write(f"{status_emoji(step_status)} **{step_name}**")
            with cols[1]:
                st.write(duration_str)
            with cols[2]:
                tokens = step.get("tokens_in", 0) or 0
                st.write(f"{tokens:,}" if tokens else "-")
            with cols[3]:
                if step.get("parsed_output"):
                    # Unique key for each button
                    btn_key = f"view_io_{run_index}_{step_idx}_{step.get('id', step_idx)}"
                    if st.button("View I/O", key=btn_key):
                        st.session_state[f"show_io_{step.get('id', step_idx)}"] = True

            # Show I/O if expanded
            step_id = step.get('id', step_idx)
            if st.session_state.get(f"show_io_{step_id}"):
                render_step_io(step, run.get("id"), run_index, step_idx)
    else:
        st.info("No step data available")


def render_step_io(step: dict, run_id: str, run_index: int, step_index: int):
    """Render step input/output"""
    step_name = step.get('step', 'unknown')
    step_id = step.get('id', step_index)

    st.markdown(f"#### {step_name} I/O")

    # Show model and duration
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.write(f"**Model:** {step.get('model', '-')}")
    with col_meta2:
        duration = step.get("duration_ms")
        st.write(f"**Duration:** {duration/1000:.1f}s" if duration else "**Duration:** -")
    with col_meta3:
        tokens = step.get("tokens_in", 0) or 0
        st.write(f"**Tokens In:** {tokens:,}" if tokens else "**Tokens In:** -")

    # Input/Output columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Input Variables**")
        input_vars = step.get("input_variables", {})
        if input_vars:
            # Special handling for claims merge input
            if "total_claims_to_merge" in input_vars:
                st.write(f"Total claims to merge: **{input_vars.get('total_claims_to_merge', 0)}**")
                claims_by_step = input_vars.get("claims_by_step", {})
                if claims_by_step:
                    st.write("Claims by step:")
                    for s, count in claims_by_step.items():
                        st.write(f"  - {s}: {count}")
                st.write(f"Company: {input_vars.get('company_name', '-')}")
            else:
                st.json(input_vars)
        else:
            st.info("No input variables")

    with col2:
        st.markdown("**Output**")
        output = step.get("parsed_output", {})
        if output:
            # Special handling for claims merge output
            if "merged_claims" in output:
                merged_claims = output.get("merged_claims", [])
                st.write(f"**Merged Claims: {len(merged_claims)}**")
                for mc in merged_claims[:5]:
                    st.write(f"- `{mc.get('claim_type', 'NOTE')}`: {mc.get('statement', '')[:80]}")
                if len(merged_claims) > 5:
                    st.write(f"... and {len(merged_claims) - 5} more")

                # Show merge stats
                stats = output.get("merge_stats", {})
                if stats:
                    st.write("**Merge Stats:**")
                    st.write(f"  - Input: {stats.get('input_claims', 0)}")
                    st.write(f"  - Output: {stats.get('output_claims', 0)}")
                    st.write(f"  - Duplicates merged: {stats.get('duplicates_merged', 0)}")
            else:
                st.json(output)
        else:
            raw = step.get("raw_output", "")
            if raw:
                st.text(raw[:1000] + ("..." if len(raw) > 1000 else ""))
            else:
                st.info("No output")

    # Error if present
    if step.get("error_message"):
        st.error(f"**Error:** {step['error_message']}")

    # Close button
    close_key = f"close_{run_index}_{step_index}_{step_id}"
    if st.button("Close", key=close_key):
        st.session_state[f"show_io_{step_id}"] = False
        st.rerun()
