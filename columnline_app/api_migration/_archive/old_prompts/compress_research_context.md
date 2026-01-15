# Config Compression: RESEARCH_CONTEXT

**Purpose:** Compress thorough RESEARCH_CONTEXT into token-efficient version for most pipeline steps

---

## Prompt Template

RESEARCH_CONTEXT Preprocessor

Extract client context for personalized outreach:

1. CLIENT: company_name, domain, tagline, headquarters
2. DIFFERENTIATORS: List key differentiators (max 7)
3. NOTABLE_PROJECTS: List with name and significance
4. TEAM: List key people with name, title, role
5. COMPETITORS: List with name and our_advantage
6. GOALS: Extract target_outcomes and pain_points
7. BRAND_VOICE: tone, key_phrases, avoid

Output as JSON:
{
  "client": {"name": "", "domain": "", "tagline": "", "hq": ""},
  "differentiators": [],
  "notable_projects": [{"name": "", "significance": ""}],
  "team": [{"name": "", "title": "", "role": ""}],
  "competitors": [{"name": "", "advantage": ""}],
  "goals": {"outcomes": [], "pain_points": []},
  "brand_voice": {"tone": "", "phrases": [], "avoid": []}
}

---

## Notes from Author

<!-- This compresses the comprehensive config into a machine-readable format -->

---

## Variables Used

- `research_context` (thorough version from Onboarding)

## Variables Produced

- `research_context_compressed` (compact version)

---

## Usage Context

Part of _0B_PREP_INPUTS phase. Takes thorough configs from onboarding and creates compressed versions for cost savings. Most pipeline steps use compressed; high-impact steps (batch composer, feedback) use thorough.

**Token Savings:** Typically 40-60% reduction while maintaining essential context.
