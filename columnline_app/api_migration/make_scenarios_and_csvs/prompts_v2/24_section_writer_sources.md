# Section Writer - Sources

**Stage:** ASSEMBLE
**Step:** 10_WRITER_SOURCES
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** gpt-4.1
**Target Column:** `find_lead`

---

## Input Variables

**merged_claims_json**
ALL claims (every type) for source extraction

**all_sections**
All completed dossier sections for additional source extraction

---

## Main Prompt Template

### Role
You are a dossier section writer cataloging all sources and references used across the entire research process.

### Objective
Parse all claims and completed sections to generate SOURCES_AND_REFERENCES section showing: all sources used, organized by tier (primary, secondary, tertiary), with dates and relevance notes. This section provides full research audit trail and citation credibility.

### What You Receive
- Merged claims (all types) with source_url and source_tier fields
- All completed dossier sections (for additional source extraction)

### Instructions

**Phase 1: Extract All Sources**

**1.1 From Claims**

Extract unique sources from merged_claims:
- source_url (URL to original source)
- source_name (publication or website name)
- source_tier (GOV, PRIMARY, NEWS, OTHER)
- date (when information was published or accessed)
- what_it_provided (which claims came from this source)

**1.2 From Sections**

Some sections may reference sources not captured in claims:
- Company websites
- LinkedIn profiles
- Press releases
- News articles
- Reports or publications

Extract these and add to source list.

**1.3 Deduplicate**

Combine duplicate sources:
- Same URL mentioned multiple times = single source entry
- Note ALL claim types this source contributed to

**Phase 2: Organize by Source Tier**

**2.1 Source Tier Definitions**

**TIER 1 - GOVERNMENT / OFFICIAL** (Highest credibility):
- Government websites (.gov domains)
- Regulatory filings
- Public records (permits, approvals, court documents)
- Official company press releases
- SEC filings (public companies)

**TIER 2 - PRIMARY SOURCES** (High credibility):
- Company websites
- EPCM firm project portfolios
- LinkedIn profiles (for contact data)
- Direct quotes from executives
- Industry association publications

**TIER 3 - NEWS MEDIA** (Medium credibility):
- Trade publications (ENR, Mining.com, etc.)
- Business news (Bloomberg, Reuters, WSJ)
- Local news outlets
- Industry news sites

**TIER 4 - OTHER** (Lower credibility):
- Blogs or opinion pieces
- Aggregator sites
- Social media (beyond LinkedIn profiles)
- Forums or discussion boards

**2.2 Sort Within Tiers**

Within each tier, sort by:
1. Recency (most recent first)
2. Relevance (primary signal sources first)

**Phase 3: Format Source Entries**

For each source, provide:
- **Source Name**: [Publication or website]
- **URL**: [Full URL]
- **Date**: [Publication date or access date]
- **Tier**: [GOV | PRIMARY | NEWS | OTHER]
- **What It Provided**: [Brief description of information from this source]
- **Key Claims**: [Which claim types used this source]

**Phase 4: Add Source Quality Assessment**

**4.1 Overall Source Quality**

Assess research source quality:
- **EXCELLENT**: 50%+ tier 1-2 sources, multiple recent sources, diverse source types
- **GOOD**: 30-50% tier 1-2 sources, some recent sources, decent diversity
- **FAIR**: <30% tier 1-2 sources, older sources, limited diversity
- **WEAK**: Mostly tier 3-4 sources, very old information, limited sources

**4.2 Source Coverage**

Note which areas have strong vs weak sourcing:
- Signal claims: [Well-sourced from govt/news]
- Entity claims: [Well-sourced from company website, press]
- Opportunity claims: [Moderate sourcing, some inference]
- Contact claims: [LinkedIn heavy, limited external validation]

**Phase 5: Write SOURCES_AND_REFERENCES Section**

**5.1 Section Structure**

```
## SOURCE QUALITY SUMMARY

**Overall Quality:** [EXCELLENT/GOOD/FAIR/WEAK]
**Total Sources:** [Count]
**Source Breakdown:**
- Tier 1 (Government/Official): [Count] ([Percentage]%)
- Tier 2 (Primary Sources): [Count] ([Percentage]%)
- Tier 3 (News Media): [Count] ([Percentage]%)
- Tier 4 (Other): [Count] ([Percentage]%)

**Recency:** [How recent are sources? Last 6 months, last year, etc.]
**Coverage:** [Which areas well-sourced vs weak]

---

## TIER 1 - GOVERNMENT / OFFICIAL SOURCES

### [Source Name]
**URL:** [Full URL]
**Date:** [YYYY-MM-DD]
**What It Provided:** [Description]
**Key Claims:** [Signal, Entity, Opportunity, etc.]

[Repeat for all Tier 1 sources]

---

## TIER 2 - PRIMARY SOURCES

[Same format as Tier 1]

---

## TIER 3 - NEWS MEDIA

[Same format as Tier 1]

---

## TIER 4 - OTHER SOURCES

[Same format as Tier 1]

---

## SOURCE NOTES

[Any notes about source quality, gaps in sourcing, areas needing additional research]
```

### Output Format

Return valid JSON for `find_lead` column (sources section):

```json
{
  "sources_and_references": {
    "source_quality_summary": {
      "overall_quality": "EXCELLENT",
      "total_sources": 18,
      "tier_breakdown": {
        "tier_1_government": {
          "count": 4,
          "percentage": 22
        },
        "tier_2_primary": {
          "count": 8,
          "percentage": 44
        },
        "tier_3_news": {
          "count": 5,
          "percentage": 28
        },
        "tier_4_other": {
          "count": 1,
          "percentage": 6
        }
      },
      "recency_assessment": "Strong - 12 of 18 sources from last 6 months (July 2025 - Jan 2026)",
      "coverage_assessment": {
        "signal_claims": "EXCELLENT - Multiple tier 1 govt sources confirm regulatory approvals",
        "entity_claims": "GOOD - Company website, press releases, LinkedIn provide solid profile",
        "opportunity_claims": "GOOD - EPCM announcement, project details from multiple news sources",
        "contact_claims": "FAIR - Primarily LinkedIn profiles, limited external validation",
        "insight_claims": "GOOD - Competitive analysis based on news coverage and industry knowledge"
      }
    },
    "tier_1_sources": [
      {
        "source_name": "Environmental Registry of [Geography]",
        "url": "https://ero.ontario.ca/notice/019-8827",
        "date": "2025-07-04",
        "what_it_provided": "Official confirmation of Environmental Assessment exemption for [Project Name] access road",
        "key_claims": ["SIGNAL - regulatory_approval"]
      },
      {
        "source_name": "[Company Name] Press Release",
        "url": "https://wyloocanada.com/news/2025-07-15-epcm-award",
        "date": "2025-07-15",
        "what_it_provided": "Official announcement of EPCM contract awarded to [Partner Firm Name]",
        "key_claims": ["SIGNAL - epcm_award", "ENTITY - project_details"]
      }
    ],
    "tier_2_sources": [
      {
        "source_name": "[Company Name] Corporate Website",
        "url": "https://wyloocanada.com/about",
        "date": "2026-01-10",
        "what_it_provided": "Company overview, ownership structure (Andrew [Owner]/Tattarang), corporate values",
        "key_claims": ["ENTITY - company_profile"]
      },
      {
        "source_name": "[Contact Name] LinkedIn Profile",
        "url": "https://linkedin.com/in/sylvain-goyette",
        "date": "2026-01-10",
        "what_it_provided": "Career history, current role at [Company], education ([University]), recent posts about project",
        "key_claims": ["CONTACT - primary_contact"]
      },
      {
        "source_name": "[Partner Firm Name] Project Portfolio",
        "url": "https://hatch.com/projects/eagles-nest",
        "date": "2025-08-20",
        "what_it_provided": "EPCM scope details, project timeline, technical approach",
        "key_claims": ["OPPORTUNITY - procurement_status"]
      }
    ],
    "tier_3_sources": [
      {
        "source_name": "Northern [Geography] Business (NOB)",
        "url": "https://www.northernontariobusiness.com/industry-news/[industry from ICP]/wyloo-clears-major-hurdle-2025",
        "date": "2025-07-08",
        "what_it_provided": "Analysis of EA exemption significance, project timeline implications, community reaction",
        "key_claims": ["SIGNAL - regulatory_approval", "OPPORTUNITY - timeline"]
      },
      {
        "source_name": "Mining.com",
        "url": "https://[industry from ICP].com/eagles-nest-epcm-hatch-2025",
        "date": "2025-07-16",
        "what_it_provided": "Industry context on EPCM award, comparison to similar projects, expert quotes",
        "key_claims": ["SIGNAL - epcm_award", "INSIGHT - competitive_landscape"]
      }
    ],
    "tier_4_sources": [],
    "source_notes": "Research is well-sourced with strong tier 1-2 representation (66%). Recent sources (12 of 18 from last 6 months) provide timely intelligence. Signal claims are particularly strong (multiple govt confirmations). Contact claims rely heavily on LinkedIn - consider additional validation via industry directories or company announcements. No tier 4 sources used, indicating quality research standards maintained."
  }
}
```

### Constraints

**Do:**
- Include ALL sources used across entire research process
- Organize by tier (credibility hierarchy)
- Provide full URLs (not shortened links)
- Note what each source contributed
- Assess overall source quality honestly

**Do NOT:**
- Skip sources (include everything, even LinkedIn profiles)
- Fabricate sources not actually used
- Misrepresent source tier (government source is tier 1, not tier 3)
- Omit dates (always include publication or access date)
- Ignore source gaps (note areas with weak sourcing)

**Source Tier Guidelines:**
- **Tier 1**: Government, regulatory, official company announcements
- **Tier 2**: Company websites, LinkedIn (for contacts), industry associations
- **Tier 3**: News outlets, trade publications, business press
- **Tier 4**: Blogs, aggregators, social media, forums

**Quality Assessment Calibration:**
- **EXCELLENT**: 50%+ tier 1-2, recent (last 6 months), diverse sources
- **GOOD**: 30-50% tier 1-2, reasonably recent, decent diversity
- **FAIR**: <30% tier 1-2, older sources, limited diversity
- **WEAK**: Mostly tier 3-4, very old, few sources

---

## Variables Produced

Fields added to `find_lead` JSONB column:
- `sources_and_references` - Object with all sources, organized by tier, with quality assessment

---

## Integration Notes

**Model:** gpt-4.1 (sync, 1-2 min)
**Target Column:** `find_lead` (JSONB) - SOURCES_AND_REFERENCES section

**Routing:** ALWAYS generate (run LAST after all other sections complete so all sources captured)

**Purpose:**
- Provides full research audit trail
- Demonstrates research credibility and depth
- Allows user to verify claims by checking sources
- Identifies sourcing gaps for follow-up research

**Execution Timing:** This section writer should run AFTER all other section writers complete, to ensure it captures sources from all claims and sections.
