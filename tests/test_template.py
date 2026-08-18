from pathlib import Path
from app.core.template import templates

def test_template_loader_points_to_app_templates():
    searchpath = [Path(path).as_posix() for path in templates.env.loader.searchpath]
    assert any(path.endswith("app/templates") for path in searchpath)

def test_login_template_exists():
    template = templates.get_template("login.html")
    assert template.name == "login.html"

def test_base_template_exists():
    template = templates.get_template("base.html")
    assert template.name == "base.html"