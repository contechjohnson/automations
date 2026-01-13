"""
Execution Logs Page - SIMPLE VERSION

Shows every LLM call with full I/O.
This is the low-level trace - every single API call to OpenAI/etc.
"""
import streamlit as st
import os
import sys
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository


def get_logs(limit: int = 50):
    """Fetch recent execution logs"""
    try:
        repo = V2Repository()
        result = repo.client.table("execution_logs").select("*").order("started_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Failed to fetch logs: {e}")
        return []


def format_time(timestamp_str: str) -> str:
    if not timestamp_str:
        return "-"
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except:
        return timestamp_str


def status_icon(status: str) -> str:
    return {"success": "✅", "failed": "❌", "running": "🔵"}.get(status, "❓")


def render_logs_page():
    """Main logs page - simple list of all LLM calls"""
    st.subheader("Execution Logs")
    st.markdown("*Low-level trace of every LLM API call. Use this to debug specific calls.*")

    if st.button("🔄 Refresh", key="refresh_logs_main"):
        st.rerun()

    # Get logs
    logs = get_logs()

    if not logs:
        st.info("No execution logs found.")
        return

    st.markdown("---")

    # Show each log
    for i, log in enumerate(logs):
        render_log_entry(log, i)


def render_log_entry(log: dict, index: int):
    """Render a single log entry with full I/O"""
    status = log.get("status", "unknown")
    worker = log.get("worker_name", "unknown")
    runtime = log.get("runtime_seconds") or 0
    started = format_time(log.get("started_at"))

    # Simplify worker name
    worker_short = worker.split(".")[-1] if "." in worker else worker

    # Header
    st.markdown(f"#### {index + 1}. {status_icon(status)} `{worker_short}` - {started}")

    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Full Worker:** `{worker}`")
    with col2:
        st.write(f"**Duration:** {runtime:.2f}s")
    with col3:
        tags = log.get("tags", [])
        st.write(f"**Tags:** {', '.join(tags) if tags else '-'}")

    # Input
    st.markdown("**INPUT:**")
    input_data = log.get("input", {})
    if input_data:
        st.json(input_data)
    else:
        st.info("No input recorded")

    # Output
    st.markdown("**OUTPUT:**")
    output_data = log.get("output", {})
    if output_data:
        st.json(output_data)
    else:
        st.info("No output recorded")

    # Error
    if log.get("error_message"):
        st.error(f"**Error:** {log['error_message']}")

    st.markdown("---")
