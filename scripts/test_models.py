#!/usr/bin/env python3
"""
Model Swap Test Script
======================
Test the same prompt across different models and compare results.

Usage:
    python3 scripts/test_models.py
    python3 scripts/test_models.py --question "What is a data center?"
    python3 scripts/test_models.py --models gpt-4.1 gpt-4.1-mini
"""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
from dotenv import load_dotenv
load_dotenv()

from workers.ai import prompt

# Default models to test
DEFAULT_MODELS = ["gpt-4.1", "gpt-4.1-mini"]

# Default test question
DEFAULT_QUESTION = "What are the key factors when evaluating a commercial construction lead for B2B sales?"


def test_model(model: str, question: str) -> dict:
    """Run a single model test."""
    print(f"\n{'='*60}")
    print(f"Testing: {model}")
    print(f"{'='*60}")

    result = prompt(
        "model-test",
        variables={"question": question},
        model=model,
        log=True,
        tags=["model-test", model]
    )

    print(f"\nTime: {result['elapsed_seconds']}s")
    print(f"\nOutput:\n{result['output'][:500]}...")

    return result


def main():
    parser = argparse.ArgumentParser(description="Test prompts across different models")
    parser.add_argument("--question", "-q", default=DEFAULT_QUESTION, help="Question to ask")
    parser.add_argument("--models", "-m", nargs="+", default=DEFAULT_MODELS, help="Models to test")
    parser.add_argument("--prompt", "-p", default="model-test", help="Prompt file name (without .md)")

    args = parser.parse_args()

    print(f"Question: {args.question}")
    print(f"Models: {args.models}")
    print(f"Prompt: {args.prompt}")

    results = []
    for model in args.models:
        try:
            result = test_model(model, args.question)
            results.append({
                "model": model,
                "time": result["elapsed_seconds"],
                "output_length": len(result["output"]),
                "status": "success"
            })
        except Exception as e:
            print(f"\nError with {model}: {e}")
            results.append({
                "model": model,
                "status": "failed",
                "error": str(e)
            })

    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Model':<20} {'Time (s)':<12} {'Output Len':<12} {'Status':<10}")
    print("-" * 60)
    for r in results:
        if r["status"] == "success":
            print(f"{r['model']:<20} {r['time']:<12.2f} {r['output_length']:<12} {r['status']:<10}")
        else:
            print(f"{r['model']:<20} {'N/A':<12} {'N/A':<12} {r['status']:<10}")

    print(f"\nResults logged to Supabase execution_logs table.")
    print("Query with: SELECT * FROM execution_logs WHERE 'model-test' = ANY(tags) ORDER BY started_at DESC;")


if __name__ == "__main__":
    main()
