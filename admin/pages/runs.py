"""
Pipeline Runs Page

Simple table of runs. Click to expand and see step details.
"""
import streamlit as st
import httpx
import os
from datetime import datetime

API_URL = os.environ.get("API_URL", "https://api.columnline.dev")


def get_runs(limit: int = 20):
    """Fetch recent pipeline runs"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_URL}/v2/pipeline/runs", params={"limit": limit})
            if response.status_code == 200:
                return response.json().get("runs", [])
    except Exception as e:
        st.error(f"Failed to fetch runs: {e}")
    return []


def get_run_detail(run_id: str):
    """Fetch full run detail with steps"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_URL}/v2/pipeline/runs/{run_id}")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        st.error(f"Failed to fetch run: {e}")
    return None


def get_clients():
    """Fetch available clients"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_URL}/v2/clients")
            if response.status_code == 200:
                return response.json().get("clients", [])
    except Exception as e:
        st.error(f"Failed to fetch clients: {e}")
    return []


def start_pipeline(client_id: str, company_name: str, hint: str = ""):
    """Start a new pipeline run"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{API_URL}/v2/pipeline/start",
                json={
                    "client_id": client_id,
                    "seed": {"company_name": company_name, "hint": hint or company_name},
                    "config": {}
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to start pipeline: {response.text}")
    except Exception as e:
        st.error(f"Error starting pipeline: {e}")
    return None


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
    # Header with new run form
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Pipeline Runs")
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    # New run form
    with st.expander("➕ Start New Run", expanded=False):
        clients = get_clients()
        if clients:
            client_options = {c["name"]: c["id"] for c in clients}
            selected_client = st.selectbox("Client", list(client_options.keys()))
            company_name = st.text_input("Company Name", placeholder="e.g. Anthropic")
            hint = st.text_input("Search Hint (optional)", placeholder="e.g. AI company San Francisco")

            if st.button("🚀 Start Pipeline", type="primary"):
                if company_name:
                    result = start_pipeline(client_options[selected_client], company_name, hint)
                    if result:
                        st.success(f"Pipeline started: {result.get('id')}")
                        st.rerun()
                else:
                    st.warning("Enter a company name")
        else:
            st.warning("No clients configured")

    # Runs table
    runs = get_runs()

    if not runs:
        st.info("No pipeline runs yet. Start one above.")
        return

    # Display as expandable rows
    for run in runs:
        status = run.get("status", "unknown")
        company = run.get("seed", {}).get("company_name", "Unknown")
        client_name = run.get("client_name", "Unknown")
        started = format_time_ago(run.get("started_at"))
        steps_completed = len(set(run.get("steps_completed", [])))

        # Header row
        header = f"{status_emoji(status)} **{company}** | {client_name} | {started} | {steps_completed} steps"

        with st.expander(header, expanded=(status == "running")):
            run_detail = get_run_detail(run["id"])

            if run_detail:
                render_run_detail(run_detail)
            else:
                st.error("Could not load run details")


def render_run_detail(run_detail: dict):
    """Render detailed view of a run"""
    run = run_detail.get("run", {})
    steps = run_detail.get("steps", [])

    # Run info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", run.get("status", "unknown"))
    with col2:
        st.metric("Current Step", run.get("current_step", "-"))
    with col3:
        st.metric("Steps Completed", len(set(run.get("steps_completed", []))))

    # Error message if failed
    if run.get("error_message"):
        st.error(f"**Error:** {run['error_message']}")
        if run.get("error_traceback"):
            with st.expander("Full Traceback"):
                st.code(run["error_traceback"])

    # Steps table
    if steps:
        st.markdown("### Steps")
        for step in steps:
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
                    if st.button("View I/O", key=f"io_{step['id']}"):
                        st.session_state[f"show_io_{step['id']}"] = True

            # Show I/O if expanded
            if st.session_state.get(f"show_io_{step['id']}"):
                render_step_io(step)


def render_step_io(step: dict):
    """Render step input/output"""
    step_name = step.get('step', 'unknown')
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
                    st.write(f"  - Conflicts resolved: {stats.get('conflicts_resolved', 0)}")
            else:
                # Check for claims extraction summary
                extraction = output.get("_claims_extraction", {})
                if extraction:
                    st.write(f"**Claims Extracted:** {extraction.get('total_claims', 0)}")
                    by_type = extraction.get("by_type", {})
                    if by_type:
                        non_zero = {k: v for k, v in by_type.items() if v > 0}
                        if non_zero:
                            st.write("By type: " + ", ".join(f"{k}: {v}" for k, v in non_zero.items()))

                # Show raw output JSON
                st.json(output)

                # Show claims if present in output
                claims = output.get("claims", [])
                if claims:
                    st.markdown(f"**Claims in Output: {len(claims)}**")
                    for claim in claims[:10]:
                        st.write(f"- {claim.get('claim_type', 'NOTE')}: {claim.get('statement', '')[:100]}")
                    if len(claims) > 10:
                        st.write(f"... and {len(claims) - 10} more")
        else:
            raw = step.get("raw_output", "")
            if raw:
                st.text(raw[:1000] + ("..." if len(raw) > 1000 else ""))
            else:
                st.info("No output")

    # Error if present
    if step.get("error_message"):
        st.error(f"**Error:** {step['error_message']}")
        if step.get("error_traceback"):
            with st.expander("Full Traceback"):
                st.code(step["error_traceback"])

    # Close button
    if st.button("Close", key=f"close_{step['id']}"):
        st.session_state[f"show_io_{step['id']}"] = False
        st.rerun()
