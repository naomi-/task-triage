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
]

