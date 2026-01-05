---
name: managing-mental-models
description: Maintain and update prime directives for Columnline, Prologis, and Life. Use when discussing business strategy, updating todos, adding clients, changing priorities, referencing context for any domain, or when user mentions "mental model", "update columnline", "prologis stuff", "life todo", "new client", "priority change", or any work that affects these three domains.
allowed-tools: Read, Write, Glob, Bash
---

# Managing Mental Models

Maintain three prime directive files that capture the complete mental model for each domain of Connor's work and life.

## Prime Directive Locations

| Domain | File | What It Contains |
|--------|------|------------------|
| **Columnline** | `directives/prime/columnline.md` | Business model, clients, leads, revenue, strategy |
| **Prologis** | `directives/prime/prologis.md` | Day job context, projects, relationships, goals |
| **Life** | `directives/prime/life.md` | Personal priorities, health, relationships, growth |

## When This Skill Activates

**Explicit triggers:**
- "Update my todos"
- "Add [X] to columnline priorities"
- "New client: [name]"
- "Prologis update"
- "Life goal change"

**Implicit triggers (auto-detect):**
- Onboarding a new client → update Columnline clients section
- Completing a major deliverable → update priorities, maybe add learnings
- Discussing day job → reference Prologis context
- Personal planning → reference Life context
- Building an automation → check if it affects any prime directive

## File Structure (Each Prime Directive)

```markdown
# {Domain} Mental Model

> One-line philosophy for this domain

## Context
{Current state, what's happening, key facts}

## Goal & Intent
{What success looks like, why this matters}

## Priorities
1. {Priority 1} - {Why}
2. {Priority 2} - {Why}
3. {Priority 3} - {Why}

## Philosophy
{Decision-making principles, values, approach}

## Network
{Key people, relationships, contacts}

## Todos
- [ ] {Task} — {context/deadline if relevant}
- [ ] {Task}
- [x] {Completed task} ✓ {date}
```

## How To Use

### Reading Context
Before doing work in any domain, read the relevant prime directive:

```bash
# Check what matters for Columnline right now
cat directives/prime/columnline.md
```

### Updating Todos
When adding or completing tasks, edit the Todos section:

```markdown
## Todos
- [ ] Follow up with Roger Acres on seed delivery — due Jan 15
- [ ] Build FERC scraper template — blocks Paul Phelan work
- [x] Deploy Maricopa permits scraper ✓ 2026-01-03
```

### Adding Clients/Contacts
When a new client is onboarded or contact is important:

```markdown
## Network
**Active Clients:**
- Roger Acres (Span Construction) — Data center electrical, 400 seeds Q1
- Paul Phelan (Phelan's Interiors) — Healthcare FFE, Eastern Iowa

**Priority Leads:**
- Abi Reiland — Commercial broker, Des Moines
```

### Updating Priorities
When strategic focus shifts:

```markdown
## Priorities
1. Roger Acres delivery — Revenue commitment, reputation
2. Framework templates — Foundation for scale
3. Paul Phelan pilot — Proves healthcare vertical
```

## Cross-Domain Awareness

Sometimes work affects multiple domains:

| If you're doing... | Consider updating... |
|-------------------|---------------------|
| Columnline client work | Life todos (block deep work time) |
| Prologis late nights | Life (energy management) |
| Life health goals | Prologis/Columnline (capacity planning) |
| New automation | Columnline (add to capabilities) |

## Auto-Detection Patterns

Claude should recognize and suggest updates when:

- **New client mentioned**: "Hey, I just closed Acme Corp" → Suggest adding to Columnline Network
- **Task completed**: "Shipped the FERC scraper" → Suggest marking todo complete
- **Priority shift**: "Actually, Paul is more urgent than Roger" → Suggest reordering priorities
- **Context change**: "Prologis is doing layoffs" → Suggest updating Prologis Context
- **Capacity issue**: "I'm burned out" → Suggest Life update + reduce commitments

## Integration with Other Skills

**Before creating a directive:**
Read prime directives to ensure the automation solves the right problem.

**Before building an automation:**
Check if it maps to a Columnline priority or client need.

**When planning work:**
Reference all three to balance commitments.

## Self-Annealing

After any update to prime directives:
1. Verify the change reflects reality
2. Check for cross-domain impacts
3. Update related todos if needed

See `LEARNINGS.md` for patterns and edge cases.
