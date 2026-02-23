"""
Tests for Triage UI (Inbox, Review, apply).
"""

import json
from unittest.mock import patch
import pytest
from django.urls import reverse
from core.dtos import TaskNode, ProjectNode, AreaNode, UserNode

# Mark all tests to use the db
pytestmark = pytest.mark.django_db


def test_inbox_get(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    client.force_login(user)
    
    url = reverse("inbox")
    response = client.get(url)
    assert response.status_code == 200
    assert "What's on your mind?" in response.content.decode()


def test_inbox_post_empty(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    client.force_login(user)
    
    url = reverse("inbox")
    response = client.post(url, {"brain_dump": "   "})
    assert response.status_code == 200
    assert "Please enter what&#x27;s on your mind." in response.content.decode()


@patch("core.services.llm_service.triage_brain_dump")
@patch("core.services.embeddings_service.embed_query")
def test_inbox_post_success(mock_embed, mock_triage, client, django_user_model, monkeypatch):
    """
    Test submitting a brain dump creates a session and redirects to triage_review.
    We need to mock the graph user creation since login needs a Memgraph user.
    """
    from core.services import graphrag_service
    from datetime import datetime, timezone
    
    user = django_user_model.objects.create_user(username="testuser3", email="test3@test.com", password="password")
    # create graph node
    graphrag_service.create_user(UserNode(id=str(user.pk), email="test3@test.com", created_at=datetime.now(timezone.utc)))
    
    client.force_login(user)
    
    mock_embed.return_value = [0.1] * 1024
    mock_triage.return_value = {
        "items": [
            {
                "action_title": "Buy milk",
                "status": "INBOX",
                "priority": 3,
                "urgency": 2,
                "effort": "XS",
                "description": "",
            }
        ]
    }
    
    url = reverse("inbox")
    response = client.post(url, {"brain_dump": "I need to buy milk"})
    
    assert response.status_code == 302
    assert "triage/" in response.url
    
    # Check session was created
    session_id = response.url.split("/")[-2]
    session = graphrag_service.get_triage_session(str(user.pk), session_id)
    assert session is not None
    assert session.input_text == "I need to buy milk"
    
    
@patch("core.services.embeddings_service.embed_query")
def test_apply_suggestions(mock_embed, client, django_user_model):
    """
    Test the POST action on triage_review applies suggestions and creates tasks.
    """
    from core.services import graphrag_service, triage_service
    from core.dtos import TriageSessionNode, SuggestionNode
    from datetime import datetime, timezone
    import uuid
    
    mock_embed.return_value = [0.1] * 1024
    
    user = django_user_model.objects.create_user(username="testuser2", email="test2@test.com", password="password")
    user_id = str(user.pk)
    graphrag_service.create_user(UserNode(id=user_id, email="test2@test.com", created_at=datetime.now(timezone.utc)))
    
    session_id = str(uuid.uuid4())
    graphrag_service.create_triage_session(user_id, TriageSessionNode(
        id=session_id, input_text="dump", model="test", prompt_version="v1", created_at=datetime.now(timezone.utc)
    ))
    
    sug1_id = str(uuid.uuid4())
    graphrag_service.create_suggestion(user_id, session_id, SuggestionNode(
        id=sug1_id,
        created_at=datetime.now(timezone.utc),
        suggestion_type="triage_item",
        payload_json=json.dumps({"action_title": "Original Title", "status": "INBOX", "priority": 3, "urgency": 3, "effort": "M"})
    ))
    
    sug2_id = str(uuid.uuid4())
    graphrag_service.create_suggestion(user_id, session_id, SuggestionNode(
        id=sug2_id,
        created_at=datetime.now(timezone.utc),
        suggestion_type="triage_item",
        payload_json=json.dumps({"action_title": "To be rejected", "status": "INBOX", "priority": 1, "urgency": 1, "effort": "S"})
    ))
    
    client.force_login(user)
    
    url = reverse("triage_review", args=[session_id])
    
    # Payload accepts sug1 with edits, rejects sug2
    decisions = [
        {"id": sug1_id, "action": "accept", "edited_data": {"action_title": "Edited Title", "status": "NEXT", "project_suggestions": ["New Project"]}},
        {"id": sug2_id, "action": "reject"}
    ]
    
    response = client.post(url, {"decisions": json.dumps(decisions)})
    assert response.status_code == 302
    assert response.url == reverse("tasks")
    
    # Verify DB state
    tasks = graphrag_service.list_tasks(user_id)
    assert any(t.title == "Edited Title" and t.status == "NEXT" for t in tasks)
    
    projs = graphrag_service.list_projects(user_id)
    assert any(p.name == "New Project" for p in projs)
    
    sugs = graphrag_service.get_suggestions_for_session(user_id, session_id)
    for s in sugs:
        if s.id == sug1_id:
            assert s.accepted_bool is True
        elif s.id == sug2_id:
            assert s.accepted_bool is False
