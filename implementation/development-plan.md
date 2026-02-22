# Development Plan — Cozy Triage MVP

## Overview

This plan breaks the MVP into 6 phases ordered by dependency. Each phase produces
runnable, testable software. Estimated total for a single developer: **3–5 weeks**.

```
Phase 0 (Bootstrap) ──► Phase 1 (Data Layer) ──► Phase 3 (AI Pipeline) ──► Phase 4 (Triage UI) ──► Phase 6 (Hardening)
                    └──► Phase 2 (Auth + Shell) ──────────────────────────────────────────────────► Phase 4
                                                   Phase 1 ──► Phase 5 (Task/Project Views)
```

---

## Phase 0: Project Bootstrap
**Goal:** Runnable Django project with Memgraph connection verified.
**Effort:** Low (~1–2 days)

### Tasks
- [ ] `django-admin startproject` + initial app(s) (`core` or domain-split)
- [ ] `requirements.txt` with pinned versions: Django, neo4j (Bolt driver), python-decouple, requests
- [ ] `settings.py` reads all secrets from environment (never hardcoded)
- [ ] `.env` file created locally with Memgraph, Anthropic, and Voyage credentials
- [ ] Verify Memgraph Cloud connection: simple Bolt ping, log success/failure
- [ ] Confirm Voyage AI key works: test embedding call returns a 1024-dim vector

### Testing
- Smoke test: `python manage.py runserver` succeeds with no errors
- Smoke test: Memgraph connection utility returns `OK`
- `pytest` skeleton in place (no test logic yet, just runnable)

---

## Phase 1: Graph Schema + Data Layer
**Goal:** Memgraph schema deployed; `graphrag_service` can CRUD all node types with ownership isolation.
**Effort:** Medium (~2–3 days)

### Tasks
- [ ] Cypher schema setup script: uniqueness constraints on all node `id` fields
- [ ] Vector index on `Task(embedding)` at correct dimensionality (1024 for Voyage `voyage-3`)
- [ ] Python dataclasses / DTOs mirroring each node type (User, Task, Project, Area, Resource, TriageSession, Suggestion)
- [ ] `graphrag_service`: CRUD + relationship creation for all node/edge types
- [ ] **Every query includes `(u:User {id: $user_id})-[:OWNS]->` ownership filter** — no exceptions
- [ ] `konmari_signal` (JOY / NEUTRAL / DRAIN) and `next_action` on Task node (see `data-model.md`)

### Dependencies
- Phase 0 complete

### Testing
- Unit tests with a local Memgraph instance or mock driver
- Assert ownership filter is present on every read query
- Test: create Task → fetch by user → returns correct node
- Test: user A cannot retrieve user B's tasks

---

## Phase 2: Authentication + Base UI Shell
**Goal:** Users can sign up, log in, and see a protected dashboard shell.
**Effort:** Low (~1–2 days)

### Tasks
- [ ] Django built-in auth: login, logout, signup views + templates
- [ ] On signup: create `User` node in Memgraph (linked to Django `auth.User`)
- [ ] `base.html`: nav skeleton, login-required decorator applied globally
- [ ] Dashboard stub: placeholder content, confirms auth works end-to-end
- [ ] CSS custom properties for cozy theme (soft palette, rounded corners, card layout)

### Dependencies
- Phase 0 complete; Phase 1 recommended (User node on signup)

### Testing
- Signup creates Django user + Memgraph User node
- Unauthenticated requests redirect to `/login`
- Login/logout cycle works

---

## Phase 3: Brain Dump + LLM Triage Pipeline *(Core AI — most complex phase)*
**Goal:** Submitted brain dump produces TriageSession + Suggestion nodes in Memgraph.
**Effort:** High (~4–5 days)

### Tasks
- [ ] `embeddings_service`: call Voyage AI, return normalized float vector; handle rate limits
- [ ] `llm_service`:
  - Build system prompt + user prompt (brain dump text)
  - Call Claude with structured JSON output mode
  - Validate response against LLM contract schema (llm-contracts.md)
  - Clamp `priority`/`urgency` to 1–5; enforce max title/description lengths
  - Retry once on malformed JSON; raise after second failure
- [ ] `triage_service` (orchestration):
  1. Create `TriageSession` node
  2. `llm_service` → initial parse of brain dump
  3. For each candidate: `embeddings_service` → Memgraph vector search for duplicates
  4. Fetch graph context: projects, areas, recent triage decisions (1–2 hop expansion)
  5. `llm_service` → final suggestions enriched with retrieved context
  6. Persist `Suggestion` nodes linked to session
- [ ] Log session ID and model/prompt version on every triage run (for debugging)

### Dependencies
- Phase 1 complete (graphrag_service, schema in place)
- External: `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY` in `.env`

### Testing
- Unit test `llm_service` with mocked Claude response (valid + invalid JSON)
- Unit test `embeddings_service` with mocked Voyage response
- Unit test validation: rejects missing fields, bad enums, out-of-range priority
- Integration test: full triage run with a fixed brain dump → expected Suggestion count + structure
- Test: LLM failure is caught, user sees a clear error, no partial state persisted

---

## Phase 4: Triage Review UI
**Goal:** User reviews, edits, accepts/rejects AI suggestions; accepted suggestions become real tasks.
**Effort:** Medium (~2–3 days)

### Tasks
- [ ] `/inbox`: multiline textarea + submit button; triggers `triage_service`; shows loading state
- [ ] `/triage/<session_id>`: suggestion review cards showing:
  - Suggested title, next action, status, priority/urgency/effort, project, duplicate warning
  - Accept / Edit (inline fields) / Reject per item
  - Batch: Accept All / Reject All
- [ ] `triage_service.apply_suggestions`: atomic write — accepted Suggestions become Task/Project/Area
      nodes with correct relationships (see `architecture.md` for full logic)
- [ ] Mark `Suggestion.accepted_bool = true/false`; redirect to `/tasks` after apply
- [ ] Never auto-apply; always require explicit user confirmation

### Dependencies
- Phase 2 (auth, base template)
- Phase 3 (triage pipeline)

### Testing
- Submit brain dump → arrive at review page with correct suggestion count
- Accept a suggestion → Task node exists in Memgraph with correct fields
- Reject a suggestion → no Task node created, `accepted_bool = false`
- Edit + accept → Task reflects edited values, not raw LLM output
- Empty brain dump → graceful validation error, no TriageSession created

---

## Phase 5: Task + Project Management Views
**Goal:** Users can view, filter, update, and complete all their tasks and projects.
**Effort:** Medium (~2–3 days)

### Tasks
- [ ] `/tasks`: tabbed list using canonical statuses — NEXT / IN_PROGRESS / WAITING / SOMEDAY / DONE / All
- [ ] Task card: title, next action, project, priority badge, effort badge, status dropdown, complete checkbox
- [ ] Filter by Area, Project, Effort
- [ ] Inline status update (no page reload required)
- [ ] `/projects`: project list; project detail with task list + no-NEXT-action warning
- [ ] `/inbox` also shows existing INBOX tasks (not just brain dump form)

### Dependencies
- Phase 2 (auth, templates)
- Phase 1 (graphrag_service reads)

### Testing
- Filter: "Next Actions" tab returns only `status=NEXT` tasks for this user
- Status transition: INBOX → NEXT → DONE via dropdown
- Projects: detail page lists correct tasks; shows warning when no NEXT task exists
- No tasks from another user are visible

---

## Phase 6: Hardening + Polish
**Goal:** Stable, secure, accessible end-to-end flow ready for daily use.
**Effort:** Low–Medium (~2 days)

### Tasks
- [ ] Error handling: LLM failures, Memgraph timeouts, Voyage quota errors — user-facing messages
- [ ] Log redaction: brain dump text never logged in plaintext in production
- [ ] Accessibility pass: keyboard nav, visible focus states, no color-only status indicators
- [ ] Cozy styling pass consistent with UI.md spec
- [ ] Security audit: ownership query review, prompt injection surface check, no secrets in logs

### Testing
- End-to-end: signup → brain dump → triage review → task list → mark complete
- Error path: simulate LLM timeout → user sees error, data intact
- Cross-user: confirm no data leakage between two test users

---

## Component Complexity Summary

| Component               | Complexity   | Key Risk                                              |
|-------------------------|--------------|-------------------------------------------------------|
| Memgraph schema + CRUD  | Medium       | Ownership filters must be on every query              |
| `embeddings_service`    | Low          | Thin Voyage wrapper; rate limits only concern         |
| `llm_service`           | Medium       | Prompt stability; validation must be strict           |
| `triage_service`        | **High**     | Multi-step orchestration; most logic lives here       |
| Triage Review UI        | Medium       | Accept/edit/reject state; apply logic must be atomic  |
| Task / Project views    | Low–Medium   | Mostly reads + status updates                         |
| Auth                    | Low          | Django built-in; only custom part is Memgraph sync    |
| Styling                 | Low          | CSS variables; no heavy framework needed              |

