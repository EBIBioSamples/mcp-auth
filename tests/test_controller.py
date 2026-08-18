import pytest

from unittest.mock import AsyncMock, Mock
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.controller import web_in_controller

def make_request(path: str = "/login", session=None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "session": {} if session is None else session,
    }
    return Request(scope)

@pytest.mark.asyncio
async def test_home_returns_303_redirect():
    response = await web_in_controller.home()

    assert response.status_code == 303
    assert response.headers["location"] == "/login"

@pytest.mark.asyncio
async def test_login_page_pops_message_and_passes_it_to_service(monkeypatch):
    request = make_request(session={"message": "Authentication successful."})
    rendered = HTMLResponse("ok")
    render_login = Mock(return_value=rendered)
    monkeypatch.setattr(web_in_controller.auth_service, "render_login", render_login)

    response = await web_in_controller.login_page(request)

    assert response is rendered
    assert "message" not in request.session
    render_login.assert_called_once_with(
        request,
        message="Authentication successful.",
    )

@pytest.mark.asyncio
async def test_login_page_passes_none_when_session_has_no_message(monkeypatch):
    request = make_request(session={})
    rendered = HTMLResponse("ok")
    render_login = Mock(return_value=rendered)
    monkeypatch.setattr(web_in_controller.auth_service, "render_login", render_login)

    await web_in_controller.login_page(request)

    render_login.assert_called_once_with(request, message=None)

@pytest.mark.asyncio
async def test_login_delegates_credentials_to_auth_service(monkeypatch):
    request = make_request()
    expected = HTMLResponse("done")
    web_in_token = AsyncMock(return_value=expected)
    monkeypatch.setattr(web_in_controller.auth_service, "web_in_token", web_in_token)

    response = await web_in_controller.login(
        request=request,
        username="alice",
        password="secret",
    )

    assert response is expected
    web_in_token.assert_awaited_once_with(
        request=request,
        username="alice",
        password="secret",
    )