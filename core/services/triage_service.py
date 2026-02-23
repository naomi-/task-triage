"""
triage_service.py — High-level triage pipeline orchestrator.

Coordinates:
  1. graphrag_service  — fetch user context (existing tasks/projects/areas)
  2. llm_service       — send brain dump + context to Claude, get suggestions
  3. embeddings_service — embed accepted tasks for vector search
  4. graphrag_service  — persist accepted suggestions as graph nodes/edges
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from core.dtos import TriageSessionNode, SuggestionNode, TaskStatus
from core.services import graphrag_service, llm_service, embeddings_service

logger = logging.getLogger(__name__)


def run_triage(user_id: str, brain_dump: str) -> dict:
    """
    Full triage pipeline: parse brain dump, fetch context, generate suggestions.

    Args:
        user_id: Django user ID (string)
        brain_dump: Unstructured text from user

    Returns:
        {
            "session_id": "uuid",
            "suggestions": [SuggestionNode, ...],
            "error": None or error message
        }
    """
    session_id = str(uuid.uuid4())

    try:
        # Step 1: Create TriageSession node
        session = TriageSessionNode(
            id=session_id,
            created_at=datetime.now(timezone.utc),
            input_text=brain_dump,
            model="claude-3-sonnet-20240229",
            prompt_version="v1",
        )
        graphrag_service.create_triage_session(user_id, session)
        logger.info(f"Created TriageSession {session_id} for user {user_id}")

        # Step 2: Fetch user context (recent projects, areas, decisions)
        context = _fetch_user_context(user_id)

        # Step 3: Call LLM to get initial suggestions
        triage_result = llm_service.triage_brain_dump(brain_dump, context)

        # Step 4: For each suggestion, check for duplicates via vector search
        suggestions = []
        for item in triage_result["items"]:
            # Embed the action title for duplicate detection
            embedding = embeddings_service.embed_query(item["action_title"])

            # Search for similar tasks in user's graph
            similar_tasks = graphrag_service.vector_search_tasks(
                user_id=user_id,
                embedding=embedding,
                limit=3,
                threshold=0.85,
            )

            # Build payload JSON with all suggestion data
            payload = {
                "raw_text": item.get("raw_text", ""),
                "action_title": item["action_title"],
                "description": item["description"],
                "status": item["status"],
                "priority": item["priority"],
                "urgency": item["urgency"],
                "effort": item["effort"],
                "para_bucket": item.get("para_bucket", "ARCHIVE"),
                "project_suggestions": item.get("project_suggestions", []),
                "area_suggestions": item.get("area_suggestions", []),
                "needs_clarification": item.get("needs_clarification", False),
                "clarifying_questions": item.get("clarifying_questions", []),
                "duplicate_candidates": [
                    {"task_id": t.id, "reason": f"Similarity: {t.title}"}
                    for t in similar_tasks
                ],
                "next_action": item.get("next_action", ""),
            }

            # Create Suggestion node
            suggestion = SuggestionNode(
                id=str(uuid.uuid4()),
                created_at=datetime.now(timezone.utc),
                suggestion_type="triage_item",
                payload_json=json.dumps(payload),
                accepted_bool=False,
            )

            # Persist suggestion
            graphrag_service.create_suggestion(user_id, session_id, suggestion)
            suggestions.append(suggestion)
            logger.info(f"Created Suggestion {suggestion.id} for session {session_id}")

        logger.info(f"Triage complete: {len(suggestions)} suggestions for session {session_id}")
        return {
            "session_id": session_id,
            "suggestions": suggestions,
            "error": None,
        }

    except Exception as e:
        logger.exception(f"Triage failed for user {user_id}, session {session_id}")
        return {
            "session_id": session_id,
            "suggestions": [],
            "error": str(e),
        }


def _fetch_user_context(user_id: str) -> dict:
    """
    Fetch user's recent projects, areas, and triage decisions for context.

    Returns:
        {
            "recent_projects": [{"name": "...", "outcome": "..."}, ...],
            "active_areas": [{"name": "..."}, ...],
            "recent_decisions": [{"title": "...", "status": "..."}, ...],
        }
    """
    try:
        # Fetch recent projects (limit 5)
        projects = graphrag_service.list_projects(user_id)[:5]
        recent_projects = [
            {"name": p.name, "outcome": p.outcome or ""}
            for p in projects
        ]

        # Fetch active areas (limit 5)
        areas = graphrag_service.list_areas(user_id)[:5]
        active_areas = [{"name": a.name} for a in areas]

        # Fetch recent NEXT/IN_PROGRESS tasks (limit 5)
        next_tasks = graphrag_service.list_tasks(user_id, status=TaskStatus.NEXT)[:5]
        recent_decisions = [
            {"title": t.title, "status": t.status}
            for t in next_tasks
        ]

        return {
            "recent_projects": recent_projects,
            "active_areas": active_areas,
            "recent_decisions": recent_decisions,
        }
    except Exception as e:
        logger.warning(f"Failed to fetch context for user {user_id}: {e}")
        return {
            "recent_projects": [],
            "active_areas": [],
            "recent_decisions": [],
        }

