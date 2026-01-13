# 08_MEDIA

**Source file:** `08_MEDIA.blueprint.json`
**Total modules:** 5
**Execution mode:** Async (called via START_ASYNC_AGENT_ENRICH_MEDIA)

## Purpose

Media and news enrichment - finds recent press coverage, news articles, and media mentions about the target company. The simplest of the enrichment blueprints.

## Module Flow

```
1. StartSubscenario (entry point)
   ↓
2. getCell: MEDIA_PROMPT (Prompts!C13)
3. getCell: MEDIA_LIVE_INPUT (Prompts!D13)
   ↓
4. createModelResponse: MEDIA
   → Model: gpt-4.1 with web_search
   → Searches for recent news and media
   ↓
5. updateCell: MEDIA_LIVE_OUTPUT (Prompts!E13)
```

## LLM Calls (1)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 4 | MEDIA | gpt-4.1 + web_search | Find news and media |

## Sheets Operations (3)

| Cell | Operation | Purpose |
|------|-----------|---------|
| Prompts!C13 | getCell | MEDIA_PROMPT |
| Prompts!D13 | getCell | MEDIA_LIVE_INPUT |
| Prompts!E13 | updateCell | MEDIA_LIVE_OUTPUT |

## Notable Differences

**This is the simplest enrichment blueprint:**
- Only 5 modules (vs 14 for others)
- No polling loop (sync call despite async launch)
- No PRODUCE_CLAIMS step
- No deep research model

## Why No Claims?

The media step doesn't produce claims because:
1. News articles are already atomic facts
2. URLs are preserved directly
3. Output goes directly to the SIGNALS writer
4. No deduplication needed (unique articles)

## Output Format

```json
{
  "media_coverage": [
    {
      "headline": "Acme Corp Announces Major Partnership",
      "source": "TechCrunch",
      "url": "https://...",
      "date": "2025-01-05",
      "summary": "...",
      "relevance": "high"
    }
  ],
  "press_releases": [...],
  "industry_mentions": [...],
  "social_media_signals": [...]
}
```

## Parallel Execution Context

Part of "Parallel Batch 1":

```
START_ASYNC_DEEP_ENRICH_LEAD ────────┐
START_ASYNC_AGENT_ENRICH_MEDIA ──────┤ (this - lightest)
START_ASYNC_AGENT_ENRICH_OPPORTUNITY ┤
START_ASYNC_AGENT_CLIENT_SPECIFIC ───┘
```

## Migration Notes

1. **Simplest to migrate** - Just one LLM call
2. **No claims system** - Skip claims extraction
3. **Quick execution** - Usually completes first in batch
4. **Direct to writers** - Output feeds WRITER_SIGNALS
5. **web_search tool** - Uses native GPT web search, not deep research
