---
name: planning-roadmap
description: Plan and prioritize automations to build. Use when discussing what to build next, prioritizing features, planning future automations, or when user mentions "roadmap", "what should we build", "priorities", "next automation", or "future plans".
allowed-tools: Read, Edit, Write
---

# Planning Roadmap

Maintain and update the automation roadmap to ensure we build what matters.

## When This Skill Activates

- "What should we build next?"
- "Let's plan the roadmap"
- "What's the priority?"
- "Should we build X or Y first?"
- "Add this to the roadmap"
- "What automations are planned?"
- "Future features for X"

## Core Principle

**Solve real problems, not hypothetical ones.**

Before adding anything to the roadmap, ask:
1. What specific problem does this solve?
2. Who needs this and how urgently?
3. What's the ROI (time saved, revenue enabled, pain removed)?
4. Can we solve this simpler or is it actually needed now?

## The Roadmap Document

All planning lives in a single document:

**[docs/ROADMAP.md](../../../docs/ROADMAP.md)**

This is the source of truth. Always read it before discussing priorities, and update it when plans change.

## Workflow

### When Discussing What to Build

1. **Read the roadmap first**
   ```
   Read docs/ROADMAP.md
   ```

2. **Evaluate against current priorities**
   - Does it align with active client needs?
   - Does it unblock other high-priority work?
   - Is there a simpler solution?

3. **Update the roadmap** if plans change
   - Add new items with clear problem statements
   - Re-rank if priorities shift
   - Move completed items to Done section

### When Adding New Items

Every roadmap item needs:

```markdown
### [P1/P2/P3] Item Name
**Problem:** What specific pain point or need does this address?
**Value:** Who benefits and how? (revenue, time saved, capability)
**Scope:** Rough size (small/medium/large)
**Dependencies:** What needs to exist first?
**Notes:** Context, alternatives considered
```

### Priority Levels

| Level | Meaning | Timeline |
|-------|---------|----------|
| **P1** | Critical - blocks revenue or core capability | This week |
| **P2** | Important - significant value, clear need | This month |
| **P3** | Nice to have - valuable but not urgent | When time allows |
| **Backlog** | Ideas - not yet validated or scoped | Someday/maybe |

### When to Deprioritize

Move items down or to backlog if:
- The problem isn't actually being felt yet
- A simpler workaround exists
- Dependencies aren't ready
- Client priorities shifted

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Add items without a problem statement | Always articulate the specific pain |
| Build for hypothetical future needs | Build for current, validated needs |
| Keep stale items at high priority | Ruthlessly demote or remove |
| Plan too far ahead in detail | Keep P3/backlog items lightweight |
| Build infrastructure before use cases | Build the use case, extract patterns later |

## Roadmap Maintenance

**Weekly:** Quick scan - anything completed? Priorities changed?
**When adding automation:** Check if it's on roadmap, update status
**When client feedback:** Re-evaluate priorities based on real needs
