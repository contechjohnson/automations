"""
Test script for v2 pipeline

Run with: python -m columnline_app.v2.test_pipeline
"""
import os
import sys
import asyncio
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from columnline_app.v2.db.repository import V2Repository
from columnline_app.v2.db.models import PipelineRun, PipelineStatus
from columnline_app.v2.pipeline.runner import PipelineRunner
from columnline_app.v2.pipeline.step_executor import StepExecutor, load_prompt_content, interpolate_prompt
from columnline_app.v2.pipeline.state import PipelineState
from columnline_app.v2.config import PIPELINE_STEPS


def test_database_connection():
    """Test database connection and data"""
    print("\n=== Testing Database Connection ===")
    repo = V2Repository()

    # Test clients
    clients = repo.get_clients()
    print(f"✅ Found {len(clients)} clients")
    for c in clients:
        print(f"   - {c.slug}: {c.name}")

    # Test prompts
    prompts = repo.get_prompts()
    print(f"✅ Found {len(prompts)} prompts")

    # Test prompt versions
    versions = repo.get_prompt_versions("1-search-builder")
    print(f"✅ Found {len(versions)} versions for 1-search-builder")

    return True


def test_prompt_loading():
    """Test prompt file loading and interpolation"""
    print("\n=== Testing Prompt Loading ===")

    # Load search builder prompt
    content = load_prompt_content("1-search-builder")
    print(f"✅ Loaded 1-search-builder.md ({len(content)} chars)")

    # Test interpolation
    variables = {
        "current_date": "2026-01-11",
        "icp_config": {"signals": [{"name": "test", "weight": 10}]},
        "research_context": {"client": {"name": "Test Corp"}},
        "industry_research": {"industries": ["Data Centers"]},
        "hint": "Test signal for data center in Virginia",
    }

    interpolated = interpolate_prompt(content, variables)
    print(f"✅ Interpolated prompt ({len(interpolated)} chars)")
    print(f"   First 200 chars: {interpolated[:200]}...")

    return True


async def test_single_step():
    """Test running a single step"""
    print("\n=== Testing Single Step Execution ===")
    repo = V2Repository()

    # Get test client
    client = repo.get_client_by_slug("span-construction")
    if not client:
        print("❌ Test client not found")
        return False

    print(f"✅ Using client: {client.name}")

    # Create test pipeline run
    pipeline_run = repo.create_pipeline_run(PipelineRun(
        client_id=client.id,
        seed={"company_name": "Microsoft Azure", "hint": "data center in Virginia"},
        status=PipelineStatus.RUNNING,
        config={"test_mode": True},
        started_at=datetime.utcnow(),
    ))
    print(f"✅ Created pipeline run: {pipeline_run.id}")

    # Build state
    state = PipelineState(
        pipeline_run_id=pipeline_run.id,
        client=client,
        seed={"company_name": "Microsoft Azure", "hint": "data center in Virginia"},
    )

    # Execute first step
    executor = StepExecutor(repo)
    step_config = PIPELINE_STEPS["1-search-builder"]

    print(f"   Running step: {step_config.name}")
    print(f"   Model: {step_config.model}")
    print(f"   Mode: {step_config.execution_mode.value}")

    try:
        step_run, output, claims = await executor.execute_step(step_config, state)
        print(f"✅ Step completed!")
        print(f"   Status: {step_run.status}")
        print(f"   Duration: {step_run.duration_ms}ms")
        print(f"   Tokens: {step_run.tokens_in} in / {step_run.tokens_out} out")

        if output:
            print(f"   Output keys: {list(output.keys()) if isinstance(output, dict) else 'not a dict'}")
            # Save output to file
            output_file = f"tmp/test_step_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("tmp", exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(output, f, indent=2, default=str)
            print(f"   Output saved to: {output_file}")

        return True

    except Exception as e:
        print(f"❌ Step failed: {e}")
        import traceback
        traceback.print_exc()

        # Mark run as failed
        repo.update_pipeline_run(pipeline_run.id, {
            "status": PipelineStatus.FAILED.value,
            "error_message": str(e),
        })
        return False


async def test_full_pipeline():
    """Test running full pipeline (first 2 steps only for speed)"""
    print("\n=== Testing Full Pipeline (limited) ===")
    print("NOTE: This will make API calls and may take several minutes")

    repo = V2Repository()
    runner = PipelineRunner(repo)

    client = repo.get_client_by_slug("span-construction")
    if not client:
        print("❌ Test client not found")
        return False

    seed = {
        "company_name": "Equinix",
        "hint": "Equinix data center expansion Virginia Loudoun County 2026",
    }

    print(f"✅ Starting pipeline for: {seed['hint']}")
    print("   This may take 5-10 minutes for deep research steps...")

    try:
        result = await runner.run_pipeline(
            client_id=client.id,
            seed=seed,
            config={"test_mode": True}
        )

        print(f"✅ Pipeline completed!")
        print(f"   Status: {result.status}")
        print(f"   Steps completed: {result.steps_completed}")

        return True

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Columnline v2 Pipeline Test Suite")
    print("=" * 60)

    # Run tests
    results = {}

    # Test 1: Database connection
    results["database"] = test_database_connection()

    # Test 2: Prompt loading
    results["prompts"] = test_prompt_loading()

    # Test 3: Single step (requires API key)
    if os.environ.get("OPENAI_API_KEY"):
        results["single_step"] = asyncio.run(test_single_step())
    else:
        print("\n⚠️ Skipping single step test (OPENAI_API_KEY not set)")
        results["single_step"] = None

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        if passed is None:
            status = "⚠️ SKIPPED"
        elif passed:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"  {test_name}: {status}")

    # Full pipeline test (optional, long running)
    run_full = os.environ.get("RUN_FULL_PIPELINE_TEST", "").lower() == "true"
    if run_full:
        results["full_pipeline"] = asyncio.run(test_full_pipeline())
    else:
        print("\n💡 To run full pipeline test, set RUN_FULL_PIPELINE_TEST=true")


if __name__ == "__main__":
    main()
