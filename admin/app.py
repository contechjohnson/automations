"""
Columnline v2 Admin Dashboard

Main entry point for the Streamlit admin dashboard.
Run with: streamlit run admin/app.py
"""
import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Columnline v2 Admin",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .step-card {
        background-color: #1e2130;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }
    .step-running {
        border-left: 4px solid #f0ad4e;
    }
    .step-completed {
        border-left: 4px solid #5cb85c;
    }
    .step-failed {
        border-left: 4px solid #d9534f;
    }
    .step-pending {
        border-left: 4px solid #5bc0de;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e2130 0%, #2d3250 100%);
        border-radius: 12px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.sidebar.title("🏗️ Columnline v2")
    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["🚀 Pipeline", "📝 Prompts", "📊 Step Detail", "🔍 Claims", "👥 Contacts"],
        label_visibility="collapsed"
    )

    if page == "🚀 Pipeline":
        from pages.pipeline import render_pipeline_page
        render_pipeline_page()
    elif page == "📝 Prompts":
        from pages.prompts import render_prompts_page
        render_prompts_page()
    elif page == "📊 Step Detail":
        from pages.step_detail import render_step_detail_page
        render_step_detail_page()
    elif page == "🔍 Claims":
        from pages.claims import render_claims_page
        render_claims_page()
    elif page == "👥 Contacts":
        from pages.contacts import render_contacts_page
        render_contacts_page()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Columnline v2.0 | Production Pipeline")


if __name__ == "__main__":
    main()
