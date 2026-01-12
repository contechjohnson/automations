"""
Pipeline Page - Start runs, monitor progress, view step timeline
"""
import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository
from columnline_app.v2.db.models import PipelineStatus, StepStatus
from columnline_app.v2.config import PIPELINE_STEPS, STAGE_ORDER


def get_status_color(status: str) -> str:
    colors = {
        "pending": "🔵",
        "running": "🟡",
        "completed": "🟢",
        "failed": "🔴",
        "cancelled": "⚫",
        "skipped": "⚪",
    }
    return colors.get(status, "⚪")


def format_duration(ms: Optional[int]) -> str:
    if not ms:
        return "-"
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    else:
        return f"{ms/60000:.1f}m"


def render_pipeline_page():
    st.title("🚀 Pipeline Dashboard")

    repo = V2Repository()

    # Top row: Start new run
    with st.expander("➕ Start New Pipeline Run", expanded=False):
        col1, col2 = st.columns([1, 2])

        with col1:
            clients = repo.get_clients("active")
            client_options = {c.name: c.id for c in clients}
            selected_client = st.selectbox(
                "Select Client",
                options=list(client_options.keys()),
                key="new_run_client"
            )

        with col2:
            seed_company = st.text_input(
                "Seed (Company Name or Signal)",
                placeholder="e.g., Microsoft Azure data center Virginia",
                key="new_run_seed"
            )

        if st.button("🚀 Start Pipeline", type="primary"):
            if selected_client and seed_company:
                client_id = client_options[selected_client]
                from columnline_app.v2.db.models import PipelineRun

                run = repo.create_pipeline_run(
                    PipelineRun(
                        client_id=client_id,
                        seed={"company_name": seed_company, "hint": seed_company},
                        status=PipelineStatus.PENDING,
                    )
                )
                st.success(f"Pipeline started! Run ID: {run.id}")
                st.rerun()
            else:
                st.error("Please select a client and enter a seed")

    st.markdown("---")

    # Filters
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        clients = repo.get_clients()
        client_filter = st.selectbox(
            "Filter by Client",
            options=["All"] + [c.name for c in clients],
            key="filter_client"
        )
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "running", "completed", "failed", "pending"],
            key="filter_status"
        )
    with col3:
        auto_refresh = st.checkbox("🔄 Auto-refresh (5s)", value=False)

    # Get runs
    client_id_filter = None
    if client_filter != "All":
        for c in clients:
            if c.name == client_filter:
                client_id_filter = c.id
                break

    status_enum = None
    if status_filter != "All":
        status_enum = PipelineStatus(status_filter)

    runs = repo.get_pipeline_runs(client_id_filter, status_enum, limit=20)

    # Pipeline runs list
    st.subheader(f"Recent Runs ({len(runs)})")

    if not runs:
        st.info("No pipeline runs found. Start a new run above!")
        return

    for run in runs:
        client = repo.get_client(run.client_id) if run.client_id else None
        client_name = client.name if client else "Unknown"

        with st.container():
            # Run header
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

            with col1:
                status = run.status.value if hasattr(run.status, 'value') else run.status
                st.markdown(f"**{get_status_color(status)} {client_name}**")
                st.caption(f"Seed: {run.seed.get('company_name', run.seed.get('hint', 'N/A')) if run.seed else 'N/A'}")

            with col2:
                steps_done = len(run.steps_completed) if run.steps_completed else 0
                total = len(PIPELINE_STEPS)
                st.metric("Progress", f"{steps_done}/{total}")

            with col3:
                if run.current_step:
                    st.caption("Current Step")
                    st.write(run.current_step)

            with col4:
                if run.started_at:
                    st.caption("Started")
                    st.write(run.started_at.strftime("%H:%M:%S") if isinstance(run.started_at, datetime) else str(run.started_at)[:19])

            with col5:
                if st.button("View Details", key=f"view_{run.id}"):
                    st.session_state["selected_run_id"] = run.id
                    st.rerun()

            # Step timeline for this run
            steps = repo.get_step_runs(run.id)
            if steps:
                with st.expander("📋 Step Timeline"):
                    render_step_timeline(steps)

            if run.error_message:
                st.error(f"Error: {run.error_message}")

            st.markdown("---")

    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


def render_step_timeline(steps: List[Any]):
    """Render a visual timeline of steps"""
    # Group by stage
    stages = {}
    for step in steps:
        config = PIPELINE_STEPS.get(step.step, {})
        stage = config.stage.value if hasattr(config, 'stage') else "UNKNOWN"
        if stage not in stages:
            stages[stage] = []
        stages[stage].append(step)

    # Render by stage
    for stage_name in [s.value for s in STAGE_ORDER]:
        if stage_name not in stages:
            continue

        st.markdown(f"**{stage_name}**")
        stage_steps = stages[stage_name]

        cols = st.columns(len(stage_steps))
        for i, step in enumerate(stage_steps):
            with cols[i]:
                status = step.status.value if hasattr(step.status, 'value') else step.status
                color = get_status_color(status)

                st.markdown(f"""
                <div class="step-card step-{status}">
                    <strong>{color} {step.step}</strong><br>
                    <small>
                        {format_duration(step.duration_ms)}<br>
                        {step.tokens_in or 0} → {step.tokens_out or 0} tokens
                    </small>
                </div>
                """, unsafe_allow_html=True)


# Selected run detail view
def render_run_detail():
    """Detailed view of a specific run"""
    run_id = st.session_state.get("selected_run_id")
    if not run_id:
        return

    repo = V2Repository()
    run = repo.get_pipeline_run(run_id)

    if not run:
        st.error("Run not found")
        return

    st.subheader(f"Run Detail: {run_id[:8]}...")

    if st.button("← Back to List"):
        del st.session_state["selected_run_id"]
        st.rerun()

    # Run info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", run.status.value if hasattr(run.status, 'value') else run.status)
    with col2:
        steps_done = len(run.steps_completed) if run.steps_completed else 0
        st.metric("Steps Completed", f"{steps_done}/{len(PIPELINE_STEPS)}")
    with col3:
        if run.started_at and run.completed_at:
            duration = (run.completed_at - run.started_at).total_seconds()
            st.metric("Duration", f"{duration:.1f}s")

    # Steps
    steps = repo.get_step_runs(run_id)

    st.subheader("Steps")
    for step in steps:
        with st.expander(f"{get_status_color(step.status)} {step.step} - {format_duration(step.duration_ms)}"):
            tab1, tab2, tab3 = st.tabs(["Input", "Output", "Prompt"])

            with tab1:
                st.json(step.input_variables)

            with tab2:
                if step.parsed_output:
                    st.json(step.parsed_output)
                elif step.raw_output:
                    st.text(step.raw_output[:5000])
                else:
                    st.info("No output yet")

            with tab3:
                if step.interpolated_prompt:
                    st.text_area(
                        "Interpolated Prompt",
                        step.interpolated_prompt,
                        height=300,
                        disabled=True
                    )

            if step.error_message:
                st.error(step.error_message)
