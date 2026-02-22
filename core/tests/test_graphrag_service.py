"""
Tests for graphrag_service.

Unit tests use the mock_memgraph fixture (no real connection needed).
Integration smoke test (marked 'integration') requires MEMGRAPH_* env vars.
"""

import pytest
from django.conf import settings


# ── Unit tests (always run, no credentials needed) ────────────────────────────

@pytest.mark.django_db
def test_ping_returns_ok_with_mock(mock_memgraph):
    """ping() should return {"ok": True, ...} when the driver is mocked."""
    from core.services.graphrag_service import ping

    result = ping()

    assert result["ok"] is True
    assert "server" in result


# ── Integration smoke test (requires real Memgraph credentials) ───────────────

@pytest.mark.integration
@pytest.mark.django_db
def test_ping_real_connection():
    """
    Smoke test: connect to a real Memgraph instance.

    Run with:  pytest -m integration
    Requires:  MEMGRAPH_URI, MEMGRAPH_USERNAME, MEMGRAPH_PASSWORD in .env
    """
    if not settings.MEMGRAPH_USERNAME or "your-cluster" in settings.MEMGRAPH_URI:
        pytest.skip("No real Memgraph credentials configured — fill in MEMGRAPH_* in .env")

    from core.services.graphrag_service import ping

    result = ping()

    assert result["ok"] is True
    print(f"\nMemgraph connected: {result['server']}")

