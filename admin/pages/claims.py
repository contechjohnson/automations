"""
Claims Browser - View raw claims, merged claims, resolved objects
"""
import streamlit as st
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository


def render_claims_page():
    st.title("🔍 Claims Browser")

    repo = V2Repository()

    # Get recent runs
    runs = repo.get_pipeline_runs(limit=20)

    if not runs:
        st.info("No pipeline runs found")
        return

    # Run selector
    run_options = {}
    for run in runs:
        client = repo.get_client(run.client_id) if run.client_id else None
        client_name = client.name if client else "Unknown"
        seed_hint = run.seed.get("company_name", run.seed.get("hint", ""))[:30] if run.seed else ""
        status = run.status.value if hasattr(run.status, 'value') else run.status
        label = f"{client_name} - {seed_hint} ({status})"
        run_options[label] = run.id

    selected_run_label = st.selectbox(
        "Select Pipeline Run",
        options=list(run_options.keys()),
        key="claims_run_selector"
    )

    if not selected_run_label:
        return

    run_id = run_options[selected_run_label]

    # Get claims
    raw_claims = repo.get_claims(run_id, is_merged=False)
    merged_claims = repo.get_merged_claims(run_id)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Raw Claims", len(raw_claims))
    with col2:
        st.metric("Merged Claims", len(merged_claims))
    with col3:
        # Count by type
        types = {}
        for c in raw_claims:
            t = c.claim_type.value if hasattr(c.claim_type, 'value') else c.claim_type
            types[t] = types.get(t, 0) + 1
        st.metric("Claim Types", len(types))
    with col4:
        high_conf = len([c for c in raw_claims if c.confidence == "HIGH"])
        st.metric("High Confidence", high_conf)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Raw Claims",
        "🔀 Merged Claims",
        "📊 By Type",
        "🗺️ Section Routing"
    ])

    with tab1:
        render_raw_claims(raw_claims)

    with tab2:
        render_merged_claims(merged_claims)

    with tab3:
        render_claims_by_type(raw_claims)

    with tab4:
        render_section_routing(run_id, repo)


def render_raw_claims(claims):
    """Render raw claims list"""
    st.markdown("### Raw Claims (Before Merge)")

    if not claims:
        st.info("No claims extracted yet")
        return

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        types = list(set(c.claim_type.value if hasattr(c.claim_type, 'value') else c.claim_type for c in claims))
        type_filter = st.multiselect("Filter by Type", options=types, default=types)
    with col2:
        tiers = list(set(c.source_tier.value if hasattr(c.source_tier, 'value') else c.source_tier for c in claims))
        tier_filter = st.multiselect("Filter by Source Tier", options=tiers, default=tiers)
    with col3:
        confs = ["HIGH", "MEDIUM", "LOW"]
        conf_filter = st.multiselect("Filter by Confidence", options=confs, default=confs)

    # Filter claims
    filtered = [
        c for c in claims
        if (c.claim_type.value if hasattr(c.claim_type, 'value') else c.claim_type) in type_filter
        and (c.source_tier.value if hasattr(c.source_tier, 'value') else c.source_tier) in tier_filter
        and (c.confidence.value if hasattr(c.confidence, 'value') else c.confidence) in conf_filter
    ]

    st.caption(f"Showing {len(filtered)} of {len(claims)} claims")

    # Display
    for claim in filtered:
        claim_type = claim.claim_type.value if hasattr(claim.claim_type, 'value') else claim.claim_type
        confidence = claim.confidence.value if hasattr(claim.confidence, 'value') else claim.confidence
        source_tier = claim.source_tier.value if hasattr(claim.source_tier, 'value') else claim.source_tier

        # Color by type
        colors = {
            "SIGNAL": "🟠",
            "CONTACT": "🟣",
            "ENTITY": "🔵",
            "RELATIONSHIP": "🟢",
            "OPPORTUNITY": "🟡",
            "METRIC": "⚪",
            "ATTRIBUTE": "🟤",
            "NOTE": "⚫",
        }
        icon = colors.get(claim_type, "⚪")

        with st.expander(f"{icon} {claim_type}: {claim.statement[:80]}..."):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Statement:** {claim.statement}")
                if claim.entities:
                    st.caption(f"Entities: {', '.join(claim.entities)}")
                if claim.source_url:
                    st.caption(f"Source: [{claim.source_name}]({claim.source_url})")
                else:
                    st.caption(f"Source: {claim.source_name or 'Unknown'}")

            with col2:
                st.caption(f"**Type:** {claim_type}")
                st.caption(f"**Tier:** {source_tier}")
                st.caption(f"**Confidence:** {confidence}")
                st.caption(f"**From Step:** {claim.source_step}")
                st.caption(f"**ID:** {claim.claim_id}")


def render_merged_claims(claims):
    """Render merged claims after insight step"""
    st.markdown("### Merged Claims (After 7B Insight)")

    if not claims:
        st.info("No merged claims yet (run insight step)")
        return

    for claim in claims:
        claim_type = claim.claim_type.value if hasattr(claim.claim_type, 'value') else claim.claim_type

        with st.expander(f"🔀 {claim.merged_claim_id}: {claim.statement[:80]}..."):
            st.markdown(f"**Statement:** {claim.statement}")

            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"**Type:** {claim_type}")
                st.caption(f"**Confidence:** {claim.confidence}")
                st.caption(f"**Original Claims:** {len(claim.original_claim_ids)}")

            with col2:
                st.caption(f"**Reconciliation:** {claim.reconciliation_type or 'PASS_THROUGH'}")
                if claim.entities:
                    st.caption(f"**Entities:** {', '.join(claim.entities)}")

            # Sources
            if claim.sources:
                st.markdown("**Sources:**")
                for source in claim.sources:
                    st.caption(f"- {source.get('name', 'Unknown')} ({source.get('tier', 'OTHER')})")


def render_claims_by_type(claims):
    """Render claims grouped by type"""
    st.markdown("### Claims by Type")

    if not claims:
        st.info("No claims to display")
        return

    # Group by type
    by_type: Dict[str, List] = {}
    for claim in claims:
        t = claim.claim_type.value if hasattr(claim.claim_type, 'value') else claim.claim_type
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(claim)

    # Bar chart
    import pandas as pd
    chart_data = pd.DataFrame({
        "Type": list(by_type.keys()),
        "Count": [len(v) for v in by_type.values()]
    })
    st.bar_chart(chart_data.set_index("Type"))

    # Details per type
    for claim_type, type_claims in sorted(by_type.items()):
        with st.expander(f"{claim_type} ({len(type_claims)})"):
            for c in type_claims:
                st.markdown(f"- {c.statement[:100]}...")


def render_section_routing(run_id: str, repo: V2Repository):
    """Show how claims are routed to dossier sections"""
    st.markdown("### Section Routing (From Dossier Plan)")

    # This would come from v2_claim_assignments table
    # For now, show placeholder

    sections = [
        "INTRO",
        "SIGNALS",
        "CONTACTS",
        "LEAD_INTELLIGENCE",
        "STRATEGY",
        "OPPORTUNITY",
        "CLIENT_SPECIFIC",
    ]

    st.info("Section routing is populated after the dossier_plan step runs")

    for section in sections:
        with st.expander(f"📄 {section}"):
            st.caption("Claims assigned to this section will appear here")
