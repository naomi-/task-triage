# DATA_MODEL.md — Graph schema

## Node labels
- User {id, email, created_at, preferences_json}
- Task {id, title, description, next_action?, status, priority, urgency, effort, due_date?, energy_signal?, created_at, updated_at, embedding, embedding_model}
- Project {id, name, outcome, status}
- Area {id, name}
- Resource {id, name, type, url?}
- TriageSession {id, created_at, input_text, model, prompt_version}
- Suggestion {id, created_at, suggestion_type, payload_json, accepted_bool}

## Relationships
(User)-[:OWNS]->(Task|Project|Area|Resource|TriageSession|Suggestion)
(Task)-[:PART_OF]->(Project)    ← many-to-many: a task may belong to multiple projects
(Task)-[:IN_AREA]->(Area)       ← many-to-many: a task may span multiple areas
(Task)-[:HAS_RESOURCE]->(Resource)
(Task)-[:DEPENDS_ON]->(Task)
(Task)-[:BLOCKS]->(Task)
(Task)-[:DUPLICATE_OF]->(Task)
(TriageSession)-[:PRODUCED]->(Suggestion)
(Suggestion)-[:SUGGESTS_UPDATE_FOR]->(Task)

## Task enums
status: INBOX | NEXT | IN_PROGRESS | WAITING | SOMEDAY | DONE | ARCHIVED
effort: XS | S | M | L | XL
energy_signal: JOY | NEUTRAL | DRAIN  (optional; how this task feels energetically — inspired by KonMari; MVP stand-in for future energy profile)

## Status meanings
- INBOX       → captured, not yet triaged
- NEXT        → chosen next action, ready to start
- IN_PROGRESS → actively being worked on right now
- WAITING     → blocked on an external person or dependency
- SOMEDAY     → parking lot; not now, maybe later
- DONE        → completed
- ARCHIVED    → inactive; kept for reference

## Time-sensitivity handling
Time-sensitive tasks are NOT modelled as a separate status value.
Instead, time-sensitivity is conveyed by two existing fields:
- `due_date`  → hard deadline (surfaces as a visual indicator in the UI)
- `urgency`   → score 1–5; urgency ≥ 4 triggers an "urgent" badge
A task can be WAITING *and* time-sensitive simultaneously; conflating these into
a single status field would lose information.

## Vector index
Create a vector index on Task(embedding) with configured dimension/capacity.
Voyage AI `voyage-3` produces 1024-dimensional vectors; set index accordingly.