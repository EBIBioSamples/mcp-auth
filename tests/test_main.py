from fastapi.testclient import TestClient
from app.main import app

def test_application_title():
    assert app.title == "Python Login Portal"

def test_expected_routes_are_registered():
    paths = {route.path for route in app.routes}

    assert "/" in paths
    assert "/login" in paths
    assert "/static" in paths

def test_application_serves_login_page():
    client = TestClient(app)
    response = client.get("/login")

    assert response.status_code == 200
    assert "login" in response.text.lower()

def test_static_css_is_served():
    client = TestClient(app)
    response = client.get("/static/style.css")

    assert response.status_code == 200
    assert response.text.strip()