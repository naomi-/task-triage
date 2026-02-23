"""
test_triage_service.py — Tests for triage orchestration service.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from core.dtos import TriageSessionNode, SuggestionNode, TaskNode, ProjectNode, AreaNode, TaskStatus
from core.services import triage_service


class TestFetchUserContext:
    """Unit tests for _fetch_user_context helper."""

    @patch("core.services.triage_service.graphrag_service")
    def test_fetch_context_success(self, mock_graphrag):
        """Successfully fetch user context."""
        # Mock the graphrag service calls
        mock_graphrag.list_projects.return_value = [
            ProjectNode(id="p1", name="Project 1", outcome="Build feature"),
            ProjectNode(id="p2", name="Project 2", outcome="Fix bugs"),
        ]
        mock_graphrag.list_areas.return_value = [
            AreaNode(id="a1", name="Work"),
            AreaNode(id="a2", name="Health"),
        ]
        mock_graphrag.list_tasks.return_value = [
            TaskNode(
                id="t1",
                title="Task 1",
                status=TaskStatus.NEXT,
                priority=3,
                urgency=3,
                effort="M",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

        context = triage_service._fetch_user_context("user123")

        assert "recent_projects" in context
        assert "active_areas" in context
        assert "recent_decisions" in context
        assert len(context["recent_projects"]) == 2
        assert len(context["active_areas"]) == 2
        assert len(context["recent_decisions"]) == 1

    @patch("core.services.triage_service.graphrag_service")
    def test_fetch_context_handles_errors(self, mock_graphrag):
        """Gracefully handle errors when fetching context."""
        mock_graphrag.list_projects.side_effect = Exception("DB error")

        context = triage_service._fetch_user_context("user123")

        # Should return empty context, not raise
        assert context["recent_projects"] == []
        assert context["active_areas"] == []
        assert context["recent_decisions"] == []


class TestRunTriage:
    """Unit tests for run_triage orchestration."""

    @patch("core.services.triage_service.graphrag_service")
    @patch("core.services.triage_service.llm_service")
    @patch("core.services.triage_service.embeddings_service")
    def test_run_triage_success(self, mock_embeddings, mock_llm, mock_graphrag):
        """Successfully run full triage pipeline."""
        # Mock LLM response
        mock_llm.triage_brain_dump.return_value = {
            "items": [
                {
                    "raw_text": "buy milk",
                    "action_title": "Buy milk",
                    "description": "Get milk from store",
                    "status": "NEXT",
                    "priority": 3,
                    "urgency": 2,
                    "effort": "XS",
                    "para_bucket": "AREA",
                    "project_suggestions": [],
                    "area_suggestions": [{"name": "Errands"}],
                    "needs_clarification": False,
                    "clarifying_questions": [],
                    "duplicate_candidates": [],
                    "next_action": "Go to store",
                }
            ]
        }

        # Mock embeddings
        mock_embeddings.embed_query.return_value = [0.1] * 1024

        # Mock graphrag calls
        mock_graphrag.vector_search_tasks.return_value = []
        mock_graphrag.create_triage_session.return_value = None
        mock_graphrag.create_suggestion.return_value = None
        mock_graphrag.list_projects.return_value = []
        mock_graphrag.list_areas.return_value = []
        mock_graphrag.list_tasks.return_value = []

        result = triage_service.run_triage("user123", "buy milk")

        assert result["error"] is None
        assert "session_id" in result
        assert len(result["suggestions"]) == 1
        assert result["suggestions"][0].suggestion_type == "triage_item"

    @patch("core.services.triage_service.graphrag_service")
    @patch("core.services.triage_service.llm_service")
    def test_run_triage_llm_failure(self, mock_llm, mock_graphrag):
        """Handle LLM failure gracefully."""
        mock_llm.triage_brain_dump.side_effect = ValueError("Invalid response")
        mock_graphrag.create_triage_session.return_value = None
        mock_graphrag.list_projects.return_value = []
        mock_graphrag.list_areas.return_value = []
        mock_graphrag.list_tasks.return_value = []

        result = triage_service.run_triage("user123", "test")

        assert result["error"] is not None
        assert len(result["suggestions"]) == 0
        assert "session_id" in result

