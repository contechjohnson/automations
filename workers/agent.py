"""
Agent Worker - OpenAI Agent SDK with Firecrawl Tools
=====================================================
Agent-based execution using OpenAI's Agent SDK for agentic workflows
where the model needs to call tools iteratively.

This module provides:
1. Firecrawl tools (scrape, search, map) as @function_tool decorated functions
2. Pre-configured agent factories (research, firecrawl, full)
3. Sync wrappers for use in RQ workers

Usage:
    from workers.agent import run_firecrawl_agent, run_research_agent

    # Agent with web search (built-in)
    result = run_research_agent("Research Acme Corp's recent projects")

    # Agent with Firecrawl tools
    result = run_firecrawl_agent("Scrape acmecorp.com and summarize their services")

    # Full agent (web search + Firecrawl)
    result = run_full_agent("Find and analyze Acme Corp's latest news")
"""

import os
import json
import asyncio
import httpx
from typing import Optional, Any, List
from agents import Agent, Runner, function_tool, WebSearchTool

# Configuration
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"
ANYMAILFINDER_API_KEY = os.environ.get("ANYMAILFINDER_API_KEY")
APIFY_API_KEY = os.environ.get("APIFY_API_KEY")


# ============================================================================
# Firecrawl Tools (@function_tool decorated)
# ============================================================================

@function_tool
def firecrawl_scrape(url: str, formats: List[str] = None) -> str:
    """
    Scrape a webpage using Firecrawl and return its content as markdown.

    Args:
        url: The URL to scrape (must be a valid http/https URL)
        formats: Output formats - defaults to ["markdown"]

    Returns:
        The scraped content as markdown, or error message if failed
    """
    if formats is None:
        formats = ["markdown"]

    if not FIRECRAWL_API_KEY:
        return "Error: FIRECRAWL_API_KEY not configured"

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{FIRECRAWL_BASE_URL}/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": url,
                    "formats": formats,
                },
            )

            if response.status_code != 200:
                return f"Error: Firecrawl returned {response.status_code}: {response.text[:500]}"

            data = response.json()
            if data.get("success"):
                return data.get("data", {}).get("markdown", "No content returned")
            else:
                return f"Error: {data.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"


@function_tool
def firecrawl_search(query: str, limit: int = 5) -> str:
    """
    Search the web using Firecrawl and return results with scraped content.

    Args:
        query: Search query string
        limit: Maximum number of results (default 5, max 10)

    Returns:
        Search results with title, URL, and scraped content for each result
    """
    if not FIRECRAWL_API_KEY:
        return "Error: FIRECRAWL_API_KEY not configured"

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{FIRECRAWL_BASE_URL}/search",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "limit": min(limit, 10),
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True,
                    },
                },
            )

            if response.status_code != 200:
                return f"Error: Firecrawl returned {response.status_code}: {response.text[:500]}"

            data = response.json()
            if data.get("success"):
                results = data.get("data", [])
                output = []
                for r in results:
                    output.append(f"## {r.get('title', 'Untitled')}")
                    output.append(f"URL: {r.get('url', 'N/A')}")
                    content = r.get("markdown", "No content")
                    # Truncate long content
                    if len(content) > 3000:
                        content = content[:3000] + "\n\n[Content truncated...]"
                    output.append(content)
                    output.append("---")
                return "\n\n".join(output)
            else:
                return f"Error: {data.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error searching '{query}': {str(e)}"


@function_tool
def firecrawl_map(url: str, limit: int = 100) -> str:
    """
    Map a website to discover all its URLs (sitemap discovery).

    Args:
        url: The base URL to map (e.g., https://example.com)
        limit: Maximum number of URLs to return (default 100)

    Returns:
        List of discovered URLs on the website
    """
    if not FIRECRAWL_API_KEY:
        return "Error: FIRECRAWL_API_KEY not configured"

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{FIRECRAWL_BASE_URL}/map",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": url,
                    "limit": limit,
                },
            )

            if response.status_code != 200:
                return f"Error: Firecrawl returned {response.status_code}: {response.text[:500]}"

            data = response.json()
            if data.get("success"):
                urls = data.get("links", [])
                return f"Found {len(urls)} URLs:\n" + "\n".join(urls[:100])
            else:
                return f"Error: {data.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error mapping {url}: {str(e)}"


# ============================================================================
# AnyMailFinder Tools
# ============================================================================

@function_tool
def anymail_finder_lookup(full_name: str, domain: str) -> str:
    """
    Find and verify email address for a person at a company using AnyMailFinder.

    Args:
        full_name: Full name of the person (e.g., "John Smith")
        domain: Company domain (e.g., "acmecorp.com")

    Returns:
        JSON with email, status, and confidence. Only returns SMTP-verified emails.
    """
    if not ANYMAILFINDER_API_KEY:
        return json.dumps({"error": "ANYMAILFINDER_API_KEY not configured"})

    try:
        with httpx.Client(timeout=180.0) as client:  # Long timeout for SMTP verification
            response = client.post(
                "https://api.anymailfinder.com/v5.1/find-email/person",
                headers={
                    "Authorization": ANYMAILFINDER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "full_name": full_name,
                    "domain": domain,
                },
            )

            if response.status_code == 401:
                return json.dumps({"error": "Invalid API key"})
            elif response.status_code == 402:
                return json.dumps({"error": "Insufficient credits"})
            elif response.status_code != 200:
                return json.dumps({"error": f"API error: {response.status_code}"})

            data = response.json()
            return json.dumps({
                "email": data.get("valid_email"),  # Only verified emails
                "raw_email": data.get("email"),  # May include unverified
                "status": data.get("email_status"),  # valid, risky, not_found
                "source": "anymailfinder",
                "full_name": full_name,
                "domain": domain,
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to lookup email: {str(e)}"})


@function_tool
def anymail_finder_linkedin(linkedin_url: str) -> str:
    """
    Find email address from a LinkedIn profile URL using AnyMailFinder.

    Args:
        linkedin_url: LinkedIn profile URL (e.g., "https://www.linkedin.com/in/johnsmith")

    Returns:
        JSON with email, status, and confidence. Only returns SMTP-verified emails.
    """
    if not ANYMAILFINDER_API_KEY:
        return json.dumps({"error": "ANYMAILFINDER_API_KEY not configured"})

    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                "https://api.anymailfinder.com/v5.1/find-email/linkedin",
                headers={
                    "Authorization": ANYMAILFINDER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"linkedin_url": linkedin_url},
            )

            if response.status_code != 200:
                return json.dumps({"error": f"API error: {response.status_code}"})

            data = response.json()
            return json.dumps({
                "email": data.get("valid_email"),
                "status": data.get("email_status"),
                "source": "anymailfinder_linkedin",
                "linkedin_url": linkedin_url,
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to lookup email: {str(e)}"})


# ============================================================================
# Apify LinkedIn Scraper Tools
# ============================================================================

@function_tool
def linkedin_scraper(linkedin_url: str) -> str:
    """
    Scrape a LinkedIn profile to get detailed information including work history,
    skills, education, and potentially email/phone.

    Args:
        linkedin_url: LinkedIn profile URL (e.g., "https://www.linkedin.com/in/johnsmith")

    Returns:
        JSON with profile data including name, title, company, bio, experiences, skills.
    """
    if not APIFY_API_KEY:
        return json.dumps({"error": "APIFY_API_KEY not configured"})

    try:
        from apify_client import ApifyClient

        client = ApifyClient(APIFY_API_KEY)

        run_input = {
            "profileUrls": [linkedin_url]
        }

        # Run the actor and wait for completion (5 min timeout)
        run = client.actor("dev_fusion/linkedin-profile-scraper").call(
            run_input=run_input,
            timeout_secs=300
        )

        if run.get("status") == "FAILED":
            return json.dumps({"error": f"Actor failed: {run.get('statusMessage')}"})

        # Get results
        results = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)

        if not results:
            return json.dumps({"error": "No profile data returned"})

        # Return first result (we only queried one URL)
        profile = results[0]

        # Extract key fields
        return json.dumps({
            "linkedin_url": profile.get("linkedinUrl", linkedin_url),
            "full_name": profile.get("fullName"),
            "first_name": profile.get("firstName"),
            "last_name": profile.get("lastName"),
            "headline": profile.get("headline"),
            "email": profile.get("email"),
            "phone": profile.get("mobileNumber"),
            "title": profile.get("jobTitle"),
            "company": profile.get("companyName"),
            "company_website": profile.get("companyWebsite"),
            "company_industry": profile.get("companyIndustry"),
            "company_size": profile.get("companySize"),
            "location": profile.get("jobLocation"),
            "job_started": profile.get("jobStartedOn"),
            "job_duration": profile.get("currentJobDuration"),
            "connections": profile.get("connections"),
            "followers": profile.get("followers"),
            "experiences": profile.get("experiences", [])[:5],  # Limit to last 5 jobs
            "educations": profile.get("educations", [])[:3],  # Limit to 3 schools
            "skills": profile.get("skills", [])[:10],  # Limit to top 10 skills
            "source": "apify_linkedin",
        })

    except ImportError:
        return json.dumps({"error": "apify-client not installed. Run: pip install apify-client"})
    except Exception as e:
        return json.dumps({"error": f"LinkedIn scrape failed: {str(e)}"})


# ============================================================================
# Agent Factories
# ============================================================================

def create_research_agent(
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
) -> Agent:
    """
    Create an agent with built-in web search capability.
    Good for general research without needing deep scraping.
    """
    default_instructions = """You are a research assistant. Your job is to:
1. Search for relevant information using web search
2. Synthesize findings into clear, actionable insights
3. Cite sources for all claims

Be thorough but concise. Focus on facts, not speculation.
Always include source URLs for verification."""

    return Agent(
        name="Research Agent",
        model=model,
        instructions=instructions or default_instructions,
        tools=[WebSearchTool()],
    )


def create_firecrawl_agent(
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
) -> Agent:
    """
    Create an agent with Firecrawl tools (scrape, search, map).
    Good for deep web scraping and site exploration.
    """
    default_instructions = """You are a web research agent with access to Firecrawl tools.

Available tools:
- firecrawl_scrape(url): Scrape a specific webpage and get its content
- firecrawl_search(query, limit): Search the web and get scraped results
- firecrawl_map(url): Discover all URLs on a website

Strategy for comprehensive research:
1. Start with firecrawl_search to find relevant pages
2. Use firecrawl_scrape for detailed content from key pages
3. Use firecrawl_map to explore site structure if needed

Always cite URLs for claims. Be thorough but efficient with API calls."""

    return Agent(
        name="Firecrawl Agent",
        model=model,
        instructions=instructions or default_instructions,
        tools=[firecrawl_scrape, firecrawl_search, firecrawl_map],
    )


def create_full_agent(
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
) -> Agent:
    """
    Create an agent with BOTH web search AND Firecrawl tools.
    Most capable agent for comprehensive research.
    """
    default_instructions = """You are a comprehensive research agent with access to:

**Web Search (fast, broad):**
- Use for discovering relevant pages quickly

**Firecrawl Tools (deep, targeted):**
- firecrawl_scrape(url): Get full content from a specific page
- firecrawl_search(query): Search and scrape in one step
- firecrawl_map(url): Discover all URLs on a site

**Strategy:**
1. Use web search first to identify relevant sources
2. Use firecrawl_scrape on the most important pages for deep content
3. Use firecrawl_map if you need to explore a site's structure

Synthesize all findings into clear, sourced insights.
Always include URLs for verification."""

    return Agent(
        name="Full Research Agent",
        model=model,
        instructions=instructions or default_instructions,
        tools=[
            WebSearchTool(),
            firecrawl_scrape,
            firecrawl_search,
            firecrawl_map,
        ],
    )


def create_contact_enrichment_agent(
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
) -> Agent:
    """
    Create an agent specialized for contact enrichment with access to:
    - Web search for general research
    - Firecrawl for scraping company/personal pages
    - AnyMailFinder for verified email lookup
    - LinkedIn scraper for profile data

    Best for enriching contact records with emails, bios, work history.
    """
    default_instructions = """You are a contact enrichment specialist. Your job is to find
and verify information about business contacts.

**Available Tools:**

**Web Search & Scraping:**
- web_search: Quick search for public information
- firecrawl_scrape(url): Get content from a specific page
- firecrawl_search(query): Search and scrape results

**Email Lookup (SMTP verified):**
- anymail_finder_lookup(full_name, domain): Find email by name + company domain
- anymail_finder_linkedin(linkedin_url): Find email from LinkedIn profile URL

**LinkedIn Profile Data:**
- linkedin_scraper(linkedin_url): Get full profile with work history, skills, education

**Strategy for enriching a contact:**
1. If you have a LinkedIn URL, use linkedin_scraper first (gets most data)
2. If LinkedIn didn't find email, use anymail_finder_linkedin
3. As fallback, use anymail_finder_lookup with name + company domain
4. Use firecrawl_scrape on company pages for additional context
5. Use web_search for news, press releases, conference appearances

**Output Requirements:**
Return structured data with:
- email (SMTP verified only)
- title, company, bio
- why_they_matter (relevance to the opportunity)
- interesting_facts (for personalized outreach)
- linkedin_url, phone (if found)

Always prioritize verified data over guesses."""

    return Agent(
        name="Contact Enrichment Agent",
        model=model,
        instructions=instructions or default_instructions,
        tools=[
            WebSearchTool(),
            firecrawl_scrape,
            firecrawl_search,
            anymail_finder_lookup,
            anymail_finder_linkedin,
            linkedin_scraper,
        ],
    )


# ============================================================================
# Runner Functions (Async)
# ============================================================================

async def run_agent_async(
    input_text: str,
    agent_type: str = "research",
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
    timeout_seconds: int = 300,  # 5 minute default timeout
) -> dict:
    """
    Run an agent asynchronously with timeout protection.

    Args:
        input_text: The task/question for the agent
        agent_type: "research" | "firecrawl" | "full" | "contact_enrichment"
        model: Model to use (gpt-4.1, gpt-5.2, etc.)
        instructions: Optional custom instructions
        timeout_seconds: Maximum time to wait (default 5 minutes)

    Returns:
        dict with input, output, model, agent_type
    """
    if agent_type == "firecrawl":
        agent = create_firecrawl_agent(model=model, instructions=instructions)
    elif agent_type == "full":
        agent = create_full_agent(model=model, instructions=instructions)
    elif agent_type == "contact_enrichment":
        agent = create_contact_enrichment_agent(model=model, instructions=instructions)
    else:
        agent = create_research_agent(model=model, instructions=instructions)

    try:
        # Add timeout to prevent indefinite hangs
        result = await asyncio.wait_for(
            Runner.run(agent, input_text),
            timeout=timeout_seconds
        )
        return {
            "input": input_text,
            "output": result.final_output,
            "model": model,
            "agent_type": agent_type,
        }
    except asyncio.TimeoutError:
        raise TimeoutError(f"Agent execution timed out after {timeout_seconds} seconds")


# ============================================================================
# Sync Wrappers (for RQ workers and direct calls)
# ============================================================================

def run_research_agent(
    input_text: str,
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
) -> dict:
    """
    Run research agent with web search. Synchronous.

    Usage:
        result = run_research_agent("Research Acme Corp's recent projects")
        print(result["output"])
    """
    return asyncio.run(run_agent_async(input_text, "research", model, instructions))


def run_firecrawl_agent(
    input_text: str,
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
) -> dict:
    """
    Run agent with Firecrawl tools (scrape, search, map). Synchronous.

    Usage:
        result = run_firecrawl_agent("Scrape acmecorp.com and summarize services")
        print(result["output"])
    """
    return asyncio.run(run_agent_async(input_text, "firecrawl", model, instructions))


def run_full_agent(
    input_text: str,
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
) -> dict:
    """
    Run full agent with web search + Firecrawl. Synchronous.
    Most capable option for comprehensive research.

    Usage:
        result = run_full_agent("Research and analyze Acme Corp thoroughly")
        print(result["output"])
    """
    return asyncio.run(run_agent_async(input_text, "full", model, instructions))


def run_contact_enrichment_agent(
    input_text: str,
    model: str = "gpt-4.1",
    instructions: Optional[str] = None,
) -> dict:
    """
    Run contact enrichment agent with web search, Firecrawl, AnyMailFinder, and LinkedIn scraper.
    Specialized for finding verified emails and enriching contact profiles.

    Usage:
        result = run_contact_enrichment_agent(
            "Enrich contact: John Smith, VP Sales at TechCorp (linkedin.com/in/johnsmith)"
        )
        print(result["output"])
    """
    return asyncio.run(run_agent_async(input_text, "contact_enrichment", model, instructions))


# ============================================================================
# Prompt-based Agent Execution
# ============================================================================

def agent_prompt(
    name: str,
    variables: dict = None,
    model: str = "gpt-4.1",
    agent_type: str = "firecrawl",
    log: bool = False,
    tags: list = None,
    notes: str = None,
) -> dict:
    """
    Load a prompt template, interpolate variables, and run with an agent.

    This is like workers/ai.py's prompt() but uses Agent SDK instead of
    direct API calls. Use when the task requires tool calling.

    Args:
        name: Prompt file name (without .md extension)
        variables: Dict of variables to interpolate ({{var}} syntax)
        model: Model to use
        agent_type: "research" | "firecrawl" | "full"
        log: If True, log execution to Supabase execution_logs table
        tags: Optional tags for the log entry
        notes: Optional notes for the log entry

    Returns:
        dict with prompt_name, model, agent_type, input, output, elapsed_seconds
    """
    import time
    from pathlib import Path

    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_path = prompts_dir / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")

    prompt_template = prompt_path.read_text()

    # Interpolate variables
    if variables:
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            prompt_template = prompt_template.replace(placeholder, str(value))

    # Optional logging
    logger = None
    if log:
        from workers.logger import ExecutionLogger
        logger = ExecutionLogger(
            worker_name=f"agent.{agent_type}.{model}",
            automation_slug=name,
            input_data={"prompt_name": name, "model": model, "agent_type": agent_type, "variables": variables},
            tags=tags or [model, agent_type, name.split(".")[0]],
            notes=notes,
        )

    # Run with agent
    start = time.time()

    try:
        if agent_type == "firecrawl":
            result = run_firecrawl_agent(prompt_template, model=model)
        elif agent_type == "full":
            result = run_full_agent(prompt_template, model=model)
        else:
            result = run_research_agent(prompt_template, model=model)

        elapsed = time.time() - start

        result_data = {
            "prompt_name": name,
            "model": model,
            "agent_type": agent_type,
            "input": prompt_template,
            "output": result.get("output", ""),
            "elapsed_seconds": round(elapsed, 2),
        }

        if logger:
            logger.success(result_data)

        return result_data

    except Exception as e:
        if logger:
            logger.fail(e)
        raise
