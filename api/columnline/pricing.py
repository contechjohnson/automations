"""
Model Pricing Configuration

OpenAI API pricing per 1M tokens for cost calculation.
Update these values when OpenAI changes pricing.
"""

# OpenAI pricing per 1M tokens (as of Jan 2026)
# Source: https://openai.com/pricing
MODEL_PRICING = {
    # GPT-4.1 series
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.10, "output": 0.40},

    # GPT-5 series
    "gpt-5.2": {"input": 3.00, "output": 12.00},

    # O-series (reasoning models)
    "o4-mini": {"input": 1.10, "output": 4.40},
    "o4-mini-deep-research": {"input": 1.10, "output": 4.40},

    # Fallback for unknown models
    "default": {"input": 2.00, "output": 8.00},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost in USD for a single API call.

    Args:
        model: Model name from OpenAI response (e.g., "gpt-4.1")
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens

    Returns:
        Estimated cost in USD (rounded to 6 decimal places)
    """
    # Get pricing for model, fallback to default if unknown
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])

    # Calculate cost (pricing is per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return round(input_cost + output_cost, 6)


def get_model_pricing(model: str) -> dict:
    """
    Get pricing info for a model.

    Returns:
        Dict with 'input' and 'output' prices per 1M tokens
    """
    return MODEL_PRICING.get(model, MODEL_PRICING["default"])
