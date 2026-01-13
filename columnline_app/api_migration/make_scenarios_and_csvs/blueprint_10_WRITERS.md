# WRITER Blueprints (6 files)

All 6 writer blueprints share **identical structure** - they only differ in:
1. Which sheet cell they read from
2. Which section they write

**Source files:**
- `WRITER_INTRO.blueprint.json`
- `WRITER_SIGNALS.blueprint.json`
- `WRITER_LEAD_INTELLIGENCE.blueprint.json`
- `WRITER_STRATEGY.blueprint.json`
- `WRITER_OPPORTUNITY_DETAILS.blueprint.json`
- `WRITER_CLIENT_SPECIFIC.blueprint.json`

**Total modules each:** 6
**Execution mode:** Async (called in parallel from 09_DOSSIER_PLAN)

---

## Common Module Flow

All 6 writers follow this exact pattern:

```
1. StartSubscenario (entry point, receives context pack)
   ↓
2. getCell: DOSSIER_SECTION_{X}_INPUT (DOSSIER SECTIONS!D{row})
   → Gets section-specific input data
   ↓
3. getCell: DOSSIER_SECTION_{X}_PROMPT (DOSSIER SECTIONS!C{row})
   → Gets section-specific prompt
   ↓
4. createModelResponse: SECTION_{X}_WRITER
   → Model: gpt-4.1
   → Generates section content
   ↓
5. updateCell: {X}_WRITER_OUTPUT (DOSSIER SECTIONS!E{row})
   → Writes generated content
   ↓
6. updateCell: APPEND_SOURCES (DOSSIER SECTIONS!F{row})
   → Writes source citations
```

---

## Writer-Specific Details

### WRITER_INTRO
| Sheet Row | 2 |
|-----------|---|
| Input Cell | DOSSIER SECTIONS!D2 |
| Prompt Cell | DOSSIER SECTIONS!C2 |
| Output Cell | DOSSIER SECTIONS!E2 |
| Sources Cell | DOSSIER SECTIONS!F2 |
| **Content Focus** | Executive summary, key opportunity, why-now |

### WRITER_SIGNALS
| Sheet Row | 3 |
|-----------|---|
| Input Cell | DOSSIER SECTIONS!D3 |
| Prompt Cell | DOSSIER SECTIONS!C3 |
| Output Cell | DOSSIER SECTIONS!E3 |
| Sources Cell | DOSSIER SECTIONS!F3 |
| **Content Focus** | Buying signals, news, triggers, timing |

### WRITER_LEAD_INTELLIGENCE
| Sheet Row | 5 |
|-----------|---|
| Input Cell | DOSSIER SECTIONS!D5 |
| Prompt Cell | DOSSIER SECTIONS!C5 |
| Output Cell | DOSSIER SECTIONS!E5 |
| Sources Cell | DOSSIER SECTIONS!F5 |
| **Content Focus** | Lead qualification, fit score, decision makers |

### WRITER_STRATEGY
| Sheet Row | 6 |
|-----------|---|
| Input Cell | DOSSIER SECTIONS!D6 |
| Prompt Cell | DOSSIER SECTIONS!C6 |
| Output Cell | DOSSIER SECTIONS!E6 |
| Sources Cell | DOSSIER SECTIONS!F6 |
| **Content Focus** | Recommended approach, talking points, objection handling |

### WRITER_OPPORTUNITY_DETAILS
| Sheet Row | 7 |
|-----------|---|
| Input Cell | DOSSIER SECTIONS!D7 |
| Prompt Cell | DOSSIER SECTIONS!C7 |
| Output Cell | DOSSIER SECTIONS!E7 |
| Sources Cell | DOSSIER SECTIONS!F7 |
| **Content Focus** | Deal size, competitive landscape, market context |

### WRITER_CLIENT_SPECIFIC
| Sheet Row | 8 |
|-----------|---|
| Input Cell | DOSSIER SECTIONS!D8 |
| Prompt Cell | DOSSIER SECTIONS!C8 |
| Output Cell | DOSSIER SECTIONS!E8 |
| Sources Cell | DOSSIER SECTIONS!F8 |
| **Content Focus** | Client-specific angles, relevant case studies, product fit |

---

## LLM Configuration

All writers use:
- **Model:** gpt-4.1
- **Mode:** Sync (single call, but called async from parent)
- **Tools:** None (just generation, no search)

## DOSSIER SECTIONS Sheet Structure

| Column | Purpose |
|--------|---------|
| A | Section key (intro, signals, etc.) |
| B | Section name (display) |
| C | Prompt template |
| D | Input data (populated by pipeline) |
| E | Output content (written by writer) |
| F | Source citations |

---

## Output Format

Each writer produces:

```json
{
  "section_key": "intro",
  "content": {
    "title": "Executive Summary",
    "body": "Markdown formatted content...",
    "highlights": [
      "Key point 1",
      "Key point 2"
    ]
  },
  "sources": [
    {
      "title": "Source Name",
      "url": "https://...",
      "accessed": "2025-01-11"
    }
  ]
}
```

---

## Parallel Execution

All 6 writers run simultaneously:

```
09_DOSSIER_PLAN
      │
      ├── WRITER_INTRO ─────────────┐
      ├── WRITER_SIGNALS ───────────┤
      ├── WRITER_LEAD_INTELLIGENCE ─┼─→ All run in parallel
      ├── WRITER_STRATEGY ──────────┤
      ├── WRITER_OPPORTUNITY ───────┤
      └── WRITER_CLIENT_SPECIFIC ───┘
                                    │
                                    ▼
                        Poll all 6 until complete
                                    │
                                    ▼
                            Final Assembly
```

---

## Migration Notes

1. **Identical structure** - One implementation with section config
2. **Simple LLM calls** - No async/polling within each writer
3. **Sheet-based prompts** - Extract 6 prompts to files
4. **Sources tracking** - Must preserve source URLs for citations
5. **Parallel execution** - Must handle 6 concurrent writers

## Python Equivalent

```python
WRITER_CONFIG = {
    "intro": {"row": 2, "prompt_file": "writer-intro.md"},
    "signals": {"row": 3, "prompt_file": "writer-signals.md"},
    "lead_intelligence": {"row": 5, "prompt_file": "writer-lead.md"},
    "strategy": {"row": 6, "prompt_file": "writer-strategy.md"},
    "opportunity": {"row": 7, "prompt_file": "writer-opportunity.md"},
    "client_specific": {"row": 8, "prompt_file": "writer-client.md"},
}

async def run_writer(section_key: str, context_pack: dict) -> dict:
    config = WRITER_CONFIG[section_key]
    result = await prompt(
        config["prompt_file"],
        variables={"context": context_pack},
        model="gpt-4.1",
        log=True,
        tags=[f"writer-{section_key}"]
    )
    return {
        "section_key": section_key,
        "content": result["content"],
        "sources": result.get("sources", [])
    }
```
