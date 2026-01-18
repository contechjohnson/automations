# 06_ENRICH_CONTACTS + 06.2_ENRICH_CONTACT

**Source files:**
- `06_ENRICH_CONTACTS.blueprint.json` (16 modules) - Batch orchestrator
- `06.2_ENRICH_CONTACT.blueprint.json` (10 modules) - Single contact processor

**Execution mode:** Async (called via START_ASYNC_BATCH_ENRICH_CONTACTS)

## Purpose

Batch enrichment of contacts discovered in step 04. The parent (06) iterates over contacts and calls the child (06.2) for each one.

---

## 06_ENRICH_CONTACTS (Parent)

### Module Flow

```
1. StartSubscenario (entry point)
   ↓
2. getCell: ENRICH_CONTACTS_PROMPT (Prompts!C9)
3. getCell: ENRICH_CONTACTS_LIVE_INPUT (Prompts!D9)
   ↓
4. createModelResponse: ENRICH_CONTACTS
   → Model: gpt-4.1
   → Parses contact list, prepares batch
   ↓
5. BasicFeeder: Feed contacts array
   ↓
6. CallSubscenario: START_ASYNC_ENRICH_CONTACT (for each)
   → Calls 06.2 for each contact
   ↓
7. BasicAggregator: Collect results
   ↓
8-14. POLLING LOOP (wait for all contacts)
   ↓
15. updateCell: Output (Prompts!E9)
16. BasicAggregator: Final assembly
```

### LLM Calls (1)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 4 | ENRICH_CONTACTS | gpt-4.1 | Parse and prepare batch |

### Iteration Pattern

```
contacts = parse_contacts(input)
for contact in contacts:
    response_id = call_subscenario("06.2", contact)
    response_ids.append(response_id)

# Poll all until complete
while not all_complete(response_ids):
    await sleep(30)
```

---

## 06.2_ENRICH_CONTACT (Child - Iterator)

### Module Flow

```
1. StartSubscenario (receives single contact)
   ↓
2. getCell: ENRICH_CONTACT_PROMPT (Prompts!C15)
   ↓
3. RunAnAIAgent: AI Agent with web search
   → Researches single contact
   → Uses agent loop (not deep research)
   ↓
4. getCell: COPY_PROMPT (Prompts!C10)
5. getCell: COPY_LIVE_INPUT (Prompts!D10)
   ↓
6. createModelResponse: COPY
   → Generates contact-specific copy
   ↓
7. getCell: COPY_CLIENT_PROMPT (Prompts!C11)
8. getCell: COPY_CLIENT_LIVE_INPUT (Prompts!D11)
   ↓
9. createModelResponse: COPY_CLIENT
   → Generates client-specific outreach copy
   ↓
10. addRow: Contacts sheet
    → Saves enriched contact to Contacts tab
```

### LLM Calls (3 types)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 3 | AI Agent | Agent SDK | Research contact via web |
| 6 | COPY | gpt-4.1 | Generate contact copy |
| 9 | COPY_CLIENT | gpt-4.1 | Generate client-specific copy |

### Sheets Operations

| Cell | Operation | Purpose |
|------|-----------|---------|
| Prompts!C15 | getCell | ENRICH_CONTACT_PROMPT |
| Prompts!C10 | getCell | COPY_PROMPT |
| Prompts!D10 | getCell | COPY_LIVE_INPUT |
| Prompts!C11 | getCell | COPY_CLIENT_PROMPT |
| Prompts!D11 | getCell | COPY_CLIENT_LIVE_INPUT |
| Contacts! | addRow | Save enriched contact |

---

## Data Flow

```
Contacts from Step 04
      │
      ▼
┌─────────────────────────────┐
│   06_ENRICH_CONTACTS        │
│   (parse & iterate)         │
└─────────────────────────────┘
      │
      │  for each contact
      ▼
┌─────────────────────────────┐
│   06.2_ENRICH_CONTACT       │
│   ├── AI Agent research     │
│   ├── Generate COPY         │
│   └── Generate COPY_CLIENT  │
└─────────────────────────────┘
      │
      ▼
Contacts Sheet (enriched row)
```

## Output Per Contact

```json
{
  "name": "John Smith",
  "title": "VP Engineering",
  "email": "john@company.com",
  "linkedin": "linkedin.com/in/johnsmith",
  "research": {
    "background": "...",
    "recent_activity": "...",
    "talking_points": [...]
  },
  "copy": "Personalized outreach message...",
  "copy_client": "Client-specific angle for outreach..."
}
```

## Parallel Execution Context

Runs alongside 09_DOSSIER_PLAN in the final phase:

```
START_ASYNC_DOSSIER_PLAN_AND_WRITERS ─┐
                                      ├─→ Poll both
START_ASYNC_BATCH_ENRICH_CONTACTS ────┘ (this)
```

## Migration Notes

1. **Parent-child pattern** - Need to handle iteration + aggregation
2. **AI Agent usage** - Uses OpenAI Agent SDK (not just chat completion)
3. **Per-contact state** - Each contact enriched independently
4. **Copy generation** - 2 types of copy per contact
5. **Sheet output** - Writes to Contacts tab (needs DB table equivalent)

## Agent SDK Note

The AI Agent in 06.2 uses a different pattern than deep research:

```python
# Agent SDK pattern (multiple turns)
from agents import Agent, Runner

agent = Agent(
    model="gpt-4.1",
    tools=[web_search_tool]
)

runner = Runner(agent)
result = runner.run(f"Research {contact_name} at {company}")
```

This allows the agent to iterate and refine searches, unlike deep research which is a single long call.
