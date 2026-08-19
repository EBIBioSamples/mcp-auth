import httpx
import pytest
import app.service.auth_service

from unittest.mock import AsyncMock, Mock
from fastapi import Request
from fastapi.responses import HTMLResponse
from redis.exceptions import RedisError
from app.service.auth_service import AuthService

class FakeAsyncClient:
    last_instance = None

    def __init__(self, response=None, error=None, *args, **kwargs):
        self.response = response
        self.error = error
        self.timeout = kwargs.get("timeout")
        self.post_args = None
        self.post_kwargs = None
        FakeAsyncClient.last_instance = self

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

def make_request(session=None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/login",
        "raw_path": b"/login",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "session": {} if session is None else session,
    }
    return Request(scope)

def response(text="jwt-token", status_code=200):
    return httpx.Response(
        status_code=status_code,
        text=text,
        request=httpx.Request("POST", "https://example.test/token"),
    )

def test_auth_service_constructs_redis_config():
    service = AuthService()
    assert service.redis_config is not None

def test_render_login_passes_expected_template_context(monkeypatch):
    request = make_request()
    expected = HTMLResponse("rendered", status_code=401)
    template_response = Mock(return_value=expected)

    monkeypatch.setattr(
        app.service.auth_service.templates,
        "TemplateResponse",
        template_response,
    )

    result = AuthService.render_login(
        request=request,
        error="bad login",
        message="message",
        username="alice",
        status_code=401,
    )

    assert result is expected
    template_response.assert_called_once_with(
        request=request,
        name="login.html",
        context={
            "error": "bad login",
            "username": "alice",
            "message": "message",
        },
        status_code=401,
    )

@pytest.mark.asyncio
async def test_webin_request_uses_trimmed_username_and_original_password(monkeypatch):
    service = AuthService()
    service.redis_config.cache_token = AsyncMock()

    webin_response = httpx.Response(
        status_code=200,
        text="jwt-token-123",
        request=httpx.Request("POST", "https://example.test/token"),

    )

    post_mock = AsyncMock(return_value= webin_response)

    monkeypatch.setattr(
        service.http_client,
        "post",
        post_mock,
    )

    request = make_request()

    result = await service.web_in_token(
        request=request,
        username="  alice  ",
        password=" secret password ",
    )

    assert result.status_code == 303

@pytest.mark.asyncio
async def test_successful_authentication_caches_exact_response(monkeypatch):
    service = AuthService()
    cache_token = AsyncMock()
    service.redis_config.cache_token = cache_token

    mock_response = httpx.Response(
        status_code=200,
        text="jwt-abc",
        request=httpx.Request(
            "POST",
            "https://example.test/token",
        ),
    )

    service.http_client.post = AsyncMock(
        return_value=mock_response
    )

    request = make_request()

    result = await service.web_in_token(request, "alice", "secret")

    cache_token.assert_awaited_once_with(username="alice", response="jwt-abc")
    assert request.session["message"].startswith("You are successfully logged in")
    assert result.status_code == 303
    assert result.headers["location"] == "/login"

@pytest.mark.asyncio
async def test_empty_response_does_not_cache_token(monkeypatch):
    service = AuthService()
    service.redis_config.cache_token = AsyncMock()

    mock_response = httpx.Response(
        status_code=200,
        text="",
        request=httpx.Request(
            "POST",
            "https://example.test/token",
        ),
    )

    service.http_client.post = AsyncMock(
        return_value=mock_response
    )

    monkeypatch.setattr(
        service,
        "render_login",
        Mock(return_value=HTMLResponse("wrong credentials", status_code=502)),
    )

    result = await service.web_in_token(make_request(), "alice", "bad")

    assert result.status_code == 502
    service.redis_config.cache_token.assert_not_awaited()

@pytest.mark.asyncio
async def test_webin_request_error_returns_502(monkeypatch):
    service = AuthService()
    request_obj = httpx.Request("POST", "https://example.test/token")
    error = httpx.ConnectError("failed", request=request_obj)
    post_mock = AsyncMock(side_effect=error)

    monkeypatch.setattr(
        service.http_client,
        "post",
        post_mock,
    )
    render_login = Mock(return_value=HTMLResponse("offline", status_code=502))
    monkeypatch.setattr(service, "render_login", render_login)
    request = make_request()

    result = await service.web_in_token(request, "alice", "secret")

    assert result.status_code == 502
    render_login.assert_called_once_with(
        request=request,
        error="Unable to connect to Webin.",
        username="alice",
        status_code=502,
    )

@pytest.mark.asyncio
async def test_cache_redis_error_is_handled_by_current_implementation(monkeypatch):
    service = AuthService()
    service.redis_config.cache_token = AsyncMock(
        side_effect=RedisError("Redis unavailable")
    )

    mock_response = httpx.Response(
        status_code=200,
        text="jwt-abc",
        request=httpx.Request(
            "POST",
            "https://example.test/token",
        ),
    )

    service.http_client.post = AsyncMock(
        return_value=mock_response
    )
    render_login = Mock(return_value=HTMLResponse("cache error", status_code=503))
    monkeypatch.setattr(service, "render_login", render_login)

    request = make_request()

    result = await service.web_in_token(request, "alice", "secret")

    assert result.status_code == 503
    render_login.assert_called_once_with(
        request=request,
        error=(
            "Authentication service is temporarily unavailable. "
            "Please contact the administrator."
        ),
        username="alice",
        status_code=503,
    )