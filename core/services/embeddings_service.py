"""
embeddings_service.py — Voyage AI embedding utilities.

Model: voyage-3 → 1024-dimensional float vectors.
"""

from __future__ import annotations

import voyageai
from django.conf import settings

_MODEL = "voyage-3"
_EXPECTED_DIM = 1024


def _get_client() -> voyageai.Client:
    return voyageai.Client(api_key=settings.VOYAGE_API_KEY)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of document strings.

    Returns a list of 1024-dimensional float vectors (one per input text).
    """
    client = _get_client()
    result = client.embed(texts, model=_MODEL, input_type="document")
    return result.embeddings


def embed_query(text: str) -> list[float]:
    """
    Embed a single query string.

    Returns a single 1024-dimensional float vector.
    """
    client = _get_client()
    result = client.embed([text], model=_MODEL, input_type="query")
    return result.embeddings[0]


def ping() -> dict:
    """
    Smoke-test the Voyage AI connection.

    Embeds a short sentinel string and confirms the vector has the expected
    dimensionality (1024).

    Returns:
        {"ok": True, "model": "voyage-3", "dim": 1024}

    Raises:
        AssertionError / Exception if the call fails or the dimension is wrong.
    """
    vector = embed_query("ping")
    assert len(vector) == _EXPECTED_DIM, (
        f"Expected {_EXPECTED_DIM}-dim vector, got {len(vector)}"
    )
    return {"ok": True, "model": _MODEL, "dim": len(vector)}

