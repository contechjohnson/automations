"""
Execution Logs Page

Simple table of all LLM calls with full I/O inspection.
"""
import streamlit as st
import httpx
import os
from datetime import datetime

API_URL = os.environ.get("API_URL", "https://api.columnline.dev")


def get_logs(limit: int = 50):
    """Fetch recent execution logs"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_URL}/logs", params={"limit": limit})
            if response.status_code == 200:
                return response.json().get("logs", [])
    except Exception as e:
        st.error(f"Failed to fetch logs: {e}")
    return []


def get_log_detail(log_id: str):
    """Fetch full log with I/O"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_URL}/logs/{log_id}")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        st.error(f"Failed to fetch log: {e}")
    return None


def format_time(timestamp_str: str) -> str:
    """Format timestamp for display"""
    if not timestamp_str:
        return "-"
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except:
        return timestamp_str


def status_emoji(status: str) -> str:
    """Status to emoji"""
    return {
        "success": "✅",
        "failed": "❌",
        "running": "🔵"
    }.get(status, "❓")


def render_logs_page():
    """Main logs page"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Execution Logs")
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Get logs
    logs = get_logs()

    if not logs:
        st.info("No execution logs found.")
        return

    # Display as table
    for log in logs:
        status = log.get("status", "unknown")
        worker = log.get("worker_name", "unknown")
        runtime = log.get("runtime_seconds", 0)
        started = format_time(log.get("started_at"))

        # Truncate worker name for display
        worker_short = worker.split(".")[-1] if "." in worker else worker

        header = f"{status_emoji(status)} **{worker_short}** | {started} | {runtime:.1f}s"

        with st.expander(header, expanded=False):
            render_log_detail(log)


def render_log_detail(log: dict):
    """Render log detail with I/O"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**Worker:** {log.get('worker_name', 'unknown')}")
    with col2:
        st.write(f"**Status:** {log.get('status', 'unknown')}")
    with col3:
        st.write(f"**Duration:** {log.get('runtime_seconds', 0):.2f}s")

    # Tags
    tags = log.get("tags", [])
    if tags:
        st.write(f"**Tags:** {', '.join(tags)}")

    # Full I/O (may need separate API call)
    log_id = log.get("id")
    if log_id:
        detail = get_log_detail(log_id)
        if detail:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Input**")
                input_data = detail.get("input", {})
                if input_data:
                    # Show truncated
                    st.json(input_data)
                else:
                    st.info("No input recorded")

            with col2:
                st.markdown("**Output**")
                output_data = detail.get("output", {})
                if output_data:
                    st.json(output_data)
                else:
                    st.info("No output recorded")

            # Error if present
            if detail.get("error_message"):
                st.error(f"**Error:** {detail['error_message']}")
    else:
        st.info("No detail available")
