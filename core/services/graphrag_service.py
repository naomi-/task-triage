"""
graphrag_service.py — Memgraph / graph-database utilities.

SECURITY RULE: Every function that reads user-owned data MUST include the
ownership filter:
    MATCH (u:User {id: $user_id})-[:OWNS]->...
No exceptions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from django.conf import settings
from neo4j import GraphDatabase, Driver

from core.dtos import (
    UserNode,
    TaskNode,
    ProjectNode,
    AreaNode,
    TriageSessionNode,
    SuggestionNode,
)


# ---------------------------------------------------------------------------
# Driver helpers
# ---------------------------------------------------------------------------

_driver_instance = None

def _get_driver() -> Driver:
    """Return a connected Neo4j/Bolt driver for Memgraph."""
    global _driver_instance
    if _driver_instance is None:
        _driver_instance = GraphDatabase.driver(
            settings.MEMGRAPH_URI,
            auth=(settings.MEMGRAPH_USERNAME, settings.MEMGRAPH_PASSWORD),
            max_connection_lifetime=300, # 5 min
            max_connection_pool_size=50,
            connection_acquisition_timeout=30.0
        )
    return _driver_instance


def ping() -> dict:
    """
    Smoke-test the Memgraph connection.

    Returns:
        {"ok": True, "server": "<Memgraph URI>"}

    Raises:
        Exception if the connection or query fails.
    """
    driver = _get_driver()
    with driver.session() as session:
        result = session.run("RETURN 1 AS n")
        record = result.single()
        assert record["n"] == 1, "Unexpected response from Memgraph"
    return {"ok": True, "server": settings.MEMGRAPH_URI}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _dt(value) -> Optional[datetime]:
    """Convert a neo4j temporal type or None to a Python datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def create_user(user: UserNode) -> str:
    """
    Persist a User node.  Returns the node id.
    """
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            """
            MERGE (u:User {id: $id})
            SET u.email        = $email,
                u.created_at   = $created_at,
                u.preferences_json = $preferences_json
            """,
            id=user.id,
            email=user.email,
            created_at=user.created_at.isoformat(),
            preferences_json=user.preferences_json,
        )
    return user.id


def get_user(user_id: str) -> Optional[UserNode]:
    """Return the User node with the given id, or None."""
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {id: $id}) RETURN u",
            id=user_id,
        )
        record = result.single()
    if record is None:
        return None
    u = record["u"]
    return UserNode(
        id=u["id"],
        email=u["email"],
        created_at=_dt(u.get("created_at")),
        preferences_json=u.get("preferences_json", "{}"),
    )


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------

def _task_from_record(t) -> TaskNode:
    return TaskNode(
        id=t["id"],
        title=t["title"],
        status=t["status"],
        priority=t["priority"],
        urgency=t["urgency"],
        effort=t["effort"],
        created_at=_dt(t.get("created_at")),
        updated_at=_dt(t.get("updated_at")),
        embedding_model=t.get("embedding_model", "voyage-3"),
        description=t.get("description", ""),
        next_action=t.get("next_action"),
        due_date=_dt(t.get("due_date")),
        energy_signal=t.get("energy_signal"),
        embedding=list(t["embedding"]) if t.get("embedding") is not None else None,
    )


def create_task(user_id: str, task: TaskNode) -> str:
    """
    Persist a Task node and create the OWNS relationship.
    Returns the task id.

    Ownership: (User)-[:OWNS]->(Task)
    """
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            """
            MATCH (u:User {id: $user_id})
            CREATE (t:Task {
                id:              $id,
                title:           $title,
                description:     $description,
                next_action:     $next_action,
                status:          $status,
                priority:        $priority,
                urgency:         $urgency,
                effort:          $effort,
                due_date:        $due_date,
                energy_signal:   $energy_signal,
                created_at:      $created_at,
                updated_at:      $updated_at,
                embedding_model: $embedding_model,
                embedding:       $embedding
            })
            CREATE (u)-[:OWNS]->(t)
            """,
            user_id=user_id,
            id=task.id,
            title=task.title,
            description=task.description,
            next_action=task.next_action,
            status=task.status,
            priority=task.priority,
            urgency=task.urgency,
            effort=task.effort,
            due_date=task.due_date.isoformat() if task.due_date else None,
            energy_signal=task.energy_signal,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            embedding_model=task.embedding_model,
            embedding=task.embedding,
        )
    return task.id


def get_task(user_id: str, task_id: str) -> Optional[TaskNode]:
    """
    Return the Task owned by user_id with the given task_id, or None.
    Ownership filter enforced.
    """
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(t:Task {id: $task_id})
            RETURN t
            """,
            user_id=user_id,
            task_id=task_id,
        )
        record = result.single()
    if record is None:
        return None
    return _task_from_record(record["t"])


def list_tasks(user_id: str, status: Optional[str] = None) -> list[TaskNode]:
    """
    Return all Tasks owned by user_id, optionally filtered by status.
    Ownership filter enforced.
    """
    driver = _get_driver()
    with driver.session() as session:
        if status:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:OWNS]->(t:Task {status: $status})
                RETURN t ORDER BY t.created_at DESC
                """,
                user_id=user_id,
                status=status,
            )
        else:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:OWNS]->(t:Task)
                RETURN t ORDER BY t.created_at DESC
                """,
                user_id=user_id,
            )
        records = list(result)
    return [_task_from_record(r["t"]) for r in records]


def update_task(user_id: str, task_id: str, updates: dict) -> bool:
    """
    Update writable fields on a Task owned by user_id.
    Returns True if the task was found and updated, False otherwise.
    Ownership filter enforced.
    """
    updates["updated_at"] = _now().isoformat()
    set_clause = ", ".join(f"t.{k} = ${k}" for k in updates)
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            f"""
            MATCH (u:User {{id: $user_id}})-[:OWNS]->(t:Task {{id: $task_id}})
            SET {set_clause}
            RETURN t.id AS id
            """,
            user_id=user_id,
            task_id=task_id,
            **updates,
        )
        record = result.single()
    return record is not None


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

def find_or_create_project(user_id: str, name: str, outcome: str = "") -> ProjectNode:
    """
    Look up an existing Project owned by user_id with a matching name
    (case-insensitive).  Create one if not found.
    Returns the ProjectNode (new or existing).
    Ownership filter enforced on lookup.
    """
    from core.dtos import ProjectStatus

    driver = _get_driver()
    with driver.session() as session:
        # Lookup — ownership filter required
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Project)
            WHERE toLower(p.name) = toLower($name)
            RETURN p LIMIT 1
            """,
            user_id=user_id,
            name=name,
        )
        record = result.single()
        if record:
            p = record["p"]
            return ProjectNode(
                id=p["id"],
                name=p["name"],
                outcome=p.get("outcome", ""),
                status=p.get("status", ProjectStatus.ACTIVE),
            )
        # Create
        new_id = _new_id()
        session.run(
            """
            MATCH (u:User {id: $user_id})
            CREATE (p:Project {id: $id, name: $name, outcome: $outcome, status: $status})
            CREATE (u)-[:OWNS]->(p)
            """,
            user_id=user_id,
            id=new_id,
            name=name,
            outcome=outcome,
            status=ProjectStatus.ACTIVE,
        )
    return ProjectNode(id=new_id, name=name, outcome=outcome)


def list_projects(user_id: str) -> list[ProjectNode]:
    """Return all Projects owned by user_id. Ownership filter enforced."""
    from core.dtos import ProjectStatus

    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {id: $user_id})-[:OWNS]->(p:Project) RETURN p",
            user_id=user_id,
        )
        records = list(result)
    return [
        ProjectNode(
            id=r["p"]["id"],
            name=r["p"]["name"],
            outcome=r["p"].get("outcome", ""),
            status=r["p"].get("status", ProjectStatus.ACTIVE),
        )
        for r in records
    ]


# ---------------------------------------------------------------------------
# Area CRUD
# ---------------------------------------------------------------------------

def find_or_create_area(user_id: str, name: str) -> AreaNode:
    """
    Look up an existing Area owned by user_id (case-insensitive).
    Create one if not found.  Returns the AreaNode.
    Ownership filter enforced on lookup.
    """
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(a:Area)
            WHERE toLower(a.name) = toLower($name)
            RETURN a LIMIT 1
            """,
            user_id=user_id,
            name=name,
        )
        record = result.single()
        if record:
            a = record["a"]
            return AreaNode(id=a["id"], name=a["name"])
        new_id = _new_id()
        session.run(
            """
            MATCH (u:User {id: $user_id})
            CREATE (a:Area {id: $id, name: $name})
            CREATE (u)-[:OWNS]->(a)
            """,
            user_id=user_id,
            id=new_id,
            name=name,
        )
    return AreaNode(id=new_id, name=name)


def list_areas(user_id: str) -> list[AreaNode]:
    """Return all Areas owned by user_id. Ownership filter enforced."""
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {id: $user_id})-[:OWNS]->(a:Area) RETURN a",
            user_id=user_id,
        )
        records = list(result)
    return [AreaNode(id=r["a"]["id"], name=r["a"]["name"]) for r in records]


# ---------------------------------------------------------------------------
# TriageSession CRUD
# ---------------------------------------------------------------------------

def create_triage_session(user_id: str, session_node: TriageSessionNode) -> str:
    """Persist a TriageSession node with OWNS relationship. Returns the id."""
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            """
            MATCH (u:User {id: $user_id})
            CREATE (ts:TriageSession {
                id:             $id,
                created_at:     $created_at,
                input_text:     $input_text,
                model:          $model,
                prompt_version: $prompt_version
            })
            CREATE (u)-[:OWNS]->(ts)
            """,
            user_id=user_id,
            id=session_node.id,
            created_at=session_node.created_at.isoformat(),
            input_text=session_node.input_text,
            model=session_node.model,
            prompt_version=session_node.prompt_version,
        )
    return session_node.id


def get_triage_session(user_id: str, session_id: str) -> Optional[TriageSessionNode]:
    """Return the TriageSession owned by user_id, or None. Ownership filter enforced."""
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(ts:TriageSession {id: $session_id})
            RETURN ts
            """,
            user_id=user_id,
            session_id=session_id,
        )
        record = result.single()
    if record is None:
        return None
    ts = record["ts"]
    return TriageSessionNode(
        id=ts["id"],
        created_at=_dt(ts.get("created_at")),
        input_text=ts["input_text"],
        model=ts["model"],
        prompt_version=ts["prompt_version"],
    )


# ---------------------------------------------------------------------------
# Suggestion CRUD
# ---------------------------------------------------------------------------

def create_suggestion(
    user_id: str,
    session_id: str,
    suggestion: SuggestionNode,
) -> str:
    """
    Persist a Suggestion node.
    Creates: (User)-[:OWNS]->(Suggestion) and (TriageSession)-[:PRODUCED]->(Suggestion).
    Returns the suggestion id.
    """
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(ts:TriageSession {id: $session_id})
            CREATE (s:Suggestion {
                id:              $id,
                created_at:      $created_at,
                suggestion_type: $suggestion_type,
                payload_json:    $payload_json,
                accepted_bool:   $accepted_bool
            })
            CREATE (u)-[:OWNS]->(s)
            CREATE (ts)-[:PRODUCED]->(s)
            """,
            user_id=user_id,
            session_id=session_id,
            id=suggestion.id,
            created_at=suggestion.created_at.isoformat(),
            suggestion_type=suggestion.suggestion_type,
            payload_json=suggestion.payload_json,
            accepted_bool=suggestion.accepted_bool,
        )
    return suggestion.id


def get_suggestions_for_session(
    user_id: str, session_id: str
) -> list[SuggestionNode]:
    """Return all Suggestions for a session. Ownership filter enforced."""
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(ts:TriageSession {id: $session_id})
            MATCH (ts)-[:PRODUCED]->(s:Suggestion)
            RETURN s ORDER BY s.created_at ASC
            """,
            user_id=user_id,
            session_id=session_id,
        )
        records = list(result)
    return [
        SuggestionNode(
            id=r["s"]["id"],
            created_at=_dt(r["s"].get("created_at")),
            suggestion_type=r["s"]["suggestion_type"],
            payload_json=r["s"]["payload_json"],
            accepted_bool=r["s"].get("accepted_bool"),
        )
        for r in records
    ]


def update_suggestion_accepted(
    user_id: str, suggestion_id: str, accepted: bool
) -> bool:
    """Set accepted_bool on a Suggestion. Ownership filter enforced. Returns True if found."""
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(s:Suggestion {id: $suggestion_id})
            SET s.accepted_bool = $accepted
            RETURN s.id AS id
            """,
            user_id=user_id,
            suggestion_id=suggestion_id,
            accepted=accepted,
        )
        record = result.single()
    return record is not None


# ---------------------------------------------------------------------------
# Relationship helpers
# ---------------------------------------------------------------------------

def create_task_part_of_project(task_id: str, project_id: str) -> None:
    """Create (Task)-[:PART_OF]->(Project). Many-to-many; safe to call multiple times."""
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            """
            MATCH (t:Task {id: $task_id}), (p:Project {id: $project_id})
            MERGE (t)-[:PART_OF]->(p)
            """,
            task_id=task_id,
            project_id=project_id,
        )


def create_task_in_area(task_id: str, area_id: str) -> None:
    """Create (Task)-[:IN_AREA]->(Area). Many-to-many; safe to call multiple times."""
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            """
            MATCH (t:Task {id: $task_id}), (a:Area {id: $area_id})
            MERGE (t)-[:IN_AREA]->(a)
            """,
            task_id=task_id,
            area_id=area_id,
        )


def create_task_duplicate_of(task_id: str, existing_task_id: str) -> None:
    """Create (Task)-[:DUPLICATE_OF]->(existing Task)."""
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            """
            MATCH (t:Task {id: $task_id}), (e:Task {id: $existing_task_id})
            MERGE (t)-[:DUPLICATE_OF]->(e)
            """,
            task_id=task_id,
            existing_task_id=existing_task_id,
        )


# ---------------------------------------------------------------------------
# Vector similarity search
# ---------------------------------------------------------------------------

def find_similar_tasks(
    user_id: str,
    embedding: list[float],
    limit: int = 5,
) -> list[tuple[TaskNode, float]]:
    """
    Return up to `limit` Tasks similar to the given embedding vector, scoped
    to the user.  Results are (TaskNode, similarity_score) tuples ordered by
    descending similarity.

    Uses Memgraph's vector_search.search() procedure against the
    task_embedding_idx index, then filters by ownership.

    Ownership filter enforced.
    """
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            CALL vector_search.search("task_embedding_idx", $limit, $embedding)
            YIELD node, similarity
            WITH node AS t, similarity
            MATCH (u:User {id: $user_id})-[:OWNS]->(t)
            RETURN t, similarity
            ORDER BY similarity DESC
            """,
            user_id=user_id,
            limit=limit,
            embedding=embedding,
        )
        records = list(result)
    return [(_task_from_record(r["t"]), r["similarity"]) for r in records]

