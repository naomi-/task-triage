"""
views.py — Cozy Triage view layer.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.forms import SignupForm
from core.services import graphrag_service
from core.dtos import UserNode, TaskStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

def signup(request):
    """
    Create a Django user + matching Memgraph User node.
    On success, log the user in and redirect to dashboard.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            django_user = form.save()
            # Sync to Memgraph — use Django's pk as the graph node id
            node = UserNode(
                id=str(django_user.pk),
                email=django_user.email,
                created_at=datetime.now(timezone.utc),
            )
            try:
                graphrag_service.create_user(node)
            except Exception:
                logger.exception(
                    "Memgraph User node creation failed for pk=%s", django_user.pk
                )
                # Don't block login — node sync can be retried; user exists in Django
            login(request, django_user)
            return redirect("dashboard")
    else:
        form = SignupForm()

    return render(request, "core/signup.html", {"form": form})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    """
    Home view — shows top Next Actions and a quick-add input.
    """
    user_id = str(request.user.pk)
    next_tasks = []
    inbox_count = 0

    try:
        next_tasks = graphrag_service.list_tasks(user_id, status=TaskStatus.NEXT)[:5]
        inbox_tasks = graphrag_service.list_tasks(user_id, status=TaskStatus.INBOX)
        inbox_count = len(inbox_tasks)
    except Exception:
        logger.exception("Failed to load dashboard tasks for user %s", user_id)

    return render(request, "core/dashboard.html", {
        "next_tasks": next_tasks,
        "inbox_count": inbox_count,
    })
