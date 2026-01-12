"""
Prompts Page

View and edit prompts. Uses local files directly.
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from columnline_app.v2.db.repository import V2Repository
from columnline_app.v2.config import PIPELINE_STEPS

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "v2"


def get_prompts():
    """Get prompts from config and files"""
    prompts = []

    # Get from pipeline config
    for step_id, config in PIPELINE_STEPS.items():
        prompts.append({
            "prompt_id": config.prompt_id,
            "name": config.name,
            "stage": config.stage.value if hasattr(config.stage, 'value') else str(config.stage),
            "step_order": config.step_order,
            "model": config.model,
            "produces_claims": config.produces_claims,
        })

    # Sort by step order
    prompts.sort(key=lambda p: (p["step_order"], p["prompt_id"]))

    return prompts


def get_prompt_content(prompt_id: str) -> str:
    """Get prompt content from file"""
    prompt_file = PROMPTS_DIR / f"{prompt_id}.md"
    if prompt_file.exists():
        return prompt_file.read_text()
    return ""


def save_prompt_content(prompt_id: str, content: str) -> bool:
    """Save prompt content to file"""
    prompt_file = PROMPTS_DIR / f"{prompt_id}.md"
    try:
        prompt_file.write_text(content)
        return True
    except Exception as e:
        st.error(f"Failed to save: {e}")
        return False


def get_last_step_run(prompt_id: str) -> dict:
    """Get last step run for this prompt"""
    try:
        repo = V2Repository()
        # Query step runs that match this prompt
        result = repo.supabase.table("v2_step_runs").select("*").like("step", f"%{prompt_id}%").order("started_at", desc=True).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        pass
    return {}


def render_prompts_page():
    """Main prompts page"""
    st.subheader("Prompts")

    # Get prompts
    prompts = get_prompts()

    if not prompts:
        st.info("No prompts found. Check prompts/v2/ directory.")
        return

    # Prompt selector
    prompt_options = {p["prompt_id"]: p for p in prompts}
    selected_id = st.selectbox(
        "Select Prompt",
        list(prompt_options.keys()),
        format_func=lambda x: f"{prompt_options[x].get('stage', 'UNKNOWN')} | {x}",
        key="prompt_selector"
    )

    if selected_id:
        render_prompt_detail(selected_id, prompt_options.get(selected_id, {}))


def render_prompt_detail(prompt_id: str, prompt_meta: dict):
    """Render prompt editor and last run"""
    st.markdown(f"### {prompt_id}")

    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Stage:** {prompt_meta.get('stage', 'UNKNOWN')}")
    with col2:
        st.write(f"**Model:** {prompt_meta.get('model', 'gpt-4.1')}")
    with col3:
        produces_claims = prompt_meta.get('produces_claims', False)
        st.write(f"**Claims:** {'Yes' if produces_claims else 'No'}")

    # Editor
    st.markdown("#### Prompt Content")
    content = get_prompt_content(prompt_id)

    if not content:
        st.warning(f"Prompt file not found: prompts/v2/{prompt_id}.md")
        return

    edited_content = st.text_area(
        "Edit prompt",
        value=content,
        height=400,
        key=f"editor_{prompt_id}",
        label_visibility="collapsed"
    )

    # Save button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Save", type="primary", key=f"save_{prompt_id}"):
            if save_prompt_content(prompt_id, edited_content):
                st.success("Saved!")
            else:
                st.error("Save failed")

    # Last run I/O
    st.markdown("---")
    st.markdown("#### Last Run")

    last_run = get_last_step_run(prompt_id)

    if last_run:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Input Variables**")
            input_vars = last_run.get("input_variables", {})
            if input_vars:
                st.json(input_vars)
            else:
                st.info("No input recorded")

        with col2:
            st.markdown("**Output**")
            output = last_run.get("parsed_output", {})
            if output:
                st.json(output)

                # Show claims if present
                claims = output.get("claims", [])
                if claims:
                    st.markdown(f"**Claims: {len(claims)}**")
                    for claim in claims[:5]:
                        ctype = claim.get("claim_type", "NOTE")
                        stmt = claim.get("statement", "")[:80]
                        st.write(f"- `{ctype}`: {stmt}")
                    if len(claims) > 5:
                        st.write(f"... and {len(claims) - 5} more")
            else:
                raw = last_run.get("raw_output", "")
                if raw:
                    st.text(raw[:500] + ("..." if len(raw) > 500 else ""))
                else:
                    st.info("No output recorded")

        # Run info
        if last_run.get("duration_ms"):
            duration_s = last_run['duration_ms'] / 1000
            tokens = last_run.get('tokens_in', 0) or 0
            st.write(f"Duration: {duration_s:.1f}s | Tokens: {tokens:,}")
    else:
        st.info("No recent runs found for this prompt")
