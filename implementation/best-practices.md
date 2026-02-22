# Best Practices — Cozy Triage

---

## 1. Commit Message Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]

[optional footer: e.g. Closes #42]
```

### Types
| Type       | When to use                                               |
|------------|-----------------------------------------------------------|
| `feat`     | New feature or user-visible behaviour                     |
| `fix`      | Bug fix                                                   |
| `refactor` | Code change that neither fixes a bug nor adds a feature   |
| `test`     | Adding or correcting tests                                |
| `docs`     | Documentation only                                        |
| `chore`    | Tooling, dependencies, config (no production code change) |
| `style`    | Formatting only (no logic change)                         |

### Examples
```
feat(triage): add vector similarity duplicate detection
fix(llm_service): clamp priority to 1–5 before persistence
test(graphrag_service): add ownership isolation tests
chore: pin neo4j driver to 5.x in requirements.txt
```

### Rules
- Summary line ≤ 72 characters, imperative mood ("add" not "added")
- One logical change per commit — avoid "fix everything" mega-commits
- Reference issue numbers in the footer when applicable

---

## 2. Code Organisation

### Django app structure
Prefer domain-based apps over a single monolith. Suggested layout:

```
core/               ← Auth, base views, base templates
  models.py         ← Django auth user only; graph nodes live in Memgraph
  views.py
  urls.py
triage/             ← Brain dump, triage pipeline, suggestions
  services/
    triage_service.py
    llm_service.py
    embeddings_service.py
    graphrag_service.py
  views.py
  urls.py
tasks/              ← Task + Project CRUD views
  views.py
  urls.py
```

### Service layer rules
- **Services are plain Python modules** (no Django model inheritance)
- Services are the only layer that talks to Memgraph or external APIs
- Views call services; services never call views
- Each service function has a single, named responsibility
- All Memgraph queries live inside `graphrag_service` — no raw Cypher in views
- **Every Memgraph read query includes the ownership filter:**
  `(u:User {id: $user_id})-[:OWNS]->(...)` — no exceptions

### Naming conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions / variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Cypher node params: `$snake_case`

---

## 3. Testing Requirements

### Before every commit
- [ ] `pytest` passes with no failures
- [ ] No new warnings introduced

### Test coverage expectations by layer
| Layer              | Approach                                         |
|--------------------|--------------------------------------------------|
| `llm_service`      | Unit tests with mocked Claude responses          |
| `embeddings_service` | Unit tests with mocked Voyage responses        |
| `triage_service`   | Unit tests mocking both services above           |
| `graphrag_service` | Tests against local Memgraph or a mock driver    |
| Views              | Django test client; assert redirects + status codes |
| Validation logic   | Parametrised tests: valid schema, each invalid case |

### Non-negotiable test cases
- LLM contract validation rejects malformed JSON
- LLM contract validation rejects out-of-range enums and priority values
- Ownership filter: user A's query cannot return user B's tasks
- Accepting a suggestion creates the correct nodes and relationships
- Rejecting a suggestion creates no Task node

### Mocking external services
Always mock Anthropic and Voyage API calls in tests. Never make live API calls in CI.
Use `unittest.mock.patch` or a dedicated fixture.

---

## 4. Security Practices

### API keys and secrets
- **Never commit `.env` or any file containing real API keys**
- `.env.example` with placeholder values is committed; `.env` is gitignored
- Load secrets via `python-decouple` or `django-environ`; crash loudly at startup if missing

### LLM output handling
- All Claude responses are validated against the JSON contract schema **before** any
  database write — validation failures raise, not silently ignore
- Max lengths enforced on `title` (200 chars) and `description` (2000 chars) to prevent
  prompt-injection content from persisting in the graph
- LLM output is always a **suggestion**; no auto-apply path exists in the codebase

### Memgraph queries
- Ownership filter required on every read — reviewed in Phase 6 security audit
- Use parameterised Cypher queries (`$param`) — never f-string / concatenate user input into Cypher
- Log session IDs and prompt versions, **not** raw brain dump text in production

### Django security checklist (production)
- `DEBUG = False`
- `SECRET_KEY` loaded from env
- `ALLOWED_HOSTS` set explicitly
- CSRF protection enabled (Django default — do not disable)

---

## 5. Documentation Expectations

- Each service module has a module-level docstring explaining its responsibility
- Each public function has a docstring: what it does, params, return type, what it raises
- Non-obvious Cypher queries have an inline comment explaining the traversal pattern
- `implementation/` docs are the source of truth for design decisions; update them when
  decisions change (don't let code drift silently from the spec)

---

## 6. Development Workflow

### Branching
- `main` is always in a deployable state
- Feature branches: `feat/<short-description>`
- Bug fix branches: `fix/<short-description>`
- Merge via pull request (even solo — it creates a review record)

### Environment setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real values
python manage.py migrate
python manage.py runserver
```

### Dependency management
- Pin all dependencies in `requirements.txt` with exact versions (`==`)
- Use `requirements-dev.txt` for test/dev-only packages (pytest, coverage, etc.)
- Run `pip install -r requirements.txt` after pulling; never manually edit versions without testing

### Pre-commit checklist
1. `pytest` green
2. No hardcoded secrets or API keys
3. No raw brain dump text in new log statements
4. Commit message follows Conventional Commits format

