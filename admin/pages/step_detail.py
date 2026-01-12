"""
Step Detail Page - Deep inspection of step I/O, lineage tracking
"""
import streamlit as st
import json
from typing import Dict, Any, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository
from columnline_app.v2.config import PIPELINE_STEPS


def render_step_detail_page():
    st.title("📊 Step Detail Inspector")

    repo = V2Repository()

    # Get recent runs to select from
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
        label = f"{client_name} - {seed_hint} ({run.status})"
        run_options[label] = run.id

    selected_run_label = st.selectbox(
        "Select Pipeline Run",
        options=list(run_options.keys()),
        key="step_detail_run"
    )

    if not selected_run_label:
        return

    run_id = run_options[selected_run_label]

    # Get steps for this run
    steps = repo.get_step_runs(run_id)

    if not steps:
        st.warning("No steps found for this run")
        return

    # Step selector
    step_options = {s.step: s.id for s in steps}
    selected_step = st.selectbox(
        "Select Step",
        options=list(step_options.keys()),
        key="step_detail_step"
    )

    if not selected_step:
        return

    step_run = repo.get_step_run(step_options[selected_step])

    if not step_run:
        st.error("Step not found")
        return

    # Step config info
    config = PIPELINE_STEPS.get(selected_step)

    st.markdown("---")

    # Header
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status = step_run.status.value if hasattr(step_run.status, 'value') else step_run.status
        if status == "completed":
            st.success(f"✅ {status.upper()}")
        elif status == "failed":
            st.error(f"❌ {status.upper()}")
        elif status == "running":
            st.warning(f"🔄 {status.upper()}")
        else:
            st.info(f"⏳ {status.upper()}")

    with col2:
        st.metric("Duration", f"{step_run.duration_ms or 0}ms")

    with col3:
        st.metric("Tokens In", step_run.tokens_in or 0)

    with col4:
        st.metric("Tokens Out", step_run.tokens_out or 0)

    # Config badges
    if config:
        badges = []
        if config.execution_mode.value == "sync":
            badges.append("🟢 Sync")
        elif config.execution_mode.value == "agent":
            badges.append("🤖 Agent")
        elif config.execution_mode.value == "background":
            badges.append("🔄 Background")
        if config.produces_claims:
            badges.append("📝 Claims")
        if config.produces_context_pack:
            badges.append("📦 Context Pack")

        st.markdown(" | ".join(badges))

    st.markdown("---")

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Input Variables",
        "📝 Interpolated Prompt",
        "📤 Raw Output",
        "🔍 Parsed Output",
        "🔗 Lineage"
    ])

    with tab1:
        st.markdown("### Input Variables")
        st.caption("Variables passed to this step for prompt interpolation")

        input_vars = step_run.input_variables or {}
        if input_vars:
            # Show each variable with its value
            for key, value in input_vars.items():
                with st.expander(f"**{key}**", expanded=len(input_vars) < 5):
                    if isinstance(value, (dict, list)):
                        st.json(value)
                    else:
                        st.text(str(value)[:2000])
        else:
            st.info("No input variables")

    with tab2:
        st.markdown("### Interpolated Prompt")
        st.caption("The actual prompt sent to the LLM (after variable substitution)")

        if step_run.interpolated_prompt:
            # Show character and word count
            char_count = len(step_run.interpolated_prompt)
            word_count = len(step_run.interpolated_prompt.split())
            st.caption(f"{word_count:,} words | {char_count:,} characters")

            st.text_area(
                "Prompt",
                step_run.interpolated_prompt,
                height=500,
                disabled=True,
                key="interp_prompt_view"
            )

            # Copy button
            if st.button("📋 Copy to Clipboard"):
                st.code(step_run.interpolated_prompt)
        else:
            st.info("No interpolated prompt recorded")

    with tab3:
        st.markdown("### Raw Output")
        st.caption("Raw response from the LLM")

        if step_run.raw_output:
            char_count = len(step_run.raw_output)
            st.caption(f"{char_count:,} characters")

            st.text_area(
                "Raw Output",
                step_run.raw_output,
                height=500,
                disabled=True,
                key="raw_output_view"
            )
        else:
            st.info("No raw output recorded")

    with tab4:
        st.markdown("### Parsed Output")
        st.caption("Structured JSON extracted from the output")

        if step_run.parsed_output:
            st.json(step_run.parsed_output)

            # Show claims if this step produces them
            if config and config.produces_claims:
                claims = step_run.parsed_output.get("claims", [])
                if claims:
                    st.markdown("#### Extracted Claims")
                    for i, claim in enumerate(claims):
                        with st.expander(f"Claim {i+1}: {claim.get('claim_type', 'NOTE')}"):
                            st.write(claim.get("statement", ""))
                            st.caption(f"Source: {claim.get('source_name', 'Unknown')} ({claim.get('source_tier', 'OTHER')})")
                            st.caption(f"Confidence: {claim.get('confidence', 'MEDIUM')}")
        else:
            st.info("No parsed output (may not be JSON)")

    with tab5:
        st.markdown("### Variable Lineage")
        st.caption("Where each input variable came from")

        # Build lineage info
        input_vars = step_run.input_variables or {}

        if not input_vars:
            st.info("No variables to trace")
        else:
            lineage_data = []
            for var_name in input_vars.keys():
                # Determine source
                if var_name in ["icp_config", "industry_research", "research_context"]:
                    source_type = "client_config"
                    source_step = None
                elif var_name == "current_date":
                    source_type = "computed"
                    source_step = None
                elif var_name in ["company_name", "hint", "domain"]:
                    source_type = "seed"
                    source_step = None
                else:
                    # Assume from previous step
                    source_type = "previous_step"
                    source_step = "inferred"

                lineage_data.append({
                    "Variable": var_name,
                    "Source Type": source_type,
                    "Source Step": source_step or "-",
                })

            st.dataframe(lineage_data, use_container_width=True)

    # Error section
    if step_run.error_message:
        st.markdown("---")
        st.error("### Error")
        st.code(step_run.error_message)

        if step_run.error_traceback:
            with st.expander("View Full Traceback"):
                st.code(step_run.error_traceback)

    # Re-run button
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Re-run This Step"):
            st.warning("Re-run functionality coming soon")

    with col2:
        if st.button("📋 Copy as Test Fixture"):
            fixture = {
                "step": selected_step,
                "input_variables": step_run.input_variables,
                "expected_output": step_run.parsed_output,
            }
            st.code(json.dumps(fixture, indent=2))
