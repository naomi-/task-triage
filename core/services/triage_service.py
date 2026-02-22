"""
triage_service.py — High-level triage pipeline orchestrator.

Coordinates:
  1. graphrag_service  — fetch user context (existing tasks/projects/areas)
  2. llm_service       — send brain dump + context to Claude, get suggestions
  3. embeddings_service — embed accepted tasks for vector search
  4. graphrag_service  — persist accepted suggestions as graph nodes/edges

Phase 1 will fill in the full implementation.
"""

from __future__ import annotations

# TODO (Phase 1): implement run_triage(user_id: str, brain_dump: str) -> dict

