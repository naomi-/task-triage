"""
Tests for embeddings_service.

Unit tests use the mock_voyage fixture (no real API call needed).
Integration smoke test (marked 'integration') requires VOYAGE_API_KEY in .env.
"""

import pytest
from django.conf import settings


# ── Unit tests (always run, no credentials needed) ────────────────────────────

@pytest.mark.django_db
def test_ping_returns_ok_with_mock(mock_voyage):
    """ping() should return {"ok": True, model: "voyage-3", dim: 1024} when mocked."""
    from core.services.embeddings_service import ping

    result = ping()

    assert result["ok"] is True
    assert result["model"] == "voyage-3"
    assert result["dim"] == 1024


@pytest.mark.django_db
def test_embed_documents_returns_correct_shape(mock_voyage):
    """embed_documents() should return one vector per input text."""
    from core.services.embeddings_service import embed_documents

    texts = ["hello world", "buy milk", "fix the CI"]
    vectors = embed_documents(texts)

    assert len(vectors) == 3
    assert all(len(v) == 1024 for v in vectors)


@pytest.mark.django_db
def test_embed_query_returns_single_vector(mock_voyage):
    """embed_query() should return a single 1024-dim vector."""
    from core.services.embeddings_service import embed_query

    vector = embed_query("what tasks are urgent?")

    assert isinstance(vector, list)
    assert len(vector) == 1024


# ── Integration smoke test (requires real Voyage AI API key) ──────────────────

@pytest.mark.integration
@pytest.mark.django_db
def test_ping_real_voyage():
    """
    Smoke test: call real Voyage AI API and confirm 1024-dim vector.

    Run with:  pytest -m integration
    Requires:  VOYAGE_API_KEY in .env
    """
    if not settings.VOYAGE_API_KEY:
        pytest.skip("VOYAGE_API_KEY not set — add it to .env")

    from core.services.embeddings_service import ping

    result = ping()

    assert result["ok"] is True
    assert result["dim"] == 1024
    print(f"\nVoyage AI connected: model={result['model']}, dim={result['dim']}")

