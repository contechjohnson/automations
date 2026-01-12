"""
Step executor - executes individual pipeline steps with I/O capture
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
                value_str = json.dumps(value, indent=2)
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
    """Extract claims from step output"""
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
        - Extracted claims (if produces_claims)
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

            # Parse output
            parsed_output = parse_json_output(raw_output) if raw_output else None

            # Extract claims if applicable
            claims = []
            if step_config.produces_claims and parsed_output:
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
            from workers.agent import run_firecrawl_agent, run_research_agent, run_full_agent

            # Choose agent based on tools
            tools = config.uses_tools or []

            if "firecrawl_scrape" in tools or "firecrawl_search" in tools:
                if "web_search" in tools:
                    result = run_full_agent(prompt, model=config.model)
                else:
                    result = run_firecrawl_agent(prompt, model=config.model)
            else:
                result = run_research_agent(prompt, model=config.model)

            # Agents return the final output
            output = result.get("output", result) if isinstance(result, dict) else str(result)

        except ImportError as e:
            # Fall back to regular LLM call if agents SDK not available
            print(f"Warning: Agent SDK not available ({e}), falling back to sync call")
            from workers.ai import ai
            output = ai(prompt, model=config.model, temperature=0.7)

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
