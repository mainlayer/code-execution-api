import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("MAINLAYER_API_KEY", "test-key")
os.environ.setdefault("MAINLAYER_RESOURCE_ID", "test-resource")


def _make_app():
    with patch("mainlayer.MainlayerClient"):
        from src.main import app
        return app


@pytest.fixture()
def authorized_client():
    app = _make_app()
    access_mock = MagicMock()
    access_mock.authorized = True
    with patch("src.main.ml") as ml_mock:
        ml_mock.resources.verify_access = AsyncMock(return_value=access_mock)
        with TestClient(app) as client:
            yield client


@pytest.fixture()
def unauthorized_client():
    app = _make_app()
    access_mock = MagicMock()
    access_mock.authorized = False
    with patch("src.main.ml") as ml_mock:
        ml_mock.resources.verify_access = AsyncMock(return_value=access_mock)
        with TestClient(app) as client:
            yield client


def test_health():
    app = _make_app()
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200


def test_execute_python_authorized(authorized_client):
    resp = authorized_client.post(
        "/execute",
        json={"code": 'print("hello")', "language": "python"},
        headers={"x-mainlayer-token": "valid-token"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "hello" in data["stdout"]
    assert data["credits_used"] == 1
    assert data["exit_code"] == 0


def test_execute_unauthorized(unauthorized_client):
    resp = unauthorized_client.post(
        "/execute",
        json={"code": 'print("hello")', "language": "python"},
        headers={"x-mainlayer-token": "bad-token"},
    )
    assert resp.status_code == 402


def test_execute_missing_token():
    app = _make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/execute",
            json={"code": 'print("hello")', "language": "python"},
        )
    assert resp.status_code == 422


def test_execute_unsupported_language(authorized_client):
    resp = authorized_client.post(
        "/execute",
        json={"code": 'puts "hello"', "language": "ruby"},
        headers={"x-mainlayer-token": "valid-token"},
    )
    assert resp.status_code == 400


def test_execute_timeout_respected(authorized_client):
    resp = authorized_client.post(
        "/execute",
        json={"code": "import time; time.sleep(5)", "language": "python", "timeout": 1},
        headers={"x-mainlayer-token": "valid-token"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["timed_out"] is True
