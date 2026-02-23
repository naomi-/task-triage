"""
test_llm_service.py — Tests for LLM triage service.
"""

from __future__ import annotations

import pytest

from core.services import llm_service


class TestValidateTriage:
    """Unit tests for triage response validation."""

    def test_valid_response(self):
        """Valid response passes validation."""
        data = {
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
                    "area_suggestions": [],
                    "needs_clarification": False,
                    "clarifying_questions": [],
                    "duplicate_candidates": [],
                    "next_action": "Go to store",
                }
            ]
        }
        result = llm_service._validate_triage_response(data)
        assert len(result["items"]) == 1
        assert result["items"][0]["action_title"] == "Buy milk"

    def test_clamps_priority_urgency(self):
        """Priority/urgency are clamped to 1-5."""
        data = {
            "items": [
                {
                    "raw_text": "test",
                    "action_title": "Test",
                    "description": "Test",
                    "status": "INBOX",
                    "priority": 99,
                    "urgency": -5,
                    "effort": "M",
                    "para_bucket": "ARCHIVE",
                    "project_suggestions": [],
                    "area_suggestions": [],
                    "needs_clarification": False,
                    "clarifying_questions": [],
                    "duplicate_candidates": [],
                    "next_action": "Test",
                }
            ]
        }
        result = llm_service._validate_triage_response(data)
        assert result["items"][0]["priority"] == 5
        assert result["items"][0]["urgency"] == 1

    def test_enforces_max_lengths(self):
        """Title/description/next_action are truncated to max lengths."""
        data = {
            "items": [
                {
                    "raw_text": "x",
                    "action_title": "a" * 300,
                    "description": "b" * 3000,
                    "status": "INBOX",
                    "priority": 3,
                    "urgency": 3,
                    "effort": "S",
                    "para_bucket": "ARCHIVE",
                    "project_suggestions": [],
                    "area_suggestions": [],
                    "needs_clarification": False,
                    "clarifying_questions": [],
                    "duplicate_candidates": [],
                    "next_action": "c" * 600,
                }
            ]
        }
        result = llm_service._validate_triage_response(data)
        assert len(result["items"][0]["action_title"]) == 200
        assert len(result["items"][0]["description"]) == 2000
        assert len(result["items"][0]["next_action"]) == 500

    def test_rejects_invalid_status(self):
        """Invalid status raises ValueError."""
        data = {
            "items": [
                {
                    "raw_text": "x",
                    "action_title": "Test",
                    "description": "Test",
                    "status": "INVALID",
                    "priority": 3,
                    "urgency": 3,
                    "effort": "M",
                    "para_bucket": "ARCHIVE",
                    "project_suggestions": [],
                    "area_suggestions": [],
                    "needs_clarification": False,
                    "clarifying_questions": [],
                    "duplicate_candidates": [],
                    "next_action": "Test",
                }
            ]
        }
        with pytest.raises(ValueError, match="invalid status"):
            llm_service._validate_triage_response(data)

    def test_rejects_invalid_effort(self):
        """Invalid effort raises ValueError."""
        data = {
            "items": [
                {
                    "raw_text": "x",
                    "action_title": "Test",
                    "description": "Test",
                    "status": "INBOX",
                    "priority": 3,
                    "urgency": 3,
                    "effort": "HUGE",
                    "para_bucket": "ARCHIVE",
                    "project_suggestions": [],
                    "area_suggestions": [],
                    "needs_clarification": False,
                    "clarifying_questions": [],
                    "duplicate_candidates": [],
                    "next_action": "Test",
                }
            ]
        }
        with pytest.raises(ValueError, match="invalid effort"):
            llm_service._validate_triage_response(data)

    def test_rejects_missing_required_field(self):
        """Missing required field raises ValueError."""
        data = {
            "items": [
                {
                    "raw_text": "x",
                    "action_title": "Test",
                    # missing description
                    "status": "INBOX",
                    "priority": 3,
                    "urgency": 3,
                    "effort": "M",
                    "para_bucket": "ARCHIVE",
                    "project_suggestions": [],
                    "area_suggestions": [],
                    "needs_clarification": False,
                    "clarifying_questions": [],
                    "duplicate_candidates": [],
                    "next_action": "Test",
                }
            ]
        }
        with pytest.raises(ValueError, match="missing required field"):
            llm_service._validate_triage_response(data)


@pytest.mark.integration
class TestTriageBrainDump:
    """Integration tests for triage_brain_dump with real Claude."""

    @pytest.mark.skip(reason="Claude API key access issue - model not available")
    def test_triage_simple_brain_dump(self):
        """Full triage of a simple brain dump."""
        text = "Buy milk. Call mom. Finish project report."
        result = llm_service.triage_brain_dump(text)

        assert "items" in result
        assert len(result["items"]) > 0

        for item in result["items"]:
            assert "action_title" in item
            assert "status" in item
            assert item["status"] in llm_service.VALID_STATUSES
            assert 1 <= item["priority"] <= 5
            assert 1 <= item["urgency"] <= 5

    def test_rejects_empty_text(self):
        """Empty brain dump raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            llm_service.triage_brain_dump("")

    def test_rejects_whitespace_only(self):
        """Whitespace-only brain dump raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            llm_service.triage_brain_dump("   \n\t  ")

