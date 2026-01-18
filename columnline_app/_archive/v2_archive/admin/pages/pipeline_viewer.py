"""
Pipeline Viewer - Visual Node-Based Flow Diagram

Make.com-style whiteboard view of the pipeline:
- See all pipeline nodes visually arranged
- Click on nodes to see inputs/outputs
- See data flow between steps (context being passed)
- See nested structures (e.g., contact enrichment sub-pipeline)
- Select a run ID to view actual execution data
"""
import streamlit as st
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import LayeredLayout

from columnline_app.v2.db.repository import V2Repository
from columnline_app.v2.config import PIPELINE_STEPS, Stage

# Status styling - colors for different step states
STATUS_STYLES = {
    "pending": {"backgroundColor": "#E0E0E0", "border": "2px dashed #9E9E9E", "color": "#666"},
    "running": {"backgroundColor": "#2196F3", "border": "3px solid #1565C0", "color": "white"},
    "completed": {"backgroundColor": "#4CAF50", "border": "2px solid #2E7D32", "color": "white"},
    "failed": {"backgroundColor": "#F44336", "border": "2px solid #C62828", "color": "white"},
}

# Node positions - manually laid out for clarity
# Format: step_id -> (x, y) where x is column (stage), y is row within stage
NODE_POSITIONS = {
    # FIND_LEAD (column 0)
    "1-search-builder": (0, 0),
    "2-signal-discovery": (0, 150),
    "3-entity-research": (0, 300),
    "4-contact-discovery": (0, 450),

    # ENRICH_LEAD (column 1)
    "5a-enrich-lead": (250, 0),
    "5b-enrich-opportunity": (250, 150),
    "5c-client-specific": (250, 300),
    "8-media": (250, 450),

    # INSIGHT (column 2)
    "7b-insight": (500, 225),

    # FINAL - Dossier Plan (column 3)
    "9-dossier-plan": (750, 0),

    # FINAL - Writers (column 4)
    "writer-intro": (1000, 0),
    "writer-signals": (1000, 100),
    "writer-lead-intelligence": (1000, 200),
    "writer-strategy": (1000, 300),
    "writer-opportunity": (1000, 400),
    "writer-client-specific": (1000, 500),

    # FINAL - Contact Enrichment (column 4, offset)
    "6-enrich-contacts": (1000, 650),
    "6.2-enrich-contact": (1200, 650),
    "7a-copy": (1350, 650),
    "7.2-copy-client-override": (1500, 650),
}

# Step descriptions for display
STEP_DESCRIPTIONS = {
    "1-search-builder": "Generates search queries",
    "2-signal-discovery": "Finds buying signals via web search",
    "3-entity-research": "Deep research on the company (5-10 min)",
    "4-contact-discovery": "Finds decision makers",
    "5a-enrich-lead": "Network info, investors, board",
    "5b-enrich-opportunity": "Budget, timeline, scope",
    "5c-client-specific": "Custom research questions",
    "8-media": "Logos and images",
    "7b-insight": "MERGE: Combines all claims",
    "9-dossier-plan": "Plans sections, routes claims",
    "writer-intro": "Executive summary",
    "writer-signals": "Buying signals section",
    "writer-lead-intelligence": "Company intelligence",
    "writer-strategy": "Recommended approach",
    "writer-opportunity": "Opportunity analysis",
    "writer-client-specific": "Client-specific section",
    "6-enrich-contacts": "Orchestrates per-contact enrichment",
    "6.2-enrich-contact": "Per-contact: finds email, bio",
    "7a-copy": "Per-contact: email/LinkedIn copy",
    "7.2-copy-client-override": "Per-contact: client tweaks",
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


def get_steps_for_run(run_id: str) -> Dict[str, dict]:
    """Get all steps for a run, keyed by step name"""
    try:
        repo = get_repo()
        result = repo.client.table("v2_step_runs").select("*").eq("pipeline_run_id", run_id).execute()
        steps = result.data if result.data else []
        return {s["step"]: s for s in steps}
    except Exception as e:
        st.error(f"Failed to fetch steps: {e}")
        return {}


def get_claims_for_step(pipeline_run_id: str, step_id: str) -> List[dict]:
    """Fetch claims from database for a step"""
    try:
        repo = get_repo()
        result = repo.client.table("v2_claims").select("*").eq("pipeline_run_id", pipeline_run_id).eq("source_step", step_id).execute()
        return result.data if result.data else []
    except Exception as e:
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


def build_pipeline_nodes(step_runs: Dict[str, dict]) -> List[StreamlitFlowNode]:
    """Build nodes from PIPELINE_STEPS config with status from step_runs"""
    nodes = []

    for step_id, config in PIPELINE_STEPS.items():
        # Get position
        pos = NODE_POSITIONS.get(step_id, (0, 0))

        # Get status from step_runs
        step_run = step_runs.get(step_id, {})
        status = step_run.get("status", "pending")
        style = STATUS_STYLES.get(status, STATUS_STYLES["pending"])

        # Build display label
        short_name = config.name.replace("Writer: ", "").replace(" (Individual)", "").replace(" (Parse)", "")

        # Create node with data
        node = StreamlitFlowNode(
            id=step_id,
            pos=(pos[0], pos[1]),
            data={
                "content": short_name,
                "step_id": step_id,
            },
            node_type="default",
            source_position="right",
            target_position="left",
            style={
                **style,
                "padding": "10px",
                "borderRadius": "8px",
                "fontSize": "12px",
                "width": "140px",
                "textAlign": "center",
            },
            draggable=False,
        )
        nodes.append(node)

    return nodes


def build_pipeline_edges() -> List[StreamlitFlowEdge]:
    """Build edges based on pipeline flow"""
    edges = []

    # FIND_LEAD sequential: 1 -> 2 -> 3 -> 4
    edges.append(StreamlitFlowEdge("e1-2", "1-search-builder", "2-signal-discovery", animated=True, style={"stroke": "#666"}))
    edges.append(StreamlitFlowEdge("e2-3", "2-signal-discovery", "3-entity-research", animated=True, style={"stroke": "#666"}))
    edges.append(StreamlitFlowEdge("e3-4", "3-entity-research", "4-contact-discovery", animated=True, style={"stroke": "#666"}))

    # FIND_LEAD -> ENRICH_LEAD (context pack: signal_to_entity)
    edges.append(StreamlitFlowEdge("e2-5a", "2-signal-discovery", "5a-enrich-lead", animated=True, style={"stroke": "#2196F3"}))
    edges.append(StreamlitFlowEdge("e2-5b", "2-signal-discovery", "5b-enrich-opportunity", animated=True, style={"stroke": "#2196F3"}))
    edges.append(StreamlitFlowEdge("e2-5c", "2-signal-discovery", "5c-client-specific", animated=True, style={"stroke": "#2196F3"}))
    edges.append(StreamlitFlowEdge("e2-8", "2-signal-discovery", "8-media", animated=True, style={"stroke": "#2196F3"}))

    # ENRICH_LEAD -> INSIGHT (all claims merge)
    edges.append(StreamlitFlowEdge("e5a-7b", "5a-enrich-lead", "7b-insight", animated=True, style={"stroke": "#4CAF50"}))
    edges.append(StreamlitFlowEdge("e5b-7b", "5b-enrich-opportunity", "7b-insight", animated=True, style={"stroke": "#4CAF50"}))
    edges.append(StreamlitFlowEdge("e5c-7b", "5c-client-specific", "7b-insight", animated=True, style={"stroke": "#4CAF50"}))
    edges.append(StreamlitFlowEdge("e8-7b", "8-media", "7b-insight", animated=True, style={"stroke": "#4CAF50"}))

    # Also from contact discovery
    edges.append(StreamlitFlowEdge("e4-7b", "4-contact-discovery", "7b-insight", animated=True, style={"stroke": "#4CAF50"}))

    # INSIGHT -> FINAL (dossier plan)
    edges.append(StreamlitFlowEdge("e7b-9", "7b-insight", "9-dossier-plan", animated=True, style={"stroke": "#FF9800"}))

    # Dossier plan -> Writers (parallel)
    for writer in ["writer-intro", "writer-signals", "writer-lead-intelligence", "writer-strategy", "writer-opportunity", "writer-client-specific"]:
        edges.append(StreamlitFlowEdge(f"e9-{writer}", "9-dossier-plan", writer, animated=True, style={"stroke": "#9C27B0"}))

    # INSIGHT -> Contact Enrichment (parallel track)
    edges.append(StreamlitFlowEdge("e7b-6", "7b-insight", "6-enrich-contacts", animated=True, style={"stroke": "#FF9800"}))

    # Contact enrichment chain: 6 -> 6.2 -> 7a -> 7.2
    edges.append(StreamlitFlowEdge("e6-62", "6-enrich-contacts", "6.2-enrich-contact", animated=True, style={"stroke": "#E91E63"}))
    edges.append(StreamlitFlowEdge("e62-7a", "6.2-enrich-contact", "7a-copy", animated=True, style={"stroke": "#E91E63"}))
    edges.append(StreamlitFlowEdge("e7a-72", "7a-copy", "7.2-copy-client-override", animated=True, style={"stroke": "#E91E63"}))

    return edges


def render_step_detail(pipeline_run_id: str, step_id: str, step_runs: Dict[str, dict]):
    """Render detail panel for a selected step"""
    st.markdown("---")
    st.markdown(f"### Step: `{step_id}`")

    # Get step config
    config = PIPELINE_STEPS.get(step_id)
    if config:
        desc = STEP_DESCRIPTIONS.get(step_id, config.name)
        st.markdown(f"*{desc}*")

    # Get step run data
    step_run = step_runs.get(step_id)

    if not step_run:
        st.warning("No execution data for this step yet")
        return

    # Metadata row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status = step_run.get("status", "pending")
        status_emoji = {"completed": "✅", "running": "🔵", "failed": "❌", "pending": "⏳"}.get(status, "❓")
        st.write(f"**Status:** {status_emoji} {status}")
    with col2:
        st.write(f"**Model:** `{step_run.get('model', '-')}`")
    with col3:
        duration_ms = step_run.get("duration_ms")
        if duration_ms:
            st.write(f"**Duration:** {duration_ms/1000:.1f}s")
        else:
            st.write("**Duration:** -")
    with col4:
        tokens_in = step_run.get("tokens_in") or 0
        tokens_out = step_run.get("tokens_out") or 0
        st.write(f"**Tokens:** {tokens_in:,} / {tokens_out:,}")

    # Error if present
    if step_run.get("error_message"):
        st.error(f"**Error:** {step_run['error_message']}")

    # Tabs for input/output/claims
    tab1, tab2, tab3, tab4 = st.tabs(["Input", "Raw Output", "Parsed Output", "Claims"])

    with tab1:
        input_vars = step_run.get("input_variables", {})
        if input_vars:
            st.json(input_vars)
        else:
            st.info("No input variables recorded")

    with tab2:
        raw = step_run.get("raw_output", "")
        if raw:
            st.text_area(
                "Raw LLM Response",
                value=raw[:10000] + ("..." if len(raw) > 10000 else ""),
                height=300,
                key=f"raw_detail_{step_id}",
                label_visibility="collapsed"
            )
        else:
            st.info("No raw output recorded")

    with tab3:
        parsed = step_run.get("parsed_output", {})
        if parsed:
            st.json(parsed)
        else:
            st.info("No parsed output recorded")

    with tab4:
        claims = get_claims_for_step(pipeline_run_id, step_id)
        if claims:
            st.write(f"**{len(claims)} claims from this step:**")

            # Group by type
            by_type = {}
            for c in claims:
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
        else:
            st.info("No claims extracted from this step")


def render_pipeline_viewer():
    """Main pipeline viewer page"""
    st.subheader("Pipeline Flow Viewer")
    st.markdown("*Visual view of the pipeline. Click on any node to see its input/output.*")

    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", key="refresh_viewer"):
            # Clear flow state to force rebuild
            if "flow_key" in st.session_state:
                st.session_state.flow_key += 1
            st.rerun()

    # Initialize flow key for unique rendering
    if "flow_key" not in st.session_state:
        st.session_state.flow_key = 0

    # Get runs
    runs = get_runs()

    if not runs:
        st.info("No pipeline runs yet. Run a pipeline first.")
        st.code("python -m columnline_app.v2.test_pipeline", language="bash")
        return

    # Run selector
    st.markdown("---")
    run_options = []
    for run in runs:
        seed = run.get("seed", {})
        company = seed.get("company_name", "Unknown") if isinstance(seed, dict) else "Unknown"
        status = run.get("status", "unknown")
        status_icon = {"completed": "✅", "running": "🔵", "failed": "❌", "pending": "⏳"}.get(status, "❓")
        started = format_time_ago(run.get("started_at"))
        run_options.append(f"{status_icon} {company} ({run.get('client_name', 'Unknown')}) - {started}")

    selected_idx = st.selectbox(
        "Select Pipeline Run",
        range(len(run_options)),
        format_func=lambda i: run_options[i],
        key="viewer_run_selector"
    )

    if selected_idx is None:
        return

    selected_run = runs[selected_idx]

    # Get step runs for this pipeline
    step_runs = get_steps_for_run(selected_run["id"])

    # Build nodes and edges
    nodes = build_pipeline_nodes(step_runs)
    edges = build_pipeline_edges()

    # Create flow state
    flow_state = StreamlitFlowState(nodes, edges)

    # Stage labels
    st.markdown("---")
    st.markdown("**Stages:** FIND_LEAD → ENRICH_LEAD → INSIGHT → FINAL")

    # Render flow diagram
    result_state = streamlit_flow(
        f"pipeline_flow_{st.session_state.flow_key}",
        flow_state,
        height=750,
        fit_view=True,
        show_controls=True,
        show_minimap=True,
        get_node_on_click=True,
        hide_watermark=True,
        pan_on_drag=True,
        zoom_on_scroll=True,
        style={"backgroundColor": "#1a1a1a"},
    )

    # Show detail panel for selected node
    if result_state and result_state.selected_id:
        render_step_detail(selected_run["id"], result_state.selected_id, step_runs)
    else:
        st.markdown("---")
        st.info("👆 Click on any node above to see its details (input, output, claims)")

    # Legend
    st.markdown("---")
    st.markdown("**Legend:**")
    cols = st.columns(4)
    with cols[0]:
        st.markdown("⏳ **Pending** - Not started yet")
    with cols[1]:
        st.markdown("🔵 **Running** - Currently executing")
    with cols[2]:
        st.markdown("✅ **Completed** - Finished successfully")
    with cols[3]:
        st.markdown("❌ **Failed** - Error occurred")

    # Auto-refresh for running pipelines
    if selected_run.get("status") == "running":
        st.info("Pipeline is running. Page will auto-refresh in 10 seconds...")
        import time
        time.sleep(10)
        st.rerun()
