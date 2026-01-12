"""
Prompts Page - Edit prompts, view versions, see last I/O
"""
import streamlit as st
import os
from typing import Dict, Any, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository
from columnline_app.v2.config import PIPELINE_STEPS, STAGE_ORDER, ExecutionMode


def get_execution_mode_badge(mode: str) -> str:
    badges = {
        "sync": "🟢 Sync",
        "agent": "🤖 Agent",
        "background": "🔄 Background",
        "async_poll": "⏳ Async",
    }
    return badges.get(mode, mode)


def render_prompts_page():
    st.title("📝 Prompt Workbench")

    repo = V2Repository()

    # Sidebar: Prompt list grouped by stage
    prompts = repo.get_prompts(is_active=True)

    # Group by stage
    prompts_by_stage: Dict[str, list] = {}
    for p in prompts:
        stage = p.stage
        if stage not in prompts_by_stage:
            prompts_by_stage[stage] = []
        prompts_by_stage[stage].append(p)

    # Sidebar selection
    st.sidebar.subheader("Select Prompt")

    selected_prompt_id = None
    for stage in [s.value for s in STAGE_ORDER]:
        if stage not in prompts_by_stage:
            continue

        st.sidebar.markdown(f"**{stage}**")
        for p in sorted(prompts_by_stage[stage], key=lambda x: x.step_order):
            config = PIPELINE_STEPS.get(p.prompt_id)
            mode = config.execution_mode.value if config else "sync"
            badge = get_execution_mode_badge(mode)

            if st.sidebar.button(
                f"{p.name} {badge}",
                key=f"select_{p.prompt_id}",
                use_container_width=True
            ):
                st.session_state["selected_prompt_id"] = p.prompt_id

    selected_prompt_id = st.session_state.get("selected_prompt_id")

    if not selected_prompt_id:
        st.info("👈 Select a prompt from the sidebar to view/edit")

        # Overview table
        st.subheader("All Prompts")
        data = []
        for p in prompts:
            config = PIPELINE_STEPS.get(p.prompt_id)
            data.append({
                "Step": p.step_order,
                "Name": p.name,
                "Stage": p.stage,
                "Mode": config.execution_mode.value if config else "-",
                "Model": p.model,
                "Claims": "✅" if p.produces_claims else "",
                "Context Pack": "✅" if p.produces_context_pack else "",
            })
        st.dataframe(data, use_container_width=True)
        return

    # Load selected prompt
    prompt = repo.get_prompt_with_content(selected_prompt_id)
    if not prompt:
        st.error("Prompt not found")
        return

    config = PIPELINE_STEPS.get(selected_prompt_id)

    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader(f"{prompt.name}")
        st.caption(f"`{prompt.prompt_id}` | Stage: {prompt.stage}")
    with col2:
        mode = config.execution_mode.value if config else prompt.execution_mode
        st.markdown(f"**{get_execution_mode_badge(mode)}**")
    with col3:
        st.markdown(f"**Model:** `{prompt.model}`")

    # Metadata row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if prompt.produces_claims:
            st.success("✅ Produces Claims")
    with col2:
        if prompt.merges_claims:
            st.warning("🔀 Merges Claims")
    with col3:
        if prompt.produces_context_pack:
            st.info(f"📦 Context Pack: {prompt.context_pack_type}")
    with col4:
        st.caption(f"Version: {prompt.current_version}")

    st.markdown("---")

    # Tabs: Edit, Last Run, Versions, Test
    tab1, tab2, tab3, tab4 = st.tabs(["✏️ Edit", "📊 Last Run", "📜 Versions", "🧪 Test"])

    with tab1:
        render_prompt_editor(prompt, repo)

    with tab2:
        render_last_run(prompt, repo)

    with tab3:
        render_versions(prompt, repo)

    with tab4:
        render_test_runner(prompt, repo)


def render_prompt_editor(prompt, repo):
    """Prompt content editor"""
    st.markdown("### Prompt Content")
    st.caption("Use `{{variable}}` syntax for interpolation")

    # Load content
    content = prompt.content or ""

    # Editor
    new_content = st.text_area(
        "Prompt Template",
        value=content,
        height=500,
        key=f"editor_{prompt.prompt_id}"
    )

    # Variable extraction
    import re
    variables = list(set(re.findall(r'\{\{(\w+)\}\}', new_content)))
    if variables:
        st.caption(f"**Variables detected:** {', '.join(sorted(variables))}")

    # Save
    col1, col2 = st.columns([1, 3])
    with col1:
        change_notes = st.text_input("Change notes", placeholder="What changed?")
    with col2:
        if st.button("💾 Save New Version", type="primary"):
            if new_content != content:
                from columnline_app.v2.db.models import PromptVersion

                new_version = prompt.current_version + 1
                repo.create_prompt_version(PromptVersion(
                    prompt_id=prompt.prompt_id,
                    version_number=new_version,
                    content=new_content,
                    change_notes=change_notes or None,
                    created_by="dashboard",
                ))

                # Update file
                prompt_file = f"prompts/v2/{prompt.prompt_id}.md"
                os.makedirs(os.path.dirname(prompt_file), exist_ok=True)
                with open(prompt_file, "w") as f:
                    f.write(new_content)

                st.success(f"Saved as version {new_version}")
                st.rerun()
            else:
                st.warning("No changes to save")


def render_last_run(prompt, repo):
    """Show last I/O for this prompt"""
    st.markdown("### Last Execution")

    last_runs = repo.get_prompt_last_runs()
    last_run = None
    for run in last_runs:
        if run.get("prompt_id") == prompt.prompt_id:
            last_run = run
            break

    if not last_run:
        st.info("No executions found for this prompt yet")
        return

    # Status
    status = last_run.get("status", "unknown")
    col1, col2, col3 = st.columns(3)
    with col1:
        if status == "completed":
            st.success("✅ Completed")
        elif status == "failed":
            st.error("❌ Failed")
        else:
            st.info(status)
    with col2:
        st.metric("Duration", f"{last_run.get('duration_ms', 0)}ms")
    with col3:
        st.metric("Tokens", f"{last_run.get('tokens_in', 0)} → {last_run.get('tokens_out', 0)}")

    # Input/Output side by side
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Input Variables")
        input_vars = last_run.get("input_variables", {})
        if input_vars:
            st.json(input_vars)
        else:
            st.info("No input variables")

    with col2:
        st.markdown("#### Output")
        output = last_run.get("output")
        if output:
            if isinstance(output, dict):
                st.json(output)
            else:
                st.text(str(output)[:3000])
        else:
            st.info("No output")

    # Interpolated prompt
    with st.expander("View Interpolated Prompt"):
        interp = last_run.get("interpolated_prompt", "")
        st.text_area("What the LLM saw", interp, height=300, disabled=True)

    # Error if any
    if last_run.get("error_message"):
        st.error(f"Error: {last_run['error_message']}")


def render_versions(prompt, repo):
    """Show version history"""
    st.markdown("### Version History")

    versions = repo.get_prompt_versions(prompt.prompt_id)

    if not versions:
        st.info("No version history (prompt loaded from file)")
        return

    for v in versions:
        with st.expander(f"v{v.version_number} - {v.created_at}"):
            if v.change_notes:
                st.caption(v.change_notes)
            st.text_area(
                "Content",
                v.content,
                height=200,
                disabled=True,
                key=f"ver_{v.id}"
            )
            if st.button("Restore this version", key=f"restore_{v.id}"):
                # Save as new version
                from columnline_app.v2.db.models import PromptVersion

                new_version = prompt.current_version + 1
                repo.create_prompt_version(PromptVersion(
                    prompt_id=prompt.prompt_id,
                    version_number=new_version,
                    content=v.content,
                    change_notes=f"Restored from v{v.version_number}",
                    created_by="dashboard",
                ))

                # Update file
                prompt_file = f"prompts/v2/{prompt.prompt_id}.md"
                with open(prompt_file, "w") as f:
                    f.write(v.content)

                st.success(f"Restored as version {new_version}")
                st.rerun()


def render_test_runner(prompt, repo):
    """Test prompt in isolation"""
    st.markdown("### Test Prompt")
    st.caption("Run this prompt with test variables to see output")

    # Variable inputs
    import re
    content = prompt.content or ""
    variables = list(set(re.findall(r'\{\{(\w+)\}\}', content)))

    test_vars = {}
    st.markdown("#### Variables")

    for var in sorted(variables):
        if var == "current_date":
            continue  # Auto-populated
        if var in ["icp_config", "industry_research", "research_context"]:
            st.caption(f"`{var}` - Will use client config")
            continue

        test_vars[var] = st.text_input(
            var,
            placeholder=f"Enter {var}",
            key=f"test_var_{var}"
        )

    # Run button
    if st.button("🧪 Run Test", type="primary"):
        with st.spinner("Running..."):
            try:
                from columnline_app.v2.pipeline.runner import PipelineRunner
                from columnline_app.v2.db.models import PipelineRun, PipelineStatus
                import asyncio

                # Get test client
                clients = repo.get_clients("active")
                if not clients:
                    st.error("No active clients")
                    return
                client = clients[0]

                # Create test run
                pipeline_run = repo.create_pipeline_run(PipelineRun(
                    client_id=client.id,
                    seed=test_vars,
                    status=PipelineStatus.RUNNING,
                    config={"test_mode": True},
                ))

                # Run single step
                runner = PipelineRunner(repo)
                result = asyncio.run(runner.run_single_step(
                    pipeline_run.id,
                    prompt.prompt_id,
                    test_vars
                ))

                st.success("Test completed!")
                st.json(result)

            except Exception as e:
                st.error(f"Test failed: {e}")
                import traceback
                st.code(traceback.format_exc())
