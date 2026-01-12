"""
Execution Logs Page

Simple table of all LLM calls with full I/O inspection.
"""
import streamlit as st
import os
import sys
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository


def get_logs(limit: int = 50):
    """Fetch recent execution logs from local database"""
    try:
        repo = V2Repository()
        # Get from execution_logs table
        result = repo.supabase.table("execution_logs").select("*").order("started_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Failed to fetch logs: {e}")
    return []


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
        if st.button("🔄 Refresh", key="refresh_logs"):
            st.rerun()

    # Get logs
    logs = get_logs()

    if not logs:
        st.info("No execution logs found.")
        return

    # Display as table
    for i, log in enumerate(logs):
        status = log.get("status", "unknown")
        worker = log.get("worker_name", "unknown")
        runtime = log.get("runtime_seconds") or 0
        started = format_time(log.get("started_at"))

        # Truncate worker name for display
        worker_short = worker.split(".")[-1] if "." in worker else worker

        header = f"{status_emoji(status)} **{worker_short}** | {started} | {runtime:.1f}s"

        with st.expander(header, expanded=False):
            render_log_detail(log, i)


def render_log_detail(log: dict, index: int):
    """Render log detail with I/O"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**Worker:** {log.get('worker_name', 'unknown')}")
    with col2:
        st.write(f"**Status:** {log.get('status', 'unknown')}")
    with col3:
        runtime = log.get('runtime_seconds') or 0
        st.write(f"**Duration:** {runtime:.2f}s")

    # Tags
    tags = log.get("tags", [])
    if tags:
        st.write(f"**Tags:** {', '.join(tags)}")

    # Full I/O from the log record
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Input**")
        input_data = log.get("input", {})
        if input_data:
            st.json(input_data)
        else:
            st.info("No input recorded")

    with col2:
        st.markdown("**Output**")
        output_data = log.get("output", {})
        if output_data:
            st.json(output_data)
        else:
            st.info("No output recorded")

    # Error if present
    if log.get("error_message"):
        st.error(f"**Error:** {log['error_message']}")
