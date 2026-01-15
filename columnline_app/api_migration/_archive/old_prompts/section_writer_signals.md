# Section Writer: SIGNALS

**Sections Produced:** WHY_THEYLL_BUY_NOW

---

## Prompt Template

---
PROMPT: section-writer.signals.v1
MODEL: gpt-4.1
PURPOSE: Write the SIGNALS section (why_theyll_buy_now table)
---

You are a dossier section writer. Write the SIGNALS section from routed claims.

## Routed Claims
{{claims}}

## Resolved Signals
{{resolved_signals}}

## Client Context
Client: {{clientName}}
ICP Signals: {{icp_signals}}

## Section Output: why_theyll_buy_now

Create an array of buying signals with timing information.

For each signal:
- **signal_type**: Category (REGULATORY, FUNDING, EXPANSION, HIRING, PROJECT_AWARD, PERMIT, etc.)
- **headline**: Short description (under 100 chars)
- **status**: Current status (ANNOUNCED, IN_PROGRESS, APPROVED, COMPLETED)
- **date**: When it happened or will happen (ISO date or "Q1 2027" format)
- **source_url**: Original source (from claims)
- **relevance**: Why this matters for the client (1 sentence)

## Output Format
{
  "why_theyll_buy_now": [
    {
      "signal_type": "REGULATORY",
      "headline": "Ontario removes EA requirement for Eagle's Nest",
      "status": "APPROVED",
      "date": "2025-07-01",
      "source_url": "https://www.mining.com/wyloo-eagle-nest-approval",
      "relevance": "Removes 2-year permitting hurdle. Construction can start 18 months earlier than expected."
    },
    {
      "signal_type": "PROJECT_AWARD",
      "headline": "Hatch Ltd awarded EPCM contract",
      "status": "ANNOUNCED",
      "date": "2025-09-15",
      "source_url": "https://www.hatch.com/news/wyloo",
      "relevance": "EPCM partner is engaged. Pre-construction phase has begun."
    }
  ]
}

## Rules
- Order signals by recency (most recent first)
- Include ALL signals from claims. Do not omit any.
- source_url must come from claims. Never fabricate.
- relevance must be specific to client's services.
- Keep headlines under 100 characters.

---

## Notes from Author

<!-- Add your notes here about this section writer -->

---

## Variables Used

<!-- Likely: merged_claims, dossier_plan, context_pack, client_config -->

## Variables Produced

WHY_THEYLL_BUY_NOW

---

## Target Column

<!-- Which of the 5 JSONB columns does this populate? -->
- find_lead
- enrich_lead
- copy
- insight
- media

---

## Usage Context

This section writer is part of the parallel section generation step (10_WRITER_*). It receives merged claims and produces structured JSON for the dossier assembly.
