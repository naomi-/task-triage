# VECTOR_STRATEGY.md — Embeddings + retrieval plan

## Default plan (MVP): Voyage embeddings + Memgraph vector search
1) Generate embedding for each Task (title + description)
2) Store embedding on :Task(embedding)
3) Create Memgraph vector index on :Task(embedding)
4) Use vector_search.search() to:
   - detect duplicates
   - pull similar tasks as retrieval context for Claude
   - support "related tasks" UI later

## Dedupe logic (v1)
- Combine:
  - exact normalized title match
  - vector similarity (top-k with threshold)
- If above threshold:
  - suggest DUPLICATE_OF edge
  - ask user to confirm merge/keep both

## Retrieval context (GraphRAG)
For each candidate task:
- fetch top-k similar tasks via vector search
- expand 1–2 hops in graph: project membership, area, blockers, recent triage decisions
- provide Claude a compact context bundle + instructions to cite node ids

## Spike option: MAGE embeddings
Goal: verify feasibility of computing embeddings inside Memgraph/MAGE:
- CALL embeddings.node_sentence() over Task title/description properties
- confirm model choice, runtime constraints, and Cloud compatibility
If successful:
- reduce external dependency (Voyage) for doc/task embeddings
If not:
- continue with Voyage