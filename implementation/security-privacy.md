# SECURITY_PRIVACY.md — MVP guardrails

## Data privacy
- All data is per-user; no cross-user graph traversal
- Avoid storing secrets in task text
- Log redaction: do not log raw brain dump in plain text in production

## Prompt injection mitigation
- Treat task text as untrusted input
- LLM output is suggestions only; user must review before applying (MVP default)
- Strict JSON schema validation before persistence

## API keys
- Anthropic + Voyage keys loaded via env vars
- No keys committed to repo

## Access control
- Every Memgraph query includes user ownership constraint (User)-[:OWNS]->(...)