# TECHNOLOGY_CHOICES.md — Why these tools

## Database: Memgraph 3.8 (Graph + Vector Single Store)
We use Memgraph 3.8 as a single store for:
- Task graph (relationships, projects, blockers, contexts)
- Vector embeddings + similarity search via vector indexes

Rationale:
- Enables hybrid graph+vector retrieval in one system
- Supports Atomic GraphRAG patterns for "one-query" context generation
- Reduces operational complexity vs separate graph DB + vector DB

Key feature references:
- Atomic GraphRAG + vector single store + parallel runtime (Memgraph 3.8 release blog)
- Vector index creation + vector_search module (Memgraph vector search docs)

## LLM: Anthropic Claude
We use Claude for:
- Parsing brain dumps into tasks
- Normalization + dedupe decisions
- GTD/PARA classification
- Priority/urgency/effort scoring
- Next-action suggestions
- Optional clarifying questions

## Embeddings: Voyage AI (fixed for MVP)
Claude does not provide embeddings.
We use Voyage AI (`voyage-3`, 1024-dimensional vectors) because:
- Anthropic docs point to Voyage as the primary worked example and recommended provider
- Strong retrieval quality; supports query/document input types

> **Deferred to future-plans.md:** Evaluating Memgraph MAGE for in-graph embeddings.
> If MAGE proves viable against Memgraph Cloud it could remove the Voyage dependency
> in a future release.

## Orchestration: Plain Django service layer (MVP)
The triage pipeline is orchestrated by `triage_service` — a plain Python module that
calls `llm_service`, `embeddings_service`, and `graphrag_service` in sequence.
No orchestration framework is needed for MVP; the flow is a linear multi-step function.

GraphRAG retrieval is executed via Memgraph Cypher queries (Atomic GraphRAG style).

> **Deferred to future-plans.md:** Synalinks as a structured orchestration framework.
> It becomes relevant if the pipeline grows to include branching, retries, parallel
> tool calls, or agent-style loops.
