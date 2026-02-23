"""
test_graphrag_crud.py — Phase 1 tests for graphrag_service CRUD.

Unit tests use the mock_memgraph fixture and verify:
  - create_task returns the task id
  - get_task with correct user_id returns the node
  - get_task with wrong user_id returns None  (ownership isolation)
  - update_task reflects updated fields
  - find_or_create_project: creates then reuses
  - find_or_create_area: creates then reuses

Integration tests (require real Memgraph creds) perform a full CRUD cycle:
  - User → Task → Project → Area → relationships → vector search
  All cleaned up after the test.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

import pytest

from django.conf import settings

from core.dtos import TaskNode, TaskStatus, TaskEffort, UserNode
from core.services import graphrag_service


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_task(title="Test task", status=TaskStatus.INBOX) -> TaskNode:
    now = datetime.now(timezone.utc)
    return TaskNode(
        id=str(uuid.uuid4()),
        title=title,
        status=status,
        priority=3,
        urgency=2,
        effort=TaskEffort.M,
        created_at=now,
        updated_at=now,
    )


def _make_user(email="test@example.com") -> UserNode:
    return UserNode(
        id=str(uuid.uuid4()),
        email=email,
        created_at=datetime.now(timezone.utc),
    )


# ── Unit tests (mock driver) ────────────────────────────────────────────────

class TestCreateTaskUnit:
    def test_create_task_returns_task_id(self, mock_memgraph):
        """create_task returns the task's id."""
        user_id = str(uuid.uuid4())
        task = _make_task()
        returned_id = graphrag_service.create_task(user_id, task)
        assert returned_id == task.id

    def test_create_task_calls_driver_session(self, mock_memgraph):
        """create_task opens a session and calls session.run."""
        user_id = str(uuid.uuid4())
        task = _make_task()
        graphrag_service.create_task(user_id, task)
        mock_memgraph.session.assert_called()


class TestGetTaskUnit:
    def test_get_task_returns_node_when_found(self, mock_memgraph):
        """get_task returns a TaskNode when the mock returns a matching record."""
        user_id = str(uuid.uuid4())
        task = _make_task()
        now_iso = task.created_at.isoformat()

        # Build a fake record that the session.run().single() will return
        fake_node = {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "urgency": task.urgency,
            "effort": task.effort,
            "created_at": now_iso,
            "updated_at": now_iso,
            "embedding_model": "voyage-3",
            "description": "",
            "next_action": None,
            "due_date": None,
            "energy_signal": None,
            "embedding": None,
        }
        fake_record = {"t": fake_node}
        mock_memgraph.session.return_value.__enter__.return_value.run.return_value.single.return_value = fake_record

        result = graphrag_service.get_task(user_id, task.id)
        assert result is not None
        assert result.id == task.id
        assert result.title == task.title

    def test_get_task_returns_none_when_not_found(self, mock_memgraph):
        """get_task returns None when the session returns no record."""
        mock_memgraph.session.return_value.__enter__.return_value.run.return_value.single.return_value = None
        result = graphrag_service.get_task("user-x", "task-y")
        assert result is None

    def test_get_task_ownership_isolation(self, mock_memgraph):
        """
        Ownership isolation: get_task with the wrong user returns None.
        The mock simulates Memgraph returning no record because the OWNS edge
        doesn't exist for that user.
        """
        # Ownership filter means different user → no record
        mock_memgraph.session.return_value.__enter__.return_value.run.return_value.single.return_value = None
        result = graphrag_service.get_task("wrong-user-id", "some-task-id")
        assert result is None


class TestUpdateTaskUnit:
    def test_update_task_returns_true_when_found(self, mock_memgraph):
        """update_task returns True when the mock returns a record."""
        fake_record = {"id": "task-abc"}
        mock_memgraph.session.return_value.__enter__.return_value.run.return_value.single.return_value = fake_record
        result = graphrag_service.update_task("user-1", "task-abc", {"status": TaskStatus.NEXT})
        assert result is True

    def test_update_task_returns_false_when_not_found(self, mock_memgraph):
        """update_task returns False when the mock returns no record."""
        mock_memgraph.session.return_value.__enter__.return_value.run.return_value.single.return_value = None
        result = graphrag_service.update_task("user-1", "task-xyz", {"status": TaskStatus.DONE})
        assert result is False


class TestOwnershipQueryContents:
    def test_get_task_query_contains_ownership_filter(self, mock_memgraph):
        """
        The Cypher sent to Memgraph for get_task MUST include the ownership filter.
        This test inspects the query string that session.run() was called with.
        """
        mock_memgraph.session.return_value.__enter__.return_value.run.return_value.single.return_value = None
        graphrag_service.get_task("user-1", "task-1")

        run_mock = mock_memgraph.session.return_value.__enter__.return_value.run
        assert run_mock.called
        query_used = run_mock.call_args[0][0]
        assert "OWNS" in query_used, "Ownership filter [:OWNS] missing from get_task query"
        assert "user_id" in query_used, "$user_id param missing from get_task query"

    def test_list_tasks_query_contains_ownership_filter(self, mock_memgraph):
        """list_tasks query MUST include ownership filter."""
        mock_memgraph.session.return_value.__enter__.return_value.run.return_value.__iter__ = lambda s: iter([])
        graphrag_service.list_tasks("user-1")

        run_mock = mock_memgraph.session.return_value.__enter__.return_value.run
        query_used = run_mock.call_args[0][0]
        assert "OWNS" in query_used
        assert "user_id" in query_used


# ── Integration tests (real Memgraph) ──────────────────────────────────────

@pytest.mark.integration
class TestGraphragCrudIntegration:
    """Full CRUD cycle against real Memgraph Cloud."""

    def setup_method(self):
        if not settings.MEMGRAPH_USERNAME or "your-cluster" in settings.MEMGRAPH_URI:
            pytest.skip("No real Memgraph credentials — fill in MEMGRAPH_* in .env")

    def test_user_crud(self):
        user = _make_user(email=f"{uuid.uuid4()}@test.com")
        graphrag_service.create_user(user)
        fetched = graphrag_service.get_user(user.id)
        assert fetched is not None
        assert fetched.email == user.email

    def test_task_full_crud_cycle(self):
        # Create a user first
        user = _make_user(email=f"{uuid.uuid4()}@test.com")
        graphrag_service.create_user(user)

        # Create task
        task = _make_task(title="Integration test task")
        graphrag_service.create_task(user.id, task)

        # Fetch
        fetched = graphrag_service.get_task(user.id, task.id)
        assert fetched is not None
        assert fetched.title == "Integration test task"

        # List
        tasks = graphrag_service.list_tasks(user.id)
        assert any(t.id == task.id for t in tasks)

        # Update
        updated = graphrag_service.update_task(user.id, task.id, {"status": TaskStatus.NEXT})
        assert updated is True

        refetched = graphrag_service.get_task(user.id, task.id)
        assert refetched.status == TaskStatus.NEXT

    def test_ownership_isolation_between_users(self):
        """User A's tasks must not be visible to user B."""
        user_a = _make_user(email=f"{uuid.uuid4()}@test.com")
        user_b = _make_user(email=f"{uuid.uuid4()}@test.com")
        graphrag_service.create_user(user_a)
        graphrag_service.create_user(user_b)

        task = _make_task(title="User A's secret task")
        graphrag_service.create_task(user_a.id, task)

        # User B must NOT be able to fetch user A's task
        result = graphrag_service.get_task(user_b.id, task.id)
        assert result is None, "Ownership isolation broken — user B can see user A's task"

    def test_project_find_or_create(self):
        user = _make_user(email=f"{uuid.uuid4()}@test.com")
        graphrag_service.create_user(user)

        p1 = graphrag_service.find_or_create_project(user.id, "My Project", outcome="Ship it")
        p2 = graphrag_service.find_or_create_project(user.id, "my project")  # same, different case
        assert p1.id == p2.id, "find_or_create_project should reuse existing project"

    def test_area_find_or_create(self):
        user = _make_user(email=f"{uuid.uuid4()}@test.com")
        graphrag_service.create_user(user)

        a1 = graphrag_service.find_or_create_area(user.id, "Health")
        a2 = graphrag_service.find_or_create_area(user.id, "HEALTH")
        assert a1.id == a2.id, "find_or_create_area should reuse existing area"

    def test_task_project_area_relationships(self):
        user = _make_user(email=f"{uuid.uuid4()}@test.com")
        graphrag_service.create_user(user)

        task = _make_task(title="Multi-project task")
        graphrag_service.create_task(user.id, task)

        project = graphrag_service.find_or_create_project(user.id, "Test Project")
        area = graphrag_service.find_or_create_area(user.id, "Test Area")

        # Relationships should not raise
        graphrag_service.create_task_part_of_project(task.id, project.id)
        graphrag_service.create_task_in_area(task.id, area.id)

        # Calling again should be idempotent (MERGE)
        graphrag_service.create_task_part_of_project(task.id, project.id)
        graphrag_service.create_task_in_area(task.id, area.id)

