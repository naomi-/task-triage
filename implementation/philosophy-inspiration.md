# METHODOLOGY.md — Conceptual foundations (GTD + PARA + Second Brain + KonMari)

This project is inspired by a combination of productivity and cognitive-organization systems.  
The goal is not to enforce a rigid workflow, but to provide **signals** that help users move from overwhelm → clarity → action.

These frameworks inform **data modeling, triage logic, and UI views**, not strict rules.

---

# 1. GTD — Getting Things Done (David Allen)
Official site: https://gettingthingsdone.com/

## Core idea
GTD separates **capture**, **clarify**, **organize**, **reflect**, and **engage** so the user can trust an external system instead of holding everything in their head.

## Key concepts mapped to the app

### Capture → “Brain dump”
- Users can input unstructured text
- Everything initially lands in `INBOX`

### Clarify → “What is it?”
Each item is:
- actionable → becomes a Task
- non-actionable → becomes:
  - reference (Resource)
  - someday/maybe (SOMEDAY)
  - trash (delete)

If actionable:
- Is it one step? → Task
- Multiple steps? → Project

### Organize → Status buckets
Canonical status values (used in data model, LLM contract, and UI):
- `INBOX`       → captured, not yet triaged
- `NEXT`        → chosen next physical action, ready to start
- `IN_PROGRESS` → actively being worked on right now
- `WAITING`     → blocked on an external person or dependency
- `SOMEDAY`     → parking lot; not now, maybe later
- `DONE`        → completed
- `ARCHIVED`    → inactive; kept for reference

**Time-sensitive tasks**: do NOT get a separate status.
Time-sensitivity is expressed via `due_date` (hard deadline) and `urgency` (1–5 score).
A task can be WAITING *and* time-sensitive; a single status field cannot hold both.
The UI surfaces urgency ≥ 4 or near due_date as a visual badge.

### Next action principle
Every active task should have:
- a concrete next step
- low ambiguity
This reduces cognitive friction.

### Weekly review (future feature)
System should support:
- re-triage
- reprioritization
- project outcome checks

---

# 2. PARA — Projects, Areas, Resources, Archives (Tiago Forte)
Overview: https://fortelabs.com/blog/para/

## Core idea
Organize information by **actionability**, not by topic.

## Buckets

### Projects
- Short-term outcomes with a clear finish line
- Example: “File 2025 taxes”

### Areas
- Ongoing responsibilities
- Example: Health, Work, Family

### Resources
- Reference material
- Not actionable tasks

### Archives
- Completed or inactive items

## App mapping
Each Task can:
- belong to a Project
- be associated with an Area
- be moved to Archive when done/inactive

PARA is primarily used for:
- filtering views
- grouping tasks
- structuring long-term context

---

# 3. Second Brain (Tiago Forte)
Overview: https://fortelabs.com/blog/basboverview/

## Core idea
Offload memory into an external system that is:
- searchable
- connected
- reusable

## Principles relevant to this app

### Progressive summarization (future)
Store:
- raw input
- normalized task
- next action
This allows multiple layers of clarity.

### Reuse over storage
Graph relationships allow:
- linking tasks to projects, areas, resources
- surfacing related past work via GraphRAG

### Context retrieval
Graph + vector search enables:
- “Have I done something like this before?”
- “What project does this belong to?”

This reduces duplicate effort and decision fatigue.

---

# 4. KonMari (Marie Kondo) — Value & Energy Signal
Overview: https://konmari.com/

## Core idea
Keep items that “spark joy”; release what does not.

In this app:
This is NOT used as a moral judgment.
It is a **prioritization signal**.

## Signals (MVP)
Each task may optionally carry `konmari_signal`:
- `JOY`     → energizing or meaningful
- `NEUTRAL` → no strong feeling either way
- `DRAIN`   → heavy, aversive, or emotionally costly

This is the MVP stand-in for a richer **Energy & Affect Profile** planned for a future
release (see `future-plans.md`). That profile will capture dimensions like energy load,
emotional resistance, collaboration needs, and environmental context tags
(e.g. "outdoor", "computer", "creative").

## How it’s used
- Helps the LLM suggest:
  - quick wins when energy is low (prefer JOY tasks)
  - delegation or decomposition for DRAIN tasks
  - scheduling DRAIN tasks during high-energy windows
- Helps avoid burnout by balancing task lists

---

# 5. Why combine these systems?

## Complementary strengths

| Framework | Strength |
|-----------|----------|
GTD | Clear next actions & trusted capture |
PARA | Structural organization by actionability |
Second Brain | Long-term knowledge graph & reuse |
KonMari | Emotional/energy awareness |

Together they enable:
- Cognitive offloading (GTD)
- Structural clarity (PARA)
- Contextual memory (GraphRAG / Second Brain)
- Energy-aware prioritization (KonMari)

---

# 6. How this informs the data model

## GTD
- Task.status enum
- next_action field
- project detection

## PARA
- Project / Area nodes
- Archive state

## Second Brain
- Graph relationships
- Vector embeddings for semantic recall

## KonMari
- optional `konmari_signal` on tasks

---

# 7. Design philosophy for engineers

This system should:
- Be **assistive, not prescriptive**
- Allow user overrides at all times
- Store suggestions separately from committed data
- Prefer **low friction capture → delayed structuring**

LLM outputs are:
- proposals
- always reviewable
- never auto-destructive

---

# 8. Future extensions (non-MVP)
- Weekly review dashboard
- Energy-based scheduling
- Project outcome tracking
- Knowledge notes (Second Brain resources)
- Cross-linking tasks ↔ notes ↔ people