import importlib
import pytest


@pytest.mark.integration
def test_https_redirect_middleware_enabled_in_production(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://dreamcatcher.example.com"]')
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("FORCE_HTTPS", "true")

    import main as main_module
    reloaded = importlib.reload(main_module)

    middleware_names = [item.cls.__name__ for item in reloaded.app.user_middleware]
    assert "HTTPSRedirectMiddleware" in middleware_names


@pytest.mark.integration
def test_https_redirect_middleware_disabled_when_force_false(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://dreamcatcher.example.com"]')
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("FORCE_HTTPS", "false")

    import main as main_module
    reloaded = importlib.reload(main_module)

    middleware_names = [item.cls.__name__ for item in reloaded.app.user_middleware]
    assert "HTTPSRedirectMiddleware" not in middleware_names
