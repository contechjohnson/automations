# workers/ai.py
"""
Simple AI module - swap models by changing a string.

Usage:
    from workers.ai import ai, agent, research
    
    # Basic calls
    result = ai("Summarize this...")                      # Default: gpt-4.1
    result = ai("Analyze...", model="gpt-5.2")           # Flagship
    result = ai("Quick check", model="gpt-4.1-mini")     # Fast/cheap
    result = ai("Think hard", model="o4-mini")           # Reasoning
    result = ai("Summarize", model="gemini-2.5-flash")   # Google
    
    # Deep research (async, can take minutes)
    result = research("Research Virginia data centers")
    
    # Agent with tools
    result = agent("Scrape this URL and summarize", tools=firecrawl_tools)
"""

import os
import time
from openai import OpenAI
import google.generativeai as genai

# Initialize clients
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def ai(
    prompt: str,
    model: str = "gpt-4.1",
    system: str = None,
    temperature: float = 0.7,
    reasoning_effort: str = None,  # For o-series: low, medium, high
) -> str:
    """
    Call any AI model. Returns text.
    
    Models:
        OpenAI: gpt-5.2, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, o3, o4-mini
        Gemini: gemini-2.5-pro, gemini-2.5-flash, gemini-3-flash-preview
    """
    
    # === OpenAI Models ===
    if model.startswith(("gpt-", "o3", "o4-mini")) and "deep-research" not in model:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        # O-series models support reasoning_effort
        if model.startswith(("o3", "o4")) and reasoning_effort:
            params["reasoning_effort"] = reasoning_effort
        
        response = openai_client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    # === Gemini Models ===
    if model.startswith("gemini"):
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        gmodel = genai.GenerativeModel(model)
        
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = gmodel.generate_content(full_prompt)
        return response.text
    
    raise ValueError(f"Unknown model: {model}")


def research(
    prompt: str,
    model: str = "o4-mini-deep-research-2025-06-26",
    timeout: int = 1800,  # 30 min max
    poll_interval: int = 15,
) -> dict:
    """
    Deep research using OpenAI Responses API.
    
    This is async and can take 5-30 minutes.
    Returns dict with 'content', 'sources', 'usage'.
    """
    
    # Submit research request with background mode
    response = openai_client.responses.create(
        model=model,
        input=[{
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}]
        }],
        reasoning={"summary": "auto"},
        tools=[{"type": "web_search_preview"}],
        background=True,
    )
    
    response_id = response.id
    status = response.status
    
    # Poll until complete
    elapsed = 0
    while status in ["queued", "in_progress"] and elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval
        
        response = openai_client.responses.retrieve(response_id)
        status = response.status
        
        print(f"Research status: {status} ({elapsed}s elapsed)")
    
    if status != "completed":
        return {
            "content": None,
            "status": status,
            "error": f"Research did not complete. Status: {status}",
            "elapsed_seconds": elapsed,
        }
    
    # Extract the final text output
    content = None
    sources = []
    for item in response.output:
        if hasattr(item, 'content'):
            for c in item.content:
                if hasattr(c, 'text'):
                    content = c.text
        if item.type == "web_search_call":
            sources.append(item)
    
    return {
        "content": content,
        "status": "completed",
        "elapsed_seconds": elapsed,
        "sources": sources,
        "usage": response.usage.model_dump() if response.usage else None,
    }


def agent(
    prompt: str,
    tools: list = None,
    model: str = "gpt-4.1",
    system: str = "You are a helpful assistant that uses tools to accomplish tasks.",
    max_turns: int = 10,
) -> dict:
    """
    Run OpenAI Agent with tools.
    
    Example with Firecrawl:
        from workers.ai import agent, firecrawl_tools
        result = agent("Scrape example.com and summarize", tools=firecrawl_tools)
    """
    from agents import Agent, Runner
    
    agent_instance = Agent(
        name="AutomationAgent",
        instructions=system,
        model=model,
        tools=tools or [],
    )
    
    result = Runner.run_sync(agent_instance, prompt)
    
    return {
        "content": result.final_output,
        "model": model,
        "turns": len(result.new_items) if hasattr(result, 'new_items') else None,
    }


# === Pre-built Tools ===

def firecrawl_scrape(url: str, formats: list = None) -> dict:
    """Scrape a URL using Firecrawl API."""
    import requests
    
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    response = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "url": url,
            "formats": formats or ["markdown"],
        }
    )
    return response.json()


def firecrawl_crawl(url: str, limit: int = 10) -> dict:
    """Crawl a website using Firecrawl API."""
    import requests
    
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    response = requests.post(
        "https://api.firecrawl.dev/v1/crawl",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "url": url,
            "limit": limit,
        }
    )
    return response.json()


# For use with Agent SDK - wrap as function tools
try:
    from agents import function_tool
    
    @function_tool
    def scrape_url(url: str) -> str:
        """Scrape a webpage and return its content as markdown."""
        result = firecrawl_scrape(url)
        if result.get("success"):
            return result.get("data", {}).get("markdown", "No content found")
        return f"Error: {result.get('error', 'Unknown error')}"
    
    @function_tool
    def crawl_website(url: str, max_pages: int = 10) -> str:
        """Crawl a website and return content from multiple pages."""
        result = firecrawl_crawl(url, limit=max_pages)
        return str(result)
    
    # Export tools for easy access
    firecrawl_tools = [scrape_url, crawl_website]
    
except ImportError:
    # agents package not installed
    firecrawl_tools = []


# === Quick aliases ===

def quick(prompt: str, system: str = None) -> str:
    """Fastest/cheapest - gpt-4.1-nano"""
    return ai(prompt, model="gpt-4.1-nano", system=system)

def smart(prompt: str, system: str = None) -> str:
    """Smartest - gpt-5.2"""
    return ai(prompt, model="gpt-5.2", system=system)

def think(prompt: str, effort: str = "medium", system: str = None) -> str:
    """Reasoning - o4-mini with configurable effort"""
    return ai(prompt, model="o4-mini", reasoning_effort=effort, system=system)

def gemini_call(prompt: str, model: str = "gemini-2.5-flash", system: str = None) -> str:
    """Google Gemini models"""
    return ai(prompt, model=model, system=system)


# === Model info ===

MODELS = {
    # OpenAI Flagship
    "gpt-5.2": {"provider": "openai", "type": "chat", "context": 256_000},
    "gpt-4.1": {"provider": "openai", "type": "chat", "context": 1_000_000},
    "gpt-4.1-mini": {"provider": "openai", "type": "chat", "context": 1_000_000},
    "gpt-4.1-nano": {"provider": "openai", "type": "chat", "context": 1_000_000},
    
    # OpenAI Reasoning
    "o3": {"provider": "openai", "type": "reasoning", "context": 200_000},
    "o4-mini": {"provider": "openai", "type": "reasoning", "context": 200_000},
    
    # OpenAI Deep Research
    "o4-mini-deep-research-2025-06-26": {"provider": "openai", "type": "research"},
    "o3-deep-research-2025-06-26": {"provider": "openai", "type": "research"},
    
    # Google Gemini
    "gemini-2.5-pro": {"provider": "google", "type": "chat", "context": 1_000_000},
    "gemini-2.5-flash": {"provider": "google", "type": "chat", "context": 1_000_000},
    "gemini-2.5-flash-lite": {"provider": "google", "type": "chat", "context": 1_000_000},
    "gemini-3-flash-preview": {"provider": "google", "type": "chat", "context": 1_000_000},
}

def list_models():
    """List all available models."""
    return list(MODELS.keys())
