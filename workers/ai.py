"""
Universal AI Module - Updated with proper Responses API for deep research
"""
import os
import json
import time
from pathlib import Path
from openai import OpenAI

# Prompts directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Initialize clients
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Model mappings
OPENAI_MODELS = {
    "gpt-5.2": "gpt-5.2",
    "gpt-4.1": "gpt-4.1", 
    "gpt-4.1-mini": "gpt-4.1-mini",
    "gpt-4.1-nano": "gpt-4.1-nano",
    "o3": "o3",
    "o4-mini": "o4-mini",
    "o4-mini-deep-research": "o4-mini-deep-research-2025-06-26",
    "o3-deep-research": "o3-deep-research-2025-06-26",
}

DEEP_RESEARCH_MODELS = ["o4-mini-deep-research", "o3-deep-research", "o4-mini-deep-research-2025-06-26", "o3-deep-research-2025-06-26"]


def ai(prompt: str, model: str = "gpt-4.1", system: str = None, temperature: float = 0.7) -> str:
    """
    Universal AI completion - routes to appropriate provider/model.
    For standard chat completions (not deep research).
    """
    model_id = OPENAI_MODELS.get(model, model)
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    response = openai_client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=temperature,
    )
    
    return response.choices[0].message.content


def research(prompt: str, model: str = "o4-mini-deep-research", background: bool = True) -> dict:
    """
    Deep research using OpenAI Responses API with web search.
    
    Uses /v1/responses endpoint with web_search_preview tool.
    Defaults to background mode since these take 5-10 minutes.
    
    Args:
        prompt: Research query/task
        model: Deep research model (o4-mini-deep-research or o3-deep-research)
        background: If True (default), returns immediately with response ID for polling
        
    Returns:
        dict with output, sources, usage info (or response_id if background)
    """
    model_id = OPENAI_MODELS.get(model, model)
    
    # Build request for Responses API
    request_params = {
        "model": model_id,
        "input": prompt,
        "tools": [
            {"type": "web_search_preview"},
        ],
        "reasoning": {"summary": "auto"},
    }
    
    if background:
        request_params["background"] = True
    
    # Use responses endpoint with long timeout
    response = openai_client.responses.create(**request_params)
    
    # If background mode, return response ID for polling
    if background:
        return {
            "response_id": response.id,
            "status": response.status,
            "model": model_id,
        }
    
    # Synchronous mode - extract output
    output_text = ""
    annotations = []
    
    if hasattr(response, 'output_text'):
        output_text = response.output_text
    elif hasattr(response, 'output'):
        for item in response.output:
            if hasattr(item, 'content'):
                for content in item.content:
                    if hasattr(content, 'text'):
                        output_text += content.text
                    if hasattr(content, 'annotations'):
                        annotations.extend(content.annotations)
    
    return {
        "output": output_text,
        "annotations": annotations,
        "model": model_id,
        "usage": response.usage.model_dump() if hasattr(response, 'usage') and response.usage else None,
    }


def poll_research(response_id: str) -> dict:
    """
    Poll for background research completion.
    
    Args:
        response_id: ID from background research request
        
    Returns:
        dict with status, and output if completed
    """
    response = openai_client.responses.retrieve(response_id)
    
    result = {
        "response_id": response_id,
        "status": response.status,
    }
    
    if response.status == "completed":
        output_text = ""
        annotations = []
        
        if hasattr(response, 'output_text'):
            output_text = response.output_text
        elif hasattr(response, 'output'):
            for item in response.output:
                if hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'text'):
                            output_text += content.text
                        if hasattr(content, 'annotations'):
                            annotations.extend(content.annotations)
            
        result["output"] = output_text
        result["annotations"] = [str(a) for a in annotations]  # Serialize
        result["usage"] = response.usage.model_dump() if hasattr(response, 'usage') and response.usage else None
    
    return result


def prompt(name: str, variables: dict = None, model: str = "gpt-4.1", system: str = None, background: bool = False) -> dict:
    """
    Load a prompt template, interpolate variables, and run it.
    
    Args:
        name: Prompt file name (without .md extension)
        variables: Dict of variables to interpolate ({{var}} syntax)
        model: Model to use
        system: Optional system prompt override
        background: For deep research, return response_id instead of waiting
        
    Returns:
        dict with prompt_name, model, input, output, elapsed_seconds, usage
        (or response_id if background mode)
    """
    # Load prompt file
    prompt_path = PROMPTS_DIR / f"{name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    
    prompt_template = prompt_path.read_text()
    
    # Interpolate variables
    if variables:
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            # Convert dicts/lists to JSON string
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            prompt_template = prompt_template.replace(placeholder, str(value))
    
    # Execute
    start = time.time()
    
    # Route to appropriate function based on model
    is_deep_research = model in DEEP_RESEARCH_MODELS or model.startswith("o4-mini-deep") or model.startswith("o3-deep")
    
    if is_deep_research:
        result = research(prompt_template, model=model, background=background)
        if background:
            return {
                "prompt_name": name,
                "model": model,
                "response_id": result.get("response_id"),
                "status": result.get("status"),
            }
        output = result.get("output", "")
        usage = result.get("usage")
    else:
        output = ai(prompt_template, model=model, system=system)
        usage = None
    
    elapsed = time.time() - start
    
    return {
        "prompt_name": name,
        "model": model,
        "input": prompt_template,
        "output": output,
        "elapsed_seconds": round(elapsed, 2),
        "usage": usage,
    }


# Gemini support (optional)
try:
    import google.generativeai as genai
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

GEMINI_MODELS = {
    "gemini-2.5-pro": "gemini-2.5-pro-preview-06-05",
    "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20",
    "gemini-3-flash": "gemini-3.0-flash-preview",
}


def gemini(prompt: str, model: str = "gemini-2.5-flash", system: str = None) -> str:
    """Gemini completion."""
    if not GEMINI_AVAILABLE:
        raise ImportError("google-generativeai not installed")
    
    model_id = GEMINI_MODELS.get(model, model)
    gemini_model = genai.GenerativeModel(model_id, system_instruction=system)
    response = gemini_model.generate_content(prompt)
    return response.text
