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
    """Replace the Memgraph driver with a no-op stub."""
    import core.services.graphrag_service as svc

    class _FakeSession:
        def run(self, query, **params):
            class _Result:
                def single(self):
                    return {"n": 1}
                def data(self):
                    return []
            return _Result()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    class _FakeDriver:
        def session(self):
            return _FakeSession()
        def close(self):
            pass

    monkeypatch.setattr(svc, "_get_driver", lambda: _FakeDriver())

