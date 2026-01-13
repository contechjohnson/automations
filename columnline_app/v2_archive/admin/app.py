"""
Columnline v2 Admin Dashboard

Simple dashboard: Runs, Prompts, Logs. That's it.
Run with: streamlit run admin/app.py
"""
import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Columnline Admin",
    page_icon="📊",
    layout="wide",
)

def main():
    st.title("Columnline v2 Admin")

    # Tab navigation with Pipeline View first
    tab1, tab2, tab3, tab4 = st.tabs(["Pipeline View", "Pipeline Runs", "Prompts", "Execution Logs"])

    with tab1:
        from pages.pipeline_viewer import render_pipeline_viewer
        render_pipeline_viewer()

    with tab2:
        from pages.runs import render_runs_page
        render_runs_page()

    with tab3:
        from pages.prompts import render_prompts_page
        render_prompts_page()

    with tab4:
        from pages.logs import render_logs_page
        render_logs_page()


if __name__ == "__main__":
    main()
