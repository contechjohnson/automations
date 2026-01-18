"""
Prompts Page - SIMPLE VERSION

Shows each prompt with:
- The actual prompt template (from file)
- What variables it expects
- Last run's input and output
- Description of what it does

Full transparency - you can see exactly what's being sent to the LLM.
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

# Prompt descriptions - what each prompt does and what it outputs
PROMPT_DESCRIPTIONS = {
    "1-search-builder": "Generates optimized search queries based on company name and hint. Output: JSON with search_queries array.",
    "2-signal-discovery": "Agent prompt for finding buying signals via web search. Output: Narrative about signals found.",
    "3-entity-research": "Deep research prompt for company analysis. Uses o4-mini-deep-research. Output: Detailed narrative.",
    "4-contact-discovery": "Deep research prompt for finding decision makers. Output: Narrative with contact details.",
    "5a-enrich-lead": "Agent prompt for enriching lead with network info. Output: Narrative with enrichment data.",
    "5b-enrich-opportunity": "Agent prompt for enriching the opportunity. Output: Narrative with budget/timeline.",
    "5c-client-specific": "Agent prompt for client-specific research questions. Output: Narrative with answers.",
    "6-enrich-contacts": "Orchestrator for per-contact enrichment. Spawns individual contact enrichment.",
    "6.2-enrich-contact": "Per-contact enrichment prompt. Uses contact_enrichment agent. Output: Structured contact data.",
    "7a-copy": "Generates email and LinkedIn outreach copy for a contact. Output: JSON with copy text.",
    "7.2-copy-client-override": "Client-specific copy customization. Tweaks copy to match client voice.",
    "7b-insight": "Claims merge prompt - the big reconciliation step. Output: JSON with merged_claims, resolved_contacts, etc.",
    "claims-extraction": "Extracts atomic claims from narrative text. THE key step that converts narrative → structured claims.",
    "claims-merge": "Merges all claims from all steps. Resolves contacts, timelines, conflicts. Output: merged_claims + resolved_contacts + resolved_signals.",
    "context-pack": "Creates focused context summary from claims for downstream steps. Reduces token usage while preserving key info.",
    "8-media": "Fetches company logos and relevant images. Output: URLs and image metadata.",
    "9-dossier-plan": "Plans the dossier sections and routes claims to writers. Output: JSON with section assignments.",
    "writer-executive-summary": "Writes executive summary section. Gets ALL claims + routed claims as guidance.",
    "writer-company-overview": "Writes company overview section. Gets ALL claims + routed claims as guidance.",
    "writer-opportunity-analysis": "Writes opportunity analysis section. Gets ALL claims + routed claims as guidance.",
    "writer-contact-profiles": "Writes contact profiles section. Gets ALL claims + resolved_contacts.",
    "writer-competitive-landscape": "Writes competitive landscape section. Gets ALL claims + routed claims as guidance.",
    "writer-recommended-approach": "Writes recommended approach section. Gets ALL claims + routed claims as guidance.",
}


def get_prompt_file_content(prompt_id: str) -> str:
    """Read prompt file content"""
    prompt_file = PROMPTS_DIR / f"{prompt_id}.md"
    if prompt_file.exists():
        return prompt_file.read_text()
    return ""


def get_all_prompt_files():
    """Get all prompt files from the prompts directory"""
    if not PROMPTS_DIR.exists():
        return []

    prompts = []
    for f in sorted(PROMPTS_DIR.glob("*.md")):
        prompt_id = f.stem
        prompts.append({
            "prompt_id": prompt_id,
            "file_path": str(f),
            "description": PROMPT_DESCRIPTIONS.get(prompt_id, "No description"),
        })
    return prompts


def get_last_step_run(prompt_id: str) -> dict:
    """Get last step run that used this prompt"""
    try:
        repo = V2Repository()
        # Match step name that contains the prompt_id
        result = repo.client.table("v2_step_runs").select("*").like("step", f"%{prompt_id}%").order("started_at", desc=True).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        pass
    return {}


def save_prompt_content(prompt_id: str, content: str) -> bool:
    """Save prompt content to file"""
    prompt_file = PROMPTS_DIR / f"{prompt_id}.md"
    try:
        prompt_file.write_text(content)
        return True
    except Exception as e:
        st.error(f"Failed to save: {e}")
        return False


def render_prompts_page():
    """Main prompts page - simple and clear"""
    st.subheader("Prompts")
    st.markdown("*Every prompt template used by the pipeline. Edit here, changes take effect immediately.*")

    # Get all prompts
    prompts = get_all_prompt_files()

    if not prompts:
        st.warning(f"No prompt files found in {PROMPTS_DIR}")
        return

    # Simple prompt selector
    st.markdown("---")
    prompt_options = [p["prompt_id"] for p in prompts]
    selected_id = st.selectbox(
        "Select Prompt",
        prompt_options,
        key="prompt_selector_main"
    )

    if selected_id:
        render_prompt_detail(selected_id)


def render_prompt_detail(prompt_id: str):
    """Show prompt detail with full content"""
    st.markdown("---")
    st.markdown(f"## `{prompt_id}`")

    # Description
    desc = PROMPT_DESCRIPTIONS.get(prompt_id, "No description available.")
    st.markdown(f"*{desc}*")

    # Get prompt content
    content = get_prompt_file_content(prompt_id)

    if not content:
        st.warning(f"Prompt file not found: {PROMPTS_DIR / f'{prompt_id}.md'}")
        return

    # Show variables used
    st.markdown("### Variables Used")
    import re
    variables = set(re.findall(r'\{\{(\w+)\}\}', content))
    if variables:
        for var in sorted(variables):
            st.write(f"- `{{{{{var}}}}}`")
    else:
        st.info("No variables detected (static prompt)")

    # Show and edit prompt
    st.markdown("### Prompt Template")
    st.markdown("*This is the exact text sent to the LLM (with variables interpolated)*")

    edited_content = st.text_area(
        "Prompt content",
        value=content,
        height=400,
        key=f"editor_{prompt_id}",
        label_visibility="collapsed"
    )

    # Save button
    if st.button("💾 Save Changes", key=f"save_{prompt_id}"):
        if save_prompt_content(prompt_id, edited_content):
            st.success("Saved!")
        else:
            st.error("Save failed")

    # Show last run
    st.markdown("---")
    st.markdown("### Last Run")
    st.markdown("*Most recent execution of this prompt - what input it received, what output it produced.*")

    last_run = get_last_step_run(prompt_id)

    if last_run:
        # Metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Model:** `{last_run.get('model', '-')}`")
        with col2:
            duration = last_run.get("duration_ms")
            st.write(f"**Duration:** {duration/1000:.1f}s" if duration else "**Duration:** -")
        with col3:
            tokens = last_run.get("tokens_in", 0) or 0
            st.write(f"**Tokens:** {tokens:,}")

        # Input
        st.markdown("**INPUT (variables passed in):**")
        input_vars = last_run.get("input_variables", {})
        if input_vars:
            st.json(input_vars)
        else:
            st.info("No input recorded")

        # Output
        st.markdown("**OUTPUT (LLM response):**")
        parsed = last_run.get("parsed_output")
        raw = last_run.get("raw_output", "")

        if parsed:
            # Show claims if present
            if "claims" in parsed:
                claims = parsed.get("claims", [])
                st.write(f"**{len(claims)} claims extracted:**")
                for c in claims[:5]:
                    ctype = c.get("claim_type", "NOTE")
                    stmt = c.get("statement", "")[:80]
                    st.write(f"- `{ctype}`: {stmt}")
                if len(claims) > 5:
                    st.write(f"... and {len(claims) - 5} more")
            else:
                st.json(parsed)

        elif raw:
            st.text_area(
                "Raw output",
                value=raw[:3000] + ("..." if len(raw) > 3000 else ""),
                height=200,
                key=f"last_run_raw_{prompt_id}",
                label_visibility="collapsed"
            )
        else:
            st.info("No output recorded")

        # Error
        if last_run.get("error_message"):
            st.error(f"**Error:** {last_run['error_message']}")

    else:
        st.info("No recent runs found for this prompt")
