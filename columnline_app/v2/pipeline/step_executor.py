"""
Step executor - executes individual pipeline steps with I/O capture

Key Architecture:
- Claims extraction is an LLM step (same prompt for all extractors)
- After narrative-producing steps, we run claims-extraction.md
- Claims merge happens at 7b-insight using claims-merge.md
- Context packs use context-pack.md
"""
import os
import re
import json
import time
import traceback
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from ..config import StepConfig, ExecutionMode, PIPELINE_STEPS
from ..db.models import StepRun, StepStatus, Claim, ClaimType, SourceTier, Confidence
from ..db.repository import V2Repository
from .state import PipelineState


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        from datetime import date
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def interpolate_prompt(template: str, variables: Dict[str, Any]) -> str:
    """
    Interpolate variables into prompt template.
    Supports {{variable}} and {{#if variable}}...{{/if}} syntax.
    """
    result = template

    # Handle conditionals first
    # {{#if variable}}content{{/if}}
    if_pattern = r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}'
    for match in re.finditer(if_pattern, result, re.DOTALL):
        var_name = match.group(1)
        content = match.group(2)
        if variables.get(var_name):
            # Keep content, remove tags
            result = result.replace(match.group(0), content)
        else:
            # Remove entire block
            result = result.replace(match.group(0), "")

    # Handle simple variable substitution
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        if placeholder in result:
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2, cls=DateTimeEncoder)
            elif isinstance(value, datetime):
                value_str = value.isoformat()
            else:
                value_str = str(value)
            result = result.replace(placeholder, value_str)

    return result


def load_prompt_content(prompt_id: str) -> str:
    """Load prompt content from file"""
    prompt_file = f"prompts/v2/{prompt_id}.md"
    if os.path.exists(prompt_file):
        with open(prompt_file, "r") as f:
            return f.read()
    raise FileNotFoundError(f"Prompt file not found: {prompt_file}")


def parse_json_output(raw_output: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from LLM output"""
    # Try direct parse first
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code blocks
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(json_pattern, raw_output)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Try to find JSON object/array anywhere
    for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
        match = re.search(pattern, raw_output)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    return None


def extract_claims_from_output(
    output: Dict[str, Any],
    pipeline_run_id: str,
    step_run_id: str,
    source_step: str
) -> List[Claim]:
    """Extract claims from LLM claims extraction output (JSON format)"""
    claims = []

    # Look for claims array in output
    claims_data = output.get("claims", [])
    if not claims_data and isinstance(output, list):
        claims_data = output

    for i, claim_data in enumerate(claims_data):
        try:
            claim = Claim(
                pipeline_run_id=pipeline_run_id,
                step_run_id=step_run_id,
                claim_id=claim_data.get("claim_id", f"{source_step}_{i+1:03d}"),
                claim_type=ClaimType(claim_data.get("claim_type", "NOTE")),
                statement=claim_data.get("statement", "")[:500],
                entities=claim_data.get("entities", []),
                date_in_claim=claim_data.get("date_in_claim"),
                source_url=claim_data.get("source_url"),
                source_name=claim_data.get("source_name", "Unknown"),
                source_tier=SourceTier(claim_data.get("source_tier", "OTHER")),
                confidence=Confidence(claim_data.get("confidence", "MEDIUM")),
                source_step=source_step,
            )
            claims.append(claim)
        except Exception as e:
            print(f"Warning: Failed to parse claim: {e}")
            continue

    return claims


async def run_claims_extraction_llm(
    narrative: str,
    source_step: str,
    company_name: str,
    model: str = "gpt-4.1"
) -> Optional[Dict[str, Any]]:
    """
    Run the claims extraction LLM step on narrative output.
    This is THE post-processing step that converts narrative to atomic claims.
    """
    from workers.ai import ai

    # Load claims extraction prompt
    prompt_template = load_prompt_content("claims-extraction")

    # Interpolate variables
    variables = {
        "source_step": source_step,
        "company_name": company_name,
        "narrative": narrative,
    }
    prompt = interpolate_prompt(prompt_template, variables)

    # Run LLM
    result = ai(prompt, model=model, temperature=0.3)  # Lower temp for structured output

    # Parse JSON output
    return parse_json_output(result)


async def run_claims_merge_llm(
    all_claims: List[Dict[str, Any]],
    company_name: str,
    pipeline_run_id: str,
    model: str = "gpt-4.1"
) -> Optional[Dict[str, Any]]:
    """
    Run the claims merge LLM step at 7b-insight.
    This is the single reconciliation point for all accumulated claims.

    Returns a merge result dict with at minimum "merged_claims" array.
    If merge fails, returns passthrough of input claims to ensure downstream steps work.
    """
    from workers.ai import ai

    # Load claims merge prompt
    prompt_template = load_prompt_content("claims-merge")

    # Interpolate variables
    variables = {
        "company_name": company_name,
        "pipeline_run_id": pipeline_run_id,
        "all_claims": json.dumps(all_claims, indent=2, cls=DateTimeEncoder),
        "input_claims_count": len(all_claims),
    }
    prompt = interpolate_prompt(prompt_template, variables)

    print(f"Claims merge prompt length: {len(prompt)} chars for {len(all_claims)} claims")

    # Run LLM with retry on parse failure
    max_retries = 2
    result = None
    parsed = None

    for attempt in range(max_retries):
        result = ai(prompt, model=model, temperature=0.3)

        print(f"Claims merge attempt {attempt + 1}: raw result length = {len(result) if result else 0} chars")
        if result:
            print(f"Claims merge result preview: {result[:500]}...")

        # Parse JSON output
        parsed = parse_json_output(result)

        if parsed and "merged_claims" in parsed:
            print(f"Claims merge parsed successfully with keys: {list(parsed.keys())}")
            return parsed
        elif parsed:
            print(f"WARNING: Parsed JSON but missing 'merged_claims' key. Keys: {list(parsed.keys())}")
            # If we got parsed JSON without merged_claims, might be malformed
            if attempt < max_retries - 1:
                print("Retrying claims merge...")
                continue
        elif result:
            print(f"WARNING: Failed to parse claims merge JSON. Result starts with: {result[:300]}")
            if attempt < max_retries - 1:
                print("Retrying claims merge...")
                continue

    # If all retries failed, create passthrough result
    print(f"Claims merge failed after {max_retries} attempts. Creating passthrough result.")
    passthrough_result = create_passthrough_merge_result(all_claims)
    return passthrough_result


def create_passthrough_merge_result(all_claims: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a passthrough merge result when LLM merge fails.
    This ensures downstream steps still receive all claims.
    """
    # Convert input claims to merged claim format
    merged_claims = []
    for i, claim in enumerate(all_claims):
        merged_claims.append({
            "merged_claim_id": f"PASS_{i+1:03d}",
            "original_claim_ids": [claim.get("claim_id", f"unknown_{i}")],
            "claim_type": claim.get("claim_type", "NOTE"),
            "statement": claim.get("statement", ""),
            "entities": claim.get("entities", []),
            "sources": [{
                "url": claim.get("source_url"),
                "name": claim.get("source_name", "Unknown"),
                "tier": claim.get("source_tier", "OTHER")
            }],
            "confidence": claim.get("confidence", "MEDIUM"),
            "reconciliation_type": "passthrough"
        })

    # Extract signals from passthrough claims (claims with SIGNAL type)
    resolved_signals = []
    for i, claim in enumerate(all_claims):
        if claim.get("claim_type") == "SIGNAL":
            resolved_signals.append({
                "signal_id": f"S_PASS_{i+1:03d}",
                "signal_type": "UNKNOWN",
                "description": claim.get("statement", ""),
                "date": claim.get("date_in_claim"),
                "strength": "UNKNOWN",
                "source_tier": claim.get("source_tier", "OTHER"),
                "evidence_claim_ids": [claim.get("claim_id", f"unknown_{i}")],
                "why_early": "Unprocessed - passthrough mode"
            })

    # Extract contacts from passthrough claims (claims with CONTACT type)
    resolved_contacts = []
    for i, claim in enumerate(all_claims):
        if claim.get("claim_type") == "CONTACT":
            entities = claim.get("entities", [])
            resolved_contacts.append({
                "contact_id": f"C_PASS_{i+1:03d}",
                "full_name": entities[0] if entities else "Unknown",
                "title": "",
                "organization": entities[1] if len(entities) > 1 else "",
                "evidence_claim_ids": [claim.get("claim_id", f"unknown_{i}")],
                "confidence": claim.get("confidence", "MEDIUM")
            })

    return {
        "merged_claims": merged_claims,
        "resolved_contacts": resolved_contacts,
        "resolved_signals": resolved_signals,
        "timeline": [],
        "conflicts_resolved": [],
        "needs_verification": [],
        "merge_stats": {
            "input_claims": len(all_claims),
            "output_claims": len(merged_claims),
            "duplicates_merged": 0,
            "conflicts_resolved": 0,
            "contacts_identified": len(resolved_contacts),
            "signals_identified": len(resolved_signals),
            "timeline_events": 0,
            "passthrough": True,
            "reason": "LLM merge failed - claims passed through unmerged"
        }
    }


async def run_context_pack_llm(
    merged_claims: List[Dict[str, Any]],
    company_name: str,
    pack_type: str,
    target_step: str,
    model: str = "gpt-4.1"
) -> Optional[Dict[str, Any]]:
    """
    Run the context pack generation LLM step.
    Creates a focused context summary from claims for downstream steps.
    """
    from workers.ai import ai

    # Load context pack prompt
    prompt_template = load_prompt_content("context-pack")

    # Interpolate variables
    variables = {
        "company_name": company_name,
        "pack_type": pack_type,
        "target_step": target_step,
        "merged_claims": json.dumps(merged_claims, indent=2, cls=DateTimeEncoder),
        "claims_count": len(merged_claims),
        "timestamp": datetime.utcnow().isoformat(),
    }
    prompt = interpolate_prompt(prompt_template, variables)

    # Run LLM
    result = ai(prompt, model=model, temperature=0.5)

    # Parse JSON output
    return parse_json_output(result)


class StepExecutor:
    """Executes individual pipeline steps"""

    def __init__(self, repo: V2Repository):
        self.repo = repo

    async def execute_step(
        self,
        step_config: StepConfig,
        state: PipelineState,
    ) -> Tuple[StepRun, Optional[Dict[str, Any]], List[Claim]]:
        """
        Execute a single step and return:
        - StepRun record
        - Parsed output (if any)
        - Extracted claims (if produces_claims via LLM extraction)
        """
        step_id = step_config.prompt_id
        start_time = time.time()

        # Create step run record
        step_run = self.repo.create_step_run(StepRun(
            pipeline_run_id=state.pipeline_run_id,
            step=step_id,
            prompt_id=step_id,
            status=StepStatus.RUNNING,
            model=step_config.model,
            started_at=datetime.utcnow(),
        ))

        try:
            # Load prompt template
            prompt_template = load_prompt_content(step_id)

            # Get required variables from template
            var_pattern = r'\{\{(\w+)\}\}'
            required_vars = list(set(re.findall(var_pattern, prompt_template)))

            # Build variables with lineage
            variables, lineage = state.build_variables(required_vars)

            # Interpolate prompt
            interpolated_prompt = interpolate_prompt(prompt_template, variables)

            # Update step run with input
            self.repo.update_step_run(step_run.id, {
                "input_variables": variables,
                "interpolated_prompt": interpolated_prompt,
            })

            # Execute based on mode
            if step_config.execution_mode == ExecutionMode.SYNC:
                raw_output, tokens_in, tokens_out = await self._execute_sync(
                    interpolated_prompt, step_config
                )
            elif step_config.execution_mode == ExecutionMode.AGENT:
                raw_output, tokens_in, tokens_out = await self._execute_agent(
                    interpolated_prompt, step_config
                )
            elif step_config.execution_mode == ExecutionMode.BACKGROUND:
                raw_output, tokens_in, tokens_out = await self._execute_background(
                    interpolated_prompt, step_config, step_run.id
                )
            else:
                raise ValueError(f"Unknown execution mode: {step_config.execution_mode}")

            # Parse output - may be JSON or narrative
            parsed_output = parse_json_output(raw_output) if raw_output else None

            # Extract claims via LLM if this step produces claims
            claims = []
            if step_config.produces_claims and step_config.extract_claims_after:
                # Run claims extraction LLM on the narrative output
                company_name = state.get_variable("company_name") or "Unknown"
                narrative = raw_output or ""

                print(f"Running claims extraction LLM for {step_id}...")
                extraction_result = await run_claims_extraction_llm(
                    narrative=narrative,
                    source_step=step_id,
                    company_name=company_name,
                    model="gpt-4.1"  # Use 4.1 for extraction
                )

                if extraction_result:
                    claims = extract_claims_from_output(
                        extraction_result,
                        state.pipeline_run_id,
                        step_run.id,
                        step_id
                    )
                    print(f"Extracted {len(claims)} claims from {step_id}")

                    # Update parsed_output with extraction result for tracking
                    if parsed_output is None:
                        parsed_output = {}
                    parsed_output["_claims_extraction"] = extraction_result.get("extraction_summary", {})

            elif step_config.produces_claims and parsed_output:
                # Fallback: Direct extraction from JSON output (legacy)
                claims = extract_claims_from_output(
                    parsed_output,
                    state.pipeline_run_id,
                    step_run.id,
                    step_id
                )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Update step run with results
            step_run = self.repo.update_step_run(step_run.id, {
                "status": StepStatus.COMPLETED.value,
                "raw_output": raw_output,
                "parsed_output": parsed_output,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "duration_ms": duration_ms,
                "completed_at": datetime.utcnow().isoformat(),
            })

            return step_run, parsed_output, claims

        except Exception as e:
            # Record failure
            duration_ms = int((time.time() - start_time) * 1000)
            step_run = self.repo.update_step_run(step_run.id, {
                "status": StepStatus.FAILED.value,
                "error_message": str(e),
                "error_traceback": traceback.format_exc(),
                "duration_ms": duration_ms,
                "completed_at": datetime.utcnow().isoformat(),
            })
            raise

    async def execute_claims_merge(
        self,
        state: PipelineState,
    ) -> Tuple[Optional[Dict[str, Any]], List[Claim]]:
        """
        Execute claims merge at the insight step.
        This processes ALL accumulated claims into merged claims.
        """
        company_name = state.get_variable("company_name") or "Unknown"

        # Get all accumulated claims as dicts
        all_claims = [
            {
                "claim_id": c.claim_id,
                "claim_type": c.claim_type.value if hasattr(c.claim_type, 'value') else c.claim_type,
                "statement": c.statement,
                "entities": c.entities,
                "date_in_claim": c.date_in_claim,
                "source_url": c.source_url,
                "source_name": c.source_name,
                "source_tier": c.source_tier.value if hasattr(c.source_tier, 'value') else c.source_tier,
                "confidence": c.confidence.value if hasattr(c.confidence, 'value') else c.confidence,
                "source_step": c.source_step,
            }
            for c in state.claims
        ]

        if not all_claims:
            print("No claims to merge")
            return None, []

        print(f"Running claims merge LLM on {len(all_claims)} claims...")
        merge_result = await run_claims_merge_llm(
            all_claims=all_claims,
            company_name=company_name,
            pipeline_run_id=state.pipeline_run_id,
            model="gpt-4.1"
        )

        if not merge_result:
            print("Claims merge returned no result")
            return None, []

        # Extract merged claims
        merged_claims = []
        for mc in merge_result.get("merged_claims", []):
            try:
                claim = Claim(
                    pipeline_run_id=state.pipeline_run_id,
                    claim_id=mc.get("merged_claim_id", "M_000"),
                    claim_type=ClaimType(mc.get("claim_type", "NOTE")),
                    statement=mc.get("statement", "")[:500],
                    entities=mc.get("entities", []),
                    source_url=mc.get("sources", [{}])[0].get("url") if mc.get("sources") else None,
                    source_name=mc.get("sources", [{}])[0].get("name", "Merged") if mc.get("sources") else "Merged",
                    source_tier=SourceTier(mc.get("sources", [{}])[0].get("tier", "OTHER")) if mc.get("sources") else SourceTier.OTHER,
                    confidence=Confidence(mc.get("confidence", "MEDIUM")),
                    source_step="7b-insight",
                    is_merged=True,
                )
                merged_claims.append(claim)
            except Exception as e:
                print(f"Warning: Failed to parse merged claim: {e}")
                continue

        print(f"Created {len(merged_claims)} merged claims")
        return merge_result, merged_claims

    async def generate_context_pack(
        self,
        state: PipelineState,
        pack_type: str,
        target_step: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a context pack using LLM from current claims.
        """
        company_name = state.get_variable("company_name") or "Unknown"

        # Get merged claims if available, else raw claims
        claims_to_use = state.merged_claims if state.merged_claims else state.claims
        claims_data = [
            {
                "claim_id": c.claim_id,
                "claim_type": c.claim_type.value if hasattr(c.claim_type, 'value') else c.claim_type,
                "statement": c.statement,
                "entities": c.entities,
                "confidence": c.confidence.value if hasattr(c.confidence, 'value') else c.confidence,
            }
            for c in claims_to_use
        ]

        if not claims_data:
            print(f"No claims available for context pack {pack_type}")
            return None

        print(f"Generating context pack '{pack_type}' from {len(claims_data)} claims...")
        pack_result = await run_context_pack_llm(
            merged_claims=claims_data,
            company_name=company_name,
            pack_type=pack_type,
            target_step=target_step,
            model="gpt-4.1"
        )

        return pack_result

    async def _execute_sync(
        self,
        prompt: str,
        config: StepConfig
    ) -> Tuple[str, int, int]:
        """Execute sync LLM call"""
        from workers.ai import ai

        result = ai(
            prompt,
            model=config.model,
            temperature=0.7,
        )

        # Estimate tokens (rough)
        tokens_in = len(prompt.split()) * 1.3
        tokens_out = len(result.split()) * 1.3

        return result, int(tokens_in), int(tokens_out)

    async def _execute_agent(
        self,
        prompt: str,
        config: StepConfig
    ) -> Tuple[str, int, int]:
        """Execute agent with tools - falls back to sync call if agents SDK unavailable"""
        try:
            from workers.agent import run_agent_async

            # Use agent_type from config if specified, otherwise infer from tools
            if config.agent_type:
                agent_type = config.agent_type
            else:
                # Fallback: choose agent type based on tools
                tools = config.uses_tools or []

                if "firecrawl_scrape" in tools or "firecrawl_search" in tools:
                    if "web_search" in tools:
                        agent_type = "full"
                    else:
                        agent_type = "firecrawl"
                else:
                    agent_type = "research"

            # Use async agent function directly (avoids asyncio.run conflict)
            # Pass timeout from config (default 300s = 5 min)
            result = await run_agent_async(
                prompt,
                agent_type=agent_type,
                model=config.model,
                timeout_seconds=config.timeout_seconds
            )

            # Agents return the final output
            output = result.get("output", result) if isinstance(result, dict) else str(result)

        except ImportError as e:
            # Fall back to regular LLM call if agents SDK not available
            print(f"Warning: Agent SDK not available ({e}), falling back to sync call")
            from workers.ai import ai
            output = ai(prompt, model=config.model, temperature=0.7)
        except TimeoutError as e:
            # Agent timed out - re-raise with more context
            raise TimeoutError(f"Agent execution for {config.prompt_id} timed out: {e}")

        tokens_in = len(prompt.split()) * 1.3
        tokens_out = len(output.split()) * 1.3

        return output, int(tokens_in), int(tokens_out)

    async def _execute_background(
        self,
        prompt: str,
        config: StepConfig,
        step_run_id: str
    ) -> Tuple[str, int, int]:
        """Execute deep research (background mode with polling)"""
        from workers.ai import research, poll_research
        import asyncio

        # Start background research
        result = research(
            prompt,
            model=config.model,
            background=True
        )

        response_id = result.get("response_id")
        if not response_id:
            raise ValueError("No response_id returned from background research")

        # Store response_id for tracking
        self.repo.update_step_run(step_run_id, {"response_id": response_id})

        # Poll until complete (with timeout)
        max_wait = config.timeout_seconds
        poll_interval = 30
        elapsed = 0

        while elapsed < max_wait:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            poll_result = poll_research(response_id)
            status = poll_result.get("status")

            if status == "completed":
                output = poll_result.get("output", "")
                tokens_in = poll_result.get("tokens_in", 0)
                tokens_out = poll_result.get("tokens_out", 0)
                return output, tokens_in, tokens_out
            elif status == "failed":
                raise Exception(f"Deep research failed: {poll_result.get('error')}")

        raise TimeoutError(f"Deep research timed out after {max_wait} seconds")
