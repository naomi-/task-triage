"""
graphrag_service.py — Memgraph / graph-database utilities.

All public functions that read data MUST include the ownership filter:
    MATCH (u:User {id: $user_id})-[:OWNS]->...
"""

from __future__ import annotations

from django.conf import settings
from neo4j import GraphDatabase, Driver


def _get_driver() -> Driver:
    """Return a connected Neo4j/Bolt driver for Memgraph."""
    return GraphDatabase.driver(
        settings.MEMGRAPH_URI,
        auth=(settings.MEMGRAPH_USERNAME, settings.MEMGRAPH_PASSWORD),
    )


def ping() -> dict:
    """
    Smoke-test the Memgraph connection.

    Returns:
        {"ok": True, "server": "<Memgraph version string>"}

    Raises:
        Exception if the connection or query fails.
    """
    driver = _get_driver()
    with driver.session() as session:
        result = session.run("RETURN 1 AS n")
        record = result.single()
        assert record["n"] == 1, "Unexpected response from Memgraph"
    driver.close()
    return {"ok": True, "server": settings.MEMGRAPH_URI}

