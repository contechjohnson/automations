# Compress Batch Strategy

**Stage:** SETUP
**Step:** 00B_COMPRESS_BATCH_STRATEGY
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** gpt-4.1

---

## Input Variables

**batch_strategy**
Full (thorough) batch strategy from Onboarding step

---

## Main Prompt Template

### Role
You are a configuration compression specialist optimizing batch strategy for token efficiency while preserving distribution rules and seed generation guidance.

### Objective
Compress thorough batch strategy into machine-readable format that reduces token usage by 30-50% while maintaining distribution targets, focus areas, and seed generation rules. Note: Batch strategy is used LESS frequently than other configs (only for batch composer), so compression is less aggressive.

### What You Receive
- Full batch strategy with distribution percentages, focus area explanations, seed generation guidance

### Instructions

**Phase 1: Identify Core Elements**

**1.1 What to Preserve**
- Distribution percentages by project type or geography
- Seed count targets (how many dossiers per batch)
- Focus areas (project types, geographies to prioritize)
- Seed source preference (discovery mode vs seed pool)
- Duplicate avoidance rules
- Quality thresholds (minimum ICP scores)

**1.2 What to Compress**
- Rationale explanations → just the rule
- Example distributions → single clear statement
- Strategy background → essentials only

**1.3 What to Remove**
- Client feedback history (unless actively incorporated)
- Strategic planning discussions
- Internal notes about why distribution chosen

**Phase 2: Compression Strategies**

**2.1 Distribution Compression**

**Original:**
```
Distribution Strategy:
Based on client's current pipeline needs and market opportunity analysis, we recommend the following distribution for batch dossier generation:

- 70% Data Centers: This remains our primary focus given client's strongest capabilities and highest-margin work. Within [project type from ICP]s, prioritize hyperscale (100MW+) over enterprise, and focus on [Geography from ICP], [Geography from ICP], and [Geography] markets where client has established presence.

- 10% Senior Housing: Secondary focus area where client is building capabilities. Focus on assisted living and memory care facilities in the $30M-$80M range. Prioritize [Geography] and [geography from ICP] where client has local relationships.

- 10% Logistics: Emerging opportunity driven by e-commerce growth. Focus on warehouses and fulfillment centers $50M+. Prioritize [Geography from ICP] and Georgia where client has recent project wins.

- 10% Multi-Family: Opportunistic pursuits in client's home markets. Focus on 150+ unit projects in [Location] and Dallas metro areas.

This distribution reflects client's strategic growth plan: maintain [project type from ICP] dominance (70%), grow adjacent markets ([project type from ICP], [industry] at 10% each), and selective multi-family opportunistically (10%).
```

**Compressed:**
```
Distribution: Data centers 70% (hyperscale, VA/TX/CA), Senior housing 10% (assisted living/memory care $30M-$80M, CA/AZ), Logistics 10% (warehouses/fulfillment $50M+, TX/GA), Multi-family 10% (150+ units, [Location]/Dallas).
Rationale: Maintain [project type from ICP] dominance, grow adjacent markets, selective multi-family.
```

**2.2 Seed Generation Rules Compression**

**Original:**
```
Seed Generation Approach:
Use Discovery Mode (web research) as primary seed source until we build up a sufficient seed pool. For each batch:

1. Count: Generate 5-10 seeds per batch (start with 5 for MVP, scale to 10 as pipeline matures)

2. Quality Threshold: All seeds must score 60+ on ICP (70+ preferred). Better to generate 7 strong seeds than 10 weak ones.

3. Duplicate Avoidance: Check last 3 batches (30 dossiers) to avoid duplicates. If company already researched in last 90 days, skip.

4. Geographic Diversity: Within each project type bucket, ensure geographic diversity (not all [project type from ICP]s in [Geography from ICP] - spread across VA, TX, CA).

5. Signal Diversity: Mix signal types (EPCM awards, permits, groundbreakings) to avoid over-indexing on one signal type.

6. Feedback Integration: After each batch delivery, incorporate client feedback for next batch. If client says "more [Geography from ICP]" or "higher scores only", adjust next batch accordingly.
```

**Compressed:**
```
Seed generation: Discovery mode, 5-10 per batch, 60+ ICP score (70+ preferred). Avoid duplicates (check last 3 batches/90 days). Ensure geographic + signal diversity. Integrate feedback batch-to-batch.
```

**2.3 Focus Areas Compression**

**Original:**
```
Priority Focus Areas (Beyond Distribution):

For Data Centers:
- Northern [Geography from ICP] [project type from ICP] corridor ([Location]) - highest priority due to power availability and client track record
- [Location] metro (West Valley) - home market advantage, strong relationships
- [Geography from ICP] Triangle (Dallas, Austin, San Antonio) - growing market, power-friendly regulations

For Senior Housing:
- Orange County, CA - aging demographics, high property values, client local presence
- [Location] metro - home market, existing [project type from ICP] relationships
- San Diego - growth market, demographic trends favorable

Avoid: Edge [project type from ICP]s (too small), government [project type from ICP]s (excluded), international (out of scope)
```

**Compressed:**
```
Data centers: VA ([Location]) highest priority, [Location] (West Valley), TX Triangle. Avoid: edge, gov't, international.
Senior housing: Orange County CA, [Location], San Diego. Avoid: <50 beds, rural.
Logistics: TX/GA priority. Avoid: <200K sf, cold storage (not client expertise).
Multi-family: [Location]/Dallas only. Avoid: <100 units, affordable housing (different procurement).
```

**Phase 3: Validate Compression**

**3.1 Quality Checks**
- Are distribution percentages clear?
- Are quality thresholds unambiguous?
- Are focus areas specific enough for seed generation?
- Can batch composer follow these rules?

**3.2 Token Reduction Target**
- Original: ~1,500-2,000 tokens
- Compressed: ~700-1,000 tokens (30-50% reduction)
- Note: Less aggressive than other compressions (batch strategy used less frequently)

### Output Format

Return valid JSON with compressed batch strategy:

```json
{
  "distribution": {
    "data_centers": {
      "percentage": 70,
      "subtypes": ["hyperscale", "enterprise", "colocation"],
      "avoid": ["edge", "government"],
      "geographies_priority": ["VA-Loudoun", "[Location]-West", "TX-Triangle"],
      "size_range": "$50M-$500M"
    },
    "senior_housing": {
      "percentage": 10,
      "subtypes": ["assisted_living", "memory_care"],
      "avoid": ["independent_living", "rural"],
      "geographies_priority": ["Orange-County-CA", "[Location]", "San-Diego"],
      "size_range": "$30M-$80M"
    },
    "[industry]": {
      "percentage": 10,
      "subtypes": ["warehouses", "fulfillment_centers"],
      "avoid": ["cold_storage", "small_format"],
      "geographies_priority": ["TX", "GA"],
      "size_range": "$50M+"
    },
    "multi_family": {
      "percentage": 10,
      "subtypes": ["urban_infill", "mixed_use"],
      "avoid": ["affordable_housing", "single_family"],
      "geographies_priority": ["[Location]", "Dallas"],
      "size_range": "150+ units"
    }
  },
  "seed_generation_rules": {
    "count_per_batch": {"min": 5, "max": 10, "start_with": 5},
    "quality_threshold": {"minimum": 60, "preferred": 70},
    "source": "discovery_mode",
    "duplicate_avoidance": {"check_last_batches": 3, "days_lookback": 90},
    "diversity_requirements": {
      "geographic": "Spread across multiple states within project type",
      "signal": "Mix signal types (EPCM, permits, groundbreakings)"
    },
    "feedback_integration": "Adjust distribution or focus based on client feedback from previous batch"
  },
  "focus_areas": {
    "highest_priority": ["VA-Loudoun-data-centers", "[Location]-home-market"],
    "growth_areas": ["TX-data-centers", "Orange-County-senior-housing", "GA-[industry]"],
    "opportunistic": ["[Location]-multi-family", "Dallas-multi-family"]
  },
  "avoid_categories": {
    "project_types": ["edge_data_centers", "government", "affordable_housing", "cold_storage"],
    "geographies": ["international", "rural"],
    "sizes": ["<$10M", ">$1B"]
  },
  "compression_metadata": {
    "original_tokens": 1800,
    "compressed_tokens": 850,
    "reduction_percentage": 53,
    "compressed_at": "2026-01-12T10:15:00Z"
  }
}
```

### Constraints

**Do:**
- Preserve exact distribution percentages
- Keep quality thresholds clear
- Maintain focus area specificity (not vague "[project type from ICP]s" but "VA [Location]")
- Include avoid categories (prevents wasted seeds)
- Keep feedback integration rule

**Do NOT:**
- Change distribution percentages
- Remove quality thresholds
- Lose geographic specificity
- Drop avoid categories (these prevent errors)
- Over-compress seed generation rules

**Compression Targets:**
- Distribution: 40% reduction (keep percentages, subtypes, geographies, avoid)
- Seed rules: 50% reduction (keep count, threshold, diversity, feedback)
- Focus areas: 60% reduction (keep specific locations and priorities)

**Quality Validation:**
Can batch composer generate seeds matching distribution targets and focus areas?
If yes → compression successful.

---

## Variables Produced

- `batch_strategy_compressed` - Compressed batch strategy (30-50% smaller)
- `reduction_percentage` - Token savings achieved

---

## Integration Notes

**Model:** gpt-4.1 (sync, < 1 min)

**Purpose:** Moderate token optimization. Batch strategy used less frequently (only in batch composer), so less aggressive compression than ICP/industry/context.

**Next Steps:**
- Compressed version used in batch composer (00C_BATCH_COMPOSER)
- Original thorough version available for client review and adjustments
- Saves 800-1,200 tokens per batch composer run
