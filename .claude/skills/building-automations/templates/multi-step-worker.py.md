# Multi-Step Worker Template

For complex workflows with multiple phases and detailed logging.

```python
"""
{Worker Name}
=============
{Brief description of multi-step workflow.}

Usage:
    from workers.{category}.{name} import run

    result = run(config={"key": "value"}, geography={"state": "VA"}, job=None)
"""

from workers.logger import ExecutionLogger
from workers.ai import prompt


def run(config: dict, geography: dict = None, job=None) -> dict:
    """
    Multi-step worker with progress tracking.

    Args:
        config: Automation configuration
        geography: Optional geography context
        job: RQ job object for progress updates

    Returns:
        Dict with results
    """
    # Initialize logger with MANDATORY fields
    log = ExecutionLogger(
        worker_name="{category}.{name}",
        automation_slug=config.get("slug", "{default-slug}"),
        input_data={"config": config, "geography": geography},
        tags=[
            config.get("slug", "{default-slug}"),
            "{category}",
            geography.get("state", "unknown") if geography else "global"
        ]
    )

    def update_progress(message: str, percent: int):
        """Update both RQ job and log metadata."""
        if job:
            job.meta = {"message": message, "percent": percent}
            job.save_meta()
        log.meta("progress", {"message": message, "percent": percent})

    try:
        # ============================================================
        # STEP 1: {Step Name}
        # ============================================================
        update_progress("Step 1: {Step Name}", 10)
        log.meta("step", "step_1")

        step1_result = do_step_1(config)

        # Gate: {Validation criteria}
        if not step1_result:
            raise ValueError("Step 1 failed: {criteria not met}")

        # ============================================================
        # STEP 2: {Step Name}
        # ============================================================
        update_progress("Step 2: {Step Name}", 40)
        log.meta("step", "step_2")

        step2_result = do_step_2(step1_result)

        # ============================================================
        # STEP 3: {Optional LLM Enhancement}
        # ============================================================
        if config.get("enhance", False):
            update_progress("Step 3: Enhancing with LLM", 70)
            log.meta("step", "enhancement")

            enhanced = prompt(
                "{slug}.enhance",
                variables={"data": step2_result},
                model="gpt-4.1-mini",
                log=True,  # Individual LLM call also logs
                tags=[config.get("slug"), "enhancement"]
            )
            step2_result = enhanced.get("output")

        # ============================================================
        # COMPLETE
        # ============================================================
        update_progress("Complete", 100)

        return log.success({
            "status": "success",
            "records": step2_result,
            "count": len(step2_result) if isinstance(step2_result, list) else 1
        })

    except Exception as e:
        log.fail(e)  # Logs error and re-raises


def do_step_1(config: dict):
    """Placeholder for step 1 logic."""
    pass


def do_step_2(data):
    """Placeholder for step 2 logic."""
    pass
```

## Key Points

1. **ExecutionLogger** - Use for multi-step workflows
2. **update_progress** - Updates both RQ job meta and log metadata
3. **log.meta("step", ...)** - Track current step for debugging
4. **log.success()** - Returns the result AND logs completion
5. **log.fail()** - Logs error AND re-raises exception
6. **Nested prompt() with log=True** - Individual LLM calls also log
