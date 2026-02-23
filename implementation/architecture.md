# ARCHITECTURE.md — System overview

## High level
Local Django app (UI + orchestration) connects to Memgraph Cloud (primary persistence).
Django calls:
1) Memgraph for reads/writes + retrieval queries
2) Voyage for embeddings
3) Claude for triage reasoning + structured output

## Components
### Django (local)
- Auth + session management
- UI pages: inbox, triage review, tasks, projects
- Services:
  - triage_service: manages triage sessions and suggestions
  - embeddings_service: calls Voyage + stores vectors
  - graphrag_service: runs Memgraph retrieval queries
  - llm_service: calls Claude and validates output

### Memgraph Cloud
- Stores user/task/project graph
- Stores embeddings as vector properties on nodes
- Vector index for task embeddings
- GraphRAG retrieval using Cypher queries (Atomic GraphRAG pattern)

## Request flow: Brain dump triage
1) User submits brain dump text
2) Create TriageSession node in Memgraph
3) Parse/normalize candidates with Claude (structured JSON)
4) For each candidate:
   - Generate embedding (Voyage)
   - Query Memgraph vector index for duplicates/similar tasks
   - Retrieve graph context: projects/areas/recent decisions (1–2 hop expansion)
5) Claude finalizes suggestions using retrieved context
6) Persist Suggestion nodes linked to TriageSession; show review UI
7) User reviews → accept / edit / reject each suggestion (see flow below)

## Request flow: Apply suggestions (triage_service.apply_suggestions)
Called when the user clicks "Apply" after reviewing. All writes are atomic.

For each **accepted** Suggestion:
- Create Task node with all accepted/edited fields (title, description,
  next_action, status, priority, urgency, effort, due_date, energy_signal,
  embedding, embedding_model)
- Create `(User)-[:OWNS]->(Task)`
- For each entry in `project_suggestions` (zero or more):
  - Look up existing Project by name (case-insensitive, scoped to this user)
  - If found: reuse it. If not: create new Project node.
  - Create `(Task)-[:PART_OF]->(Project)`
- For each entry in `area_suggestions` (zero or more):
  - Look up existing Area by name (case-insensitive, scoped to this user)
  - If found: reuse it. If not: create new Area node.
  - Create `(Task)-[:IN_AREA]->(Area)`
- A task may have any combination: multiple PART_OF edges, multiple IN_AREA edges,
  or none at all — these relationships are explicitly many-to-many.
- If `duplicate_candidates` are present and user confirmed a duplicate relationship:
  - Create `(Task)-[:DUPLICATE_OF]->(existing_task)`
- Set `Suggestion.accepted_bool = true`

For each **rejected** Suggestion:
- Set `Suggestion.accepted_bool = false`
- No Task, Project, or Area nodes are created

After all writes: redirect user to `/tasks`.