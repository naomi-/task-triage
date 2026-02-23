# Future Plans — Post-MVP Features

This document tracks features, frameworks, and explorations that were explicitly
deferred from the MVP to keep scope tight. Revisit these once the core triage loop
is stable and in daily use.

---

## 1. Synalinks — Structured AI Orchestration

**What it is:** Synalinks is a Python orchestration framework for building
structured, validated AI pipelines with composable graph-like workflows.

**Why deferred:** The MVP triage pipeline is a linear 4-step sequence
(`llm_service` → `embeddings_service` → `graphrag_service` → persist). A plain
Python service module handles this cleanly in ~30 lines with no added dependencies.

**When to revisit:** When the pipeline gains meaningful branching — e.g. conditional
clarifying question loops, parallel tool calls, agent-style retry strategies, or
multiple competing LLM calls whose results need merging.

**Reference:** https://synalinks.io

---

## 2. Memgraph MAGE — In-Graph Embeddings

**What it is:** MAGE (Memgraph Advanced Graph Extensions) includes PyTorch-based
graph machine learning modules. One potential use: computing embeddings directly
inside Memgraph rather than via an external API.

**Why deferred:** Voyage AI `voyage-3` is already a proven, well-documented choice
for Anthropic-stack projects. Running MAGE in Memgraph Cloud requires validating
that PyTorch modules are available and performant in that hosted environment — a
non-trivial spike with uncertain payoff.

**When to revisit:** After the MVP is stable. Time-box a half-day spike:
- Confirm MAGE embedding modules work against Memgraph Cloud
- Benchmark retrieval quality vs Voyage voyage-3
- Assess latency and cost difference

If MAGE is viable and meaningfully cheaper/faster, it removes the Voyage API
dependency entirely.

**Reference:** https://memgraph.com/docs/mage

---

## 3. Energy & Affect Profile — Rich Emotional Context on Tasks

**What it is:** A richer replacement for the MVP `energy_signal` field. Instead of
a single three-way signal (JOY / NEUTRAL / DRAIN), this would be a structured
profile capturing multiple dimensions of a task's emotional and energetic character.

**Why deferred:** The MVP `energy_signal` is sufficient to enable the core
prioritization and scheduling hints. The full profile requires more UX work
(how does the user input it? free text parsed by Claude? structured sliders?),
more data model complexity, and careful prompt design to avoid the LLM over-assigning
emotional labels.

**Proposed dimensions (draft):**

| Dimension           | Example values / description                              |
|---------------------|-----------------------------------------------------------|
| `energy_load`       | LOW / MEDIUM / HIGH — cognitive/physical effort required  |
| `emotional_weight`  | LOW / MEDIUM / HIGH — emotional difficulty or sensitivity |
| `affect`            | ENERGIZING / NEUTRAL / DRAINING / JOYFUL / DREADED        |
| `resistance`        | 0–5 — how much the user avoids starting this task         |
| `collaboration`     | SOLO / NEEDS_HELP / BLOCKED_ON_OTHER                      |
| `context_tags`      | list: e.g. ["outdoor", "computer", "creative", "phone"]   |
| `energy_window`     | ANYTIME / HIGH_ENERGY_ONLY / LOW_ENERGY_OK                |

**How it informs scheduling:**
- `HIGH_ENERGY_ONLY` + `HIGH emotional_weight` → surface only during peak hours
- `LOW_ENERGY_OK` + `DRAINING` → good candidate for delegation or decomposition
- `context_tags: ["phone"]` → batch with other phone calls
- `resistance >= 4` → suggest breaking into smaller steps or asking for help

**Migration path:** The `energy_signal` field stays on `Task`. Once the Energy &
Affect Profile schema is finalized, add the new fields alongside it (non-breaking).
Deprecate `energy_signal` in a later release once the richer profile is backfilled.

---

## 4. Weekly Review Dashboard

A guided weekly review flow inspired by GTD's Weekly Review:
- Surfaces tasks stuck in INBOX (not triaged)
- Lists IN_PROGRESS tasks with no recent activity
- Prompts: "Is this still relevant?" / "Can this be deleted or archived?"
- Summary stats: tasks completed this week, new tasks added, projects advanced

**Why deferred:** Requires date-range queries and review-state tracking not needed
for the core daily triage loop.

---

## 5. Recurring Tasks

Support for tasks that regenerate on a schedule (daily / weekly / monthly /
custom cron). Requires a `recurrence_rule` field on Task and a background job
(e.g. Celery or Django management command) to create new task instances.

**Why deferred:** Significant complexity (scheduler, job queue) not needed for MVP.

