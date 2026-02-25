"""
core/urls.py — URL patterns for the core app.
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from core import views

urlpatterns = [
    # Dashboard (home)
    path("", views.dashboard, name="dashboard"),

    # Auth
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # Triage Pipeline
    path("inbox/", views.inbox, name="inbox"),
    path("triage/<str:session_id>/", views.triage_review, name="triage_review"),
    
    # Tasks
    path("tasks/", views.tasks, name="tasks"),

    # JSON API
    path("api/inbox/", views.api_inbox, name="api_inbox"),
    path("api/triage/apply/", views.api_triage_apply, name="api_triage_apply"),
    path("api/triage/<str:session_id>/", views.api_triage_suggestions, name="api_triage_suggestions"),
    path("api/tasks/", views.api_tasks, name="api_tasks"),
    path("api/projects/", views.api_projects, name="api_projects"),
    path("api/projects/<str:project_id>/", views.api_project_detail, name="api_project_detail"),
    path("api/tasks/<str:task_id>/status/", views.api_task_status, name="api_task_status"),
]
