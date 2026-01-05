#!/usr/bin/env python3
"""
Test entity research prompt against different models.

Usage:
    python test_entity_research.py [model]
    
    # Quick test with GPT-4.1 (default)
    python test_entity_research.py
    
    # Test specific model
    python test_entity_research.py gpt-5.2
    python test_entity_research.py o4-mini-deep-research-2025-06-26
"""

import sys
import json
from datetime import datetime
from workers.ai import prompt

# Test data - New England Women's Healthcare
TEST_DATA = {
    "lead": {
        "company_name": "New England Womens Healthcare",
        "timing_urgency": "HIGH",
        "one_liner": "Expanded to 15+ providers and 3 locations following Wakefield office launch",
        "primary_signal": "practice_expansion",
        "the_angle": "NEWH has scaled to 10 OB/GYNs and 5 NPs but lacks an in-house dietitian to support their high patient volume. Their heavy use of NPs suggests a holistic mindset open to mid-level provider partnerships.",
        "lead_score": 89,
        "company_snapshot": {
            "description": "A physician-owned, independent OBGYN practice providing comprehensive prenatal, obstetrics, and gynecological care across three locations.",
            "domain": "newh-obgyn.com",
            "hq_city": "Woburn",
            "hq_state": "MA"
        },
        "primary_buying_signal": {
            "signal": "practice_expansion",
            "description": "New England Womens Healthcare has expanded to 10 OB/GYN physicians and 5 nurse practitioners across three locations (Woburn, Wilmington, and Wakefield) to meet growing patient demand as of January 2026.",
            "source_name": "ZipRecruiter / Tebra",
            "source_url": "https://www.ziprecruiter.com/c/New-England-Womens-Healthcare/Job/OB-GYN-Physician-Physician-owned-Private-Practice!-Job/-in-Woburn,MA?jid=7f8e9a1b"
        }
    },
    "clientName": "Kali Pearson",
    "clientServices": "One-on-one virtual nutrition coaching (100% telehealth), Gestational diabetes management, Fertility nutrition support, Postpartum nutrition and recovery, Weight loss (specialized, maternal health context), PCOS and hormonal health, Hashimotos thyroiditis support, Functional testing and root cause analysis, Physician follow-up notes after each patient visit",
    "personas": [
        {
            "title": "Office Manager / Practice Administrator",
            "seniority": "Manager to Director level",
            "note": "PRIMARY OUTREACH TARGET - 95% of successful partnerships start here, NOT physician directly"
        },
        {
            "title": "OB/GYN Physician (DO, MD, NP, PA)",
            "seniority": "C-level (practice owner or partner)",
            "note": "DECISION MAKER but reached through office manager. DOs and NPs refer more than MDs (holistic mindset)"
        }
    ]
}


def run_test(model: str = "gpt-4.1"):
    """Run entity research prompt with specified model."""
    
    print(f"\n{'='*60}")
    print(f"TESTING: find-lead.entity-research")
    print(f"MODEL: {model}")
    print(f"TIME: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    try:
        result = prompt(
            "find-lead.entity-research",
            variables=TEST_DATA,
            model=model,
        )
        
        print(f"✅ SUCCESS")
        print(f"Elapsed: {result['elapsed_seconds']}s")
        print(f"\n{'='*60}")
        print("OUTPUT:")
        print(f"{'='*60}\n")
        print(result['output'][:5000] if result['output'] else "No output")
        if result['output'] and len(result['output']) > 5000:
            print(f"\n... [truncated, total {len(result['output'])} chars]")
        
        # Save full result to file
        output_file = f"test_output_{model.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📁 Full output saved to: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "gpt-4.1"
    run_test(model)
