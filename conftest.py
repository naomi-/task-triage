"""
Root conftest.py — shared pytest fixtures for the whole project.

Fixtures that mock external APIs (Memgraph, Voyage AI, Anthropic) live here so
every test module can use them without importing anything extra.
"""

import pytest


@pytest.fixture
def mock_voyage(monkeypatch):
    """Replace Voyage AI embed calls with a deterministic 1024-dim zero vector."""
    import core.services.embeddings_service as svc

    fake_vector = [0.0] * 1024

    def _fake_embed(texts, model, input_type):
        class _Result:
            embeddings = [fake_vector for _ in texts]

        return _Result()

    monkeypatch.setattr(svc, "_get_client", lambda: type("C", (), {"embed": staticmethod(_fake_embed)})())
    return fake_vector


@pytest.fixture
def mock_memgraph(monkeypatch):
    """
    Replace the Memgraph driver with a MagicMock.

    Returns the driver mock so tests can configure what session.run() returns:

        mock_memgraph.session.return_value.__enter__.return_value \\
            .run.return_value.single.return_value = {"t": {...}}
    """
    from unittest.mock import MagicMock
    import core.services.graphrag_service as svc

    driver_mock = MagicMock()

    # Default: single() returns {"n": 1} (keeps the ping test working)
    (
        driver_mock.session.return_value
        .__enter__.return_value
        .run.return_value
        .single.return_value
    ) = {"n": 1}

    # Default: iterating the result returns an empty list (list_tasks etc.)
    (
        driver_mock.session.return_value
        .__enter__.return_value
        .run.return_value
        .__iter__
    ) = lambda self: iter([])

    monkeypatch.setattr(svc, "_get_driver", lambda: driver_mock)
    return driver_mock

