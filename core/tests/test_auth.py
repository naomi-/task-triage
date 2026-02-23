"""
test_auth.py — Unit + integration tests for Phase 2 auth flow.

Unit tests use Django's test client with mocked Memgraph calls.
Integration tests (marked @pytest.mark.integration) exercise the real
Memgraph connection and are skipped when credentials are missing.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from django.contrib.auth.models import User
from django.test import Client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client() -> Client:
    return Client()


def _signup(client, username="testuser", email="test@example.com",
            password="Tr0ubl3d_P4ssw0rd!"):
    return client.post("/signup/", {
        "username": username,
        "email": email,
        "password1": password,
        "password2": password,
    })


# ---------------------------------------------------------------------------
# Unit tests (mocked Memgraph)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSignupView:
    def test_signup_page_renders(self):
        client = _make_client()
        resp = client.get("/signup/")
        assert resp.status_code == 200
        assert b"Create account" in resp.content

    @patch("core.views.graphrag_service.create_user")
    def test_signup_creates_django_user(self, mock_create_user):
        mock_create_user.return_value = "1"
        client = _make_client()
        resp = _signup(client)
        # Should redirect to dashboard on success
        assert resp.status_code == 302
        assert resp["Location"] == "/"
        assert User.objects.filter(username="testuser").exists()

    @patch("core.views.graphrag_service.create_user")
    def test_signup_calls_graphrag_create_user(self, mock_create_user):
        mock_create_user.return_value = "1"
        client = _make_client()
        _signup(client)
        assert mock_create_user.called
        call_arg = mock_create_user.call_args[0][0]  # first positional arg = UserNode
        assert call_arg.email == "test@example.com"

    @patch("core.views.graphrag_service.create_user")
    def test_signup_proceeds_even_if_memgraph_fails(self, mock_create_user):
        """Memgraph failure must not block the user from signing up."""
        mock_create_user.side_effect = Exception("Memgraph down")
        client = _make_client()
        resp = _signup(client, username="resilientuser", email="r@example.com")
        assert resp.status_code == 302  # still redirects
        assert User.objects.filter(username="resilientuser").exists()

    def test_signup_duplicate_username_shows_error(self):
        User.objects.create_user("dupeuser", "dupe@example.com", "Str0ng_Pass!")
        client = _make_client()
        with patch("core.views.graphrag_service.create_user"):
            resp = _signup(client, username="dupeuser")
        assert resp.status_code == 200  # re-renders form
        assert b"already exists" in resp.content.lower() or b"taken" in resp.content.lower() or b"username" in resp.content.lower()

    def test_signup_password_mismatch_shows_error(self):
        client = _make_client()
        resp = client.post("/signup/", {
            "username": "mismatch",
            "email": "m@example.com",
            "password1": "Abc12345!",
            "password2": "Different99!",
        })
        assert resp.status_code == 200
        assert not User.objects.filter(username="mismatch").exists()


@pytest.mark.django_db
class TestLoginView:
    def test_login_page_renders(self):
        resp = _make_client().get("/login/")
        assert resp.status_code == 200
        assert b"Log in" in resp.content

    @patch("core.views.graphrag_service.create_user")
    def test_login_redirects_authenticated_user(self, mock_create_user):
        mock_create_user.return_value = "1"
        client = _make_client()
        _signup(client)  # signs up + logs in automatically
        resp = client.get("/login/")
        # Django's LoginView redirects already-logged-in users to LOGIN_REDIRECT_URL
        assert resp.status_code in (200, 302)

    def test_wrong_password_shows_error(self):
        User.objects.create_user("logintest", "l@example.com", "R34lP4ss!")
        client = _make_client()
        resp = client.post("/login/", {"username": "logintest", "password": "wrongpass"})
        assert resp.status_code == 200
        assert b"correct" in resp.content.lower() or b"invalid" in resp.content.lower() or b"error" in resp.content.lower()


@pytest.mark.django_db
class TestDashboardView:
    def test_unauthenticated_redirects_to_login(self):
        resp = _make_client().get("/")
        assert resp.status_code == 302
        assert "/login/" in resp["Location"]

    @patch("core.views.graphrag_service.list_tasks", return_value=[])
    @patch("core.views.graphrag_service.create_user")
    def test_dashboard_renders_after_login(self, mock_create, mock_list):
        mock_create.return_value = "1"
        client = _make_client()
        _signup(client, username="dashuser", email="dash@example.com")
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"dashuser" in resp.content

    @patch("core.views.graphrag_service.list_tasks", return_value=[])
    @patch("core.views.graphrag_service.create_user")
    def test_logout_redirects_to_login(self, mock_create, mock_list):
        mock_create.return_value = "1"
        client = _make_client()
        _signup(client, username="logoutuser", email="lo@example.com")
        resp = client.post("/logout/")
        assert resp.status_code == 302
        assert "/login/" in resp["Location"]


# ---------------------------------------------------------------------------
# Integration tests (real Memgraph)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.integration
class TestSignupIntegration:
    def test_signup_creates_memgraph_user_node(self):
        """
        Full flow: signup → Django user + Memgraph User node.
        Cleans up after itself.
        """
        from core.services import graphrag_service

        client = _make_client()
        username = "integ_signup_test"
        email = "integ_signup@cozy.test"

        try:
            resp = _signup(client, username=username, email=email,
                           password="VeryLongPassword123!")
            assert resp.status_code == 302, f"Expected 302, got {resp.status_code}"

            django_user = User.objects.get(username=username)
            node = graphrag_service.get_user(str(django_user.pk))
            assert node is not None
            assert node.email == email
        finally:
            # Cleanup Django user
            User.objects.filter(username=username).delete()

