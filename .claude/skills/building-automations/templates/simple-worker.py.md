# Simple Worker Template

Copy and adapt for basic LLM-powered automations.

```python
"""
{Worker Name}
=============
{Brief description of what this worker does.}

Usage:
    from workers.{category}.{name} import run

    result = run({"field": "value"})
"""

from workers.ai import prompt


def run(input_data: dict) -> dict:
    """
    {Description of the function.}

    Args:
        input_data: Dict with fields:
            - field1: Description
            - field2: Description

    Returns:
        Dict with output fields
    """
    # Validate input
    required = ["field1"]
    for field in required:
        if field not in input_data:
            raise ValueError(f"Missing required field: {field}")

    # Run prompt with MANDATORY logging
    result = prompt(
        "{prompt-name}",           # prompts/{prompt-name}.md
        variables={
            "field1": input_data["field1"],
            "field2": input_data.get("field2", "default"),
        },
        model="gpt-4.1",           # From directive's AI Configuration
        log=True,                  # ALWAYS true
        tags=["{automation-slug}", "gpt-4.1"]
    )

    return {
        "status": "success",
        "output": result.get("output"),
        "model": result.get("model"),
        "elapsed_seconds": result.get("elapsed_seconds")
    }
```

## Prompt File

Create `prompts/{prompt-name}.md`:

```markdown
# {Prompt Title}

{Context and instructions}

## Input

{{field1}}

{{field2}}

## Task

{What the LLM should do}

## Output Format

{Expected output structure}
```
