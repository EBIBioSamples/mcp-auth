import httpx
import pytest

from unittest.mock import AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.controller.web_in_controller import router, auth_service

class FakeAsyncClient:
    def __init__(self, response=None, error=None, *args, **kwargs):
        self.response = response
        self.error = error
        self.post_args = None
        self.post_kwargs = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        self.post_args = args
        self.post_kwargs = kwargs
        if self.error:
            raise self.error
        return self.response

@pytest.fixture
def client():
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(router)
    return TestClient(app)

def test_home_redirects_to_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"

def test_login_page_returns_200(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "login" in response.text.lower()

def test_successful_login_caches_token_and_redirects(monkeypatch, client):
    webin_response = httpx.Response(
        status_code=200,
        text="jwt-token-123",
        request=httpx.Request("POST", "https://example.test/token"),

    )

    post_mock = AsyncMock(return_value=webin_response)

    monkeypatch.setattr(
        auth_service.http_client,
        "post",
        post_mock,
    )

    cache_token = AsyncMock()
    monkeypatch.setattr(auth_service.redis_config, "cache_token", cache_token)

    response = client.post(
        "/login",
        data={"username": "  test-user  ", "password": "secret"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    cache_token.assert_awaited_once_with(
        username="test-user",
        response="jwt-token-123",
    )

def test_success_message_is_shown_once_after_redirect(monkeypatch, client):
    webin_response = httpx.Response(
        status_code=200,
        text="jwt-token-123",
        request=httpx.Request("POST", "https://example.test/token"),
    )

    post_mock = AsyncMock(return_value=webin_response)

    monkeypatch.setattr(
        auth_service.http_client,
        "post",
        post_mock,
    )

    monkeypatch.setattr(auth_service.redis_config, "cache_token", AsyncMock())

    response = client.post(
        "/login",
        data={"username": "test-user", "password": "secret"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "successfully logged in" in response.text.lower()

    second_response = client.get("/login")
    assert "successfully logged in" not in second_response.text.lower()

def test_empty_webin_response_returns_credentials_error(monkeypatch, client):
    webin_response = httpx.Response(
        status_code=200,
        text="",
        request=httpx.Request("POST", "https://example.test/token"),
    )

    post_mock = AsyncMock(return_value=webin_response)

    monkeypatch.setattr(
        auth_service.http_client,
        "post",
        post_mock,
    )

    cache_token = AsyncMock()
    monkeypatch.setattr(auth_service.redis_config, "cache_token", cache_token)

    response = client.post(
        "/login",
        data={"username": "wrong-user", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "wrong credentials" in response.text.lower()
    cache_token.assert_not_awaited()

def test_webin_connection_error_returns_502(monkeypatch, client):
    request = httpx.Request("POST", "https://example.test/token")
    error = httpx.ConnectError("connection failed", request=request)

    post_mock = AsyncMock(side_effect = error)

    monkeypatch.setattr(
        auth_service.http_client,
        "post",
        post_mock,
    )

    response = client.post(
        "/login",
        data={"username": "test-user", "password": "secret"},
    )

    assert response.status_code == 502
    assert "unable to connect to webin" in response.text.lower()