"""
dtos.py — Plain Python dataclasses mirroring each Memgraph node type.

These are lightweight data transfer objects used throughout the service layer.
They are NOT Django ORM models — there is no SQL table behind them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── Enums (stored as strings in Memgraph) ─────────────────────────────────────

class TaskStatus:
    INBOX = "INBOX"
    NEXT = "NEXT"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    SOMEDAY = "SOMEDAY"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"
    VALUES = {INBOX, NEXT, IN_PROGRESS, WAITING, SOMEDAY, DONE, ARCHIVED}


class TaskEffort:
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    VALUES = {XS, S, M, L, XL}


class EnergySignal:
    """
    How this task feels energetically.  Inspired by the KonMari principle of
    noticing whether something sparks joy — extended here to a three-point
    scale across positive, neutral, and draining tasks.
    """
    JOY = "JOY"
    NEUTRAL = "NEUTRAL"
    DRAIN = "DRAIN"
    VALUES = {JOY, NEUTRAL, DRAIN}


class ProjectStatus:
    ACTIVE = "ACTIVE"
    DONE = "DONE"
    SOMEDAY = "SOMEDAY"
    ARCHIVED = "ARCHIVED"
    VALUES = {ACTIVE, DONE, SOMEDAY, ARCHIVED}


# ── Node dataclasses ───────────────────────────────────────────────────────────

@dataclass
class UserNode:
    id: str
    email: str
    created_at: datetime
    preferences_json: str = "{}"


@dataclass
class TaskNode:
    id: str
    title: str
    status: str                          # TaskStatus value
    priority: int                        # 1–5
    urgency: int                         # 1–5
    effort: str                          # TaskEffort value
    created_at: datetime
    updated_at: datetime
    embedding_model: str = "voyage-3"
    description: str = ""
    next_action: Optional[str] = None
    due_date: Optional[datetime] = None
    energy_signal: Optional[str] = None   # EnergySignal value (JOY / NEUTRAL / DRAIN)
    embedding: Optional[list[float]] = None


@dataclass
class ProjectNode:
    id: str
    name: str
    outcome: str
    status: str = ProjectStatus.ACTIVE   # ProjectStatus value


@dataclass
class AreaNode:
    id: str
    name: str


@dataclass
class ResourceNode:
    id: str
    name: str
    type: str
    url: Optional[str] = None


@dataclass
class TriageSessionNode:
    id: str
    created_at: datetime
    input_text: str
    model: str
    prompt_version: str


@dataclass
class SuggestionNode:
    id: str
    created_at: datetime
    suggestion_type: str
    payload_json: str
    accepted_bool: Optional[bool] = None

