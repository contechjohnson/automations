"""
Contacts Page - View enriched contacts with copy
"""
import streamlit as st
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository


def render_contacts_page():
    st.title("👥 Contacts")

    repo = V2Repository()

    # Get recent runs with dossiers
    runs = repo.get_pipeline_runs(limit=30)

    # Filter to runs with dossiers
    runs_with_dossiers = []
    for run in runs:
        dossier = repo.get_dossier_by_pipeline(run.id)
        if dossier:
            runs_with_dossiers.append((run, dossier))

    if not runs_with_dossiers:
        st.info("No dossiers found. Run a pipeline to generate contacts.")
        return

    # Selector
    options = {}
    for run, dossier in runs_with_dossiers:
        label = f"{dossier.company_name} - Score: {dossier.lead_score or 'N/A'}"
        options[label] = dossier.id

    selected_label = st.selectbox(
        "Select Dossier",
        options=list(options.keys()),
        key="contacts_dossier"
    )

    if not selected_label:
        return

    dossier_id = options[selected_label]
    dossier = repo.get_dossier(dossier_id)
    contacts = repo.get_contacts(dossier_id)

    # Dossier summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Company", dossier.company_name)
    with col2:
        st.metric("Lead Score", dossier.lead_score or "-")
    with col3:
        st.metric("Contacts", len(contacts))
    with col4:
        verified = len([c for c in contacts if c.is_verified])
        st.metric("Verified", verified)

    st.markdown("---")

    if not contacts:
        st.warning("No contacts found for this dossier")
        return

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Contact List", "📧 Email Copy", "💼 LinkedIn Copy"])

    with tab1:
        render_contact_list(contacts)

    with tab2:
        render_email_copy(contacts)

    with tab3:
        render_linkedin_copy(contacts)


def render_contact_list(contacts):
    """Render contact list view"""
    st.markdown("### Contact List")

    for contact in contacts:
        # Primary badge
        badge = "⭐ Primary" if contact.is_primary else ""
        verified_badge = "✅ Verified" if contact.is_verified else ""

        with st.expander(f"**{contact.first_name} {contact.last_name}** - {contact.title or 'Unknown'} {badge} {verified_badge}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Organization:** {contact.organization or 'Unknown'}")
                if contact.email:
                    st.markdown(f"**Email:** {contact.email}")
                if contact.phone:
                    st.markdown(f"**Phone:** {contact.phone}")
                if contact.linkedin_url:
                    st.markdown(f"**LinkedIn:** [{contact.linkedin_url}]({contact.linkedin_url})")

                if contact.bio:
                    st.markdown("---")
                    st.markdown("**Bio:**")
                    st.write(contact.bio)

                if contact.why_they_matter:
                    st.markdown("**Why They Matter:**")
                    st.write(contact.why_they_matter)

                if contact.relation_to_signal:
                    st.markdown("**Relation to Signal:**")
                    st.write(contact.relation_to_signal)

            with col2:
                st.caption(f"**Confidence:** {contact.confidence or 'Unknown'}")
                st.caption(f"**Source:** {contact.source or 'Unknown'}")
                if contact.tenure:
                    st.caption(f"**Tenure:** {contact.tenure}")


def render_email_copy(contacts):
    """Render email copy for each contact"""
    st.markdown("### Email Copy")
    st.caption("Generated outreach copy for email")

    for contact in contacts:
        name = f"{contact.first_name} {contact.last_name}"

        with st.expander(f"📧 {name} - {contact.title or 'Unknown'}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Standard Email:**")
                if contact.email_copy:
                    st.text_area(
                        "Email Copy",
                        contact.email_copy,
                        height=200,
                        key=f"email_{contact.id}",
                        disabled=True
                    )
                    if st.button("📋 Copy", key=f"copy_email_{contact.id}"):
                        st.code(contact.email_copy)
                else:
                    st.info("No email copy generated")

            with col2:
                st.markdown("**Client Override Email:**")
                if contact.client_email_copy:
                    st.text_area(
                        "Client Email Copy",
                        contact.client_email_copy,
                        height=200,
                        key=f"client_email_{contact.id}",
                        disabled=True
                    )
                    if st.button("📋 Copy", key=f"copy_client_email_{contact.id}"):
                        st.code(contact.client_email_copy)
                else:
                    st.info("No client override email")


def render_linkedin_copy(contacts):
    """Render LinkedIn copy for each contact"""
    st.markdown("### LinkedIn Copy")
    st.caption("Generated outreach copy for LinkedIn")

    for contact in contacts:
        name = f"{contact.first_name} {contact.last_name}"

        with st.expander(f"💼 {name} - {contact.title or 'Unknown'}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Standard LinkedIn:**")
                if contact.linkedin_copy:
                    st.text_area(
                        "LinkedIn Copy",
                        contact.linkedin_copy,
                        height=200,
                        key=f"linkedin_{contact.id}",
                        disabled=True
                    )
                    if st.button("📋 Copy", key=f"copy_linkedin_{contact.id}"):
                        st.code(contact.linkedin_copy)
                else:
                    st.info("No LinkedIn copy generated")

            with col2:
                st.markdown("**Client Override LinkedIn:**")
                if contact.client_linkedin_copy:
                    st.text_area(
                        "Client LinkedIn Copy",
                        contact.client_linkedin_copy,
                        height=200,
                        key=f"client_linkedin_{contact.id}",
                        disabled=True
                    )
                    if st.button("📋 Copy", key=f"copy_client_linkedin_{contact.id}"):
                        st.code(contact.client_linkedin_copy)
                else:
                    st.info("No client override LinkedIn")

            # LinkedIn URL
            if contact.linkedin_url:
                st.markdown(f"[Open LinkedIn Profile]({contact.linkedin_url})")
