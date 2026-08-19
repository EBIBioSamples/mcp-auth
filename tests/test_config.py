import importlib
import app.core.config as config_module

def test_settings_have_expected_defaults():
    settings = config_module.Settings()

    assert settings.WEBIN_TOKEN_URL.startswith("https://")
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.session_secret

def test_settings_read_environment_values(monkeypatch):
    monkeypatch.setenv("WEBIN_TOKEN_URL", "https://example.test/token")
    monkeypatch.setenv("REDIS_URL", "redis://example.test:6380/1")
    monkeypatch.setenv("SESSION_SECRET", "unit-test-secret")

    reloaded = importlib.reload(config_module)
    try:
        settings = reloaded.Settings()
        assert settings.WEBIN_TOKEN_URL == "https://example.test/token"
        assert settings.redis_url == "redis://example.test:6380/1"
        assert settings.session_secret == "unit-test-secret"
    finally:
        monkeypatch.delenv("WEBIN_TOKEN_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.delenv("SESSION_SECRET", raising=False)
        importlib.reload(config_module)