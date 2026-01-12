"""
Prompts Page

Simple table of prompts. Click to edit and see last run I/O.
"""
import streamlit as st
import httpx
import os
from pathlib import Path

API_URL = os.environ.get("API_URL", "https://api.columnline.dev")
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "v2"


def get_prompts():
    """Fetch prompts from API or files"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_URL}/v2/prompts")
            if response.status_code == 200:
                return response.json().get("prompts", [])
    except Exception as e:
        st.warning(f"API unavailable, loading from files: {e}")

    # Fallback: load from files
    prompts = []
    if PROMPTS_DIR.exists():
        for f in PROMPTS_DIR.glob("*.md"):
            prompts.append({
                "prompt_id": f.stem,
                "name": f.stem.replace("-", " ").title(),
                "stage": "UNKNOWN",
                "step_order": 0
            })
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
        with httpx.Client(timeout=30.0) as client:
            # Get recent runs and find step with this prompt
            response = client.get(f"{API_URL}/v2/pipeline/runs", params={"limit": 10})
            if response.status_code == 200:
                runs = response.json().get("runs", [])
                for run in runs:
                    # Get run detail to find step
                    detail = client.get(f"{API_URL}/v2/pipeline/runs/{run['id']}")
                    if detail.status_code == 200:
                        data = detail.json()
                        for step in data.get("steps", []):
                            # Match step name to prompt_id (step names like "3-entity-research")
                            step_name = step.get("step", "")
                            if prompt_id in step_name or step_name.endswith(prompt_id):
                                return step
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
        format_func=lambda x: f"{prompt_options[x].get('stage', 'UNKNOWN')} | {x}"
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
        if st.button("💾 Save", type="primary"):
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
            st.write(f"Duration: {last_run['duration_ms']/1000:.1f}s | Tokens: {last_run.get('tokens_in', 0):,}")
    else:
        st.info("No recent runs found for this prompt")

    # Test button
    st.markdown("---")
    with st.expander("🧪 Test This Prompt"):
        st.info("Test functionality: Uses last run input to re-run this step")
        if st.button("Run with Last Input"):
            st.warning("Test execution not yet implemented")
