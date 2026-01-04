"""
Entity Research Worker
======================
Deep investigative research on companies using OpenAI o4-mini-deep-research.
Polls until complete, streams progress updates.

Model: o4-mini-deep-research-2025-06-26
"""

import os
import time
from datetime import datetime
from rq import get_current_job
from openai import OpenAI


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are an investigative journalist with access to comprehensive web search. Your task is to research a company thoroughly, finding corporate structure, domains, leadership, and buying signals. Be exhaustive and cite your sources."""

RESEARCH_PROMPT = """You are an investigative journalist researching a company for B2B sales intelligence.
Your goal is to produce a comprehensive intelligence report with CITATIONS for every claim.

## CLIENT CONTEXT
{client_info}

## TARGET TO RESEARCH
{target_info}

## YOUR MISSION - INVESTIGATIVE DEEP DIVE

Research this company thoroughly. For EVERY fact you report, include a source URL.

### 1. CORPORATE STRUCTURE INVESTIGATION (CRITICAL)
- Is this a shell LLC, project entity, DBA, or subsidiary?
- Who OWNS this company? Trace the ownership chain:
  - Immediate parent company (direct owner)
  - Ultimate parent/holding company (top of chain)
  - Private equity or VC investors (if any)
- What SUBSIDIARIES or DIVISIONS does this company have?
- Are there related entities (joint ventures, spinoffs, DBAs, sister companies)?
- Map the organizational hierarchy

### 2. PROJECT EXECUTION ECOSYSTEM (CRITICAL)
Find ALL parties working on this signal:
- **EPCM/Engineering firm** - Who is doing feasibility study, design, or engineering?
- **Consulting/project management firm** - Is there a contracted development consultant?
- **General contractor** - Who is managing construction or execution?
- **Architect/design firm** - Who is doing design work?
- **Specialized consultants** - Any other consultants hired?

For EACH external firm found, note:
- Company name and domain
- Their role on this project
- Source URL where you found this

### 3. DOMAIN INVESTIGATION (CRITICAL)
Find ALL domains associated with this company:
- Primary company website domain
- Parent company website domain (if different)
- Related business websites (subsidiaries, DBAs, brands)
- EMAIL DOMAIN (may be different from website!)

### 4. COMPANY INTEL (COMPREHENSIVE)
- What do they do? Detailed 5-8 sentence description
- Employee count (with source)
- Revenue/funding (if findable, with source)
- Founded year
- ALL office locations
- Recent acquisitions or divestitures

### 5. KEY PEOPLE (WITH VERIFICATION)
Find decision-makers. For EACH person:
- Full name (exact spelling)
- Title (exact as found)
- Company they work for
- LinkedIn URL (ONLY if you found the EXACT URL - never fabricate)
- Email address (if found)
- Why they matter for this signal
- Source URL

### 6. NETWORK INTELLIGENCE
- Industry associations
- Conferences they sponsor/attend
- Awards or recognition
- Board memberships
- Partner companies

### 7. WARM PATHS (INTRODUCTION OPPORTUNITIES)
Find external connections:
- Mutual connections
- Shared vendors/partners
- Association leadership
- Conference speakers

### 8. ADDITIONAL BUYING SIGNALS
For EACH signal found:
- Signal type
- Description
- Date/timeframe
- Source URL
- Why this indicates buying intent

### 9. INVESTIGATION SUMMARY
- Confidence score (0.0-1.0)
- Why this target matches the ICP
- Key sources used with URLs
"""


def run_entity_research(
    client_info: str,
    target_info: str,
    max_tool_calls: int = 75,
    poll_interval: int = 60,
    max_wait: int = 720
) -> dict:
    """
    Run deep research with progress streaming.
    
    Args:
        client_info: Client context (name, services, ICP)
        target_info: Target company/lead to research
        max_tool_calls: Max web searches (default 75)
        poll_interval: Seconds between status checks (default 60)
        max_wait: Max seconds to wait (default 720 = 12 min)
    
    Returns:
        Research results with timing and usage data
    """
    job = get_current_job()
    
    def update(message: str, percent: int, **extra):
        """Update job progress."""
        if job:
            job.meta = {
                "message": message,
                "percent": percent,
                "timestamp": datetime.utcnow().isoformat(),
                **extra
            }
            job.save_meta()
        print(f"[{percent}%] {message}")
    
    # Initialize
    update("Initializing OpenAI client...", 5)
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=60.0)
    
    # Build prompt
    full_prompt = RESEARCH_PROMPT.format(
        client_info=client_info,
        target_info=target_info
    )
    
    # Start research
    update("Starting deep research...", 10)
    start_time = time.time()
    
    response = client.responses.create(
        model="o4-mini-deep-research-2025-06-26",
        input=[
            {"role": "developer", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt}
        ],
        tools=[{"type": "web_search_preview"}],
        background=True,
        reasoning={"summary": "auto"},
        max_tool_calls=max_tool_calls
    )
    
    response_id = response.id
    update(f"Research started. ID: {response_id}", 15, response_id=response_id)
    
    # Polling loop
    poll_count = 0
    final_status = "timeout"
    
    while time.time() - start_time < max_wait:
        time.sleep(poll_interval)
        poll_count += 1
        elapsed = int(time.time() - start_time)
        
        try:
            response = client.responses.retrieve(response_id)
            status = response.status
            
            # Calculate progress (15% to 90% during polling)
            progress_pct = min(15 + (poll_count * 10), 90)
            update(
                f"Poll #{poll_count}: {status} ({elapsed}s elapsed)", 
                progress_pct,
                openai_status=status,
                elapsed_seconds=elapsed
            )
            
            if status == "completed":
                final_status = "completed"
                break
            elif status in ["failed", "cancelled"]:
                final_status = status
                break
                
        except Exception as e:
            update(f"Poll error: {e}", progress_pct)
    
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    
    # Build result
    result = {
        "response_id": response_id,
        "status": final_status,
        "timing": {
            "started_at": datetime.fromtimestamp(start_time).isoformat(),
            "completed_at": datetime.fromtimestamp(end_time).isoformat(),
            "elapsed_seconds": round(elapsed_seconds, 1),
            "elapsed_minutes": round(elapsed_seconds / 60, 2),
            "poll_count": poll_count
        }
    }
    
    if final_status == "completed":
        update("Extracting results...", 95)
        
        try:
            response = client.responses.retrieve(response_id)
            
            output_text = None
            tool_calls_count = 0
            
            for item in response.output:
                if hasattr(item, 'content') and item.type == "message":
                    for block in item.content:
                        if hasattr(block, 'text'):
                            output_text = block.text
                if hasattr(item, 'type') and item.type == "web_search_call":
                    tool_calls_count += 1
            
            result["output_text"] = output_text
            result["tool_calls_count"] = tool_calls_count
            
            if hasattr(response, 'usage') and response.usage:
                result["usage"] = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "web_search_calls": tool_calls_count,
                    "estimated_cost_usd": round(
                        (response.usage.input_tokens / 1_000_000 * 2) +
                        (response.usage.output_tokens / 1_000_000 * 8) +
                        (tool_calls_count * 0.01), 4
                    )
                }
            
            update("Complete!", 100)
            
        except Exception as e:
            result["error"] = str(e)
            update(f"Error extracting results: {e}", 100)
    else:
        update(f"Research ended with status: {final_status}", 100)
    
    return result
