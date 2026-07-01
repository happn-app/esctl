from esctl.config.config import Config
from esctl.config.models.http import HTTPESConfig


def _http(**kwargs):
    kwargs.setdefault("name", "test")
    return HTTPESConfig(type="http", **kwargs)


def test_url():
    cfg = _http(host="es.example.com", port=9201)
    assert cfg.url == "http://es.example.com:9201"


def test_url_default_port():
    assert _http(host="es.example.com").url == "http://es.example.com:9200"


def test_basic_auth_present():
    cfg = _http(host="h", username="elastic", password="secret")
    assert cfg.basic_auth == ("elastic", "secret")


def test_basic_auth_missing():
    assert _http(host="h").basic_auth is None
    assert _http(host="h", username="elastic").basic_auth is None


def test_censored_password():
    cfg = _http(host="h", username="u", password="supersecret")
    assert cfg.censored_password == "supe" + "*" * len("rsecret")


def test_censored_password_empty_when_none():
    assert _http(host="h").censored_password == ""


def test_inject_context_names():
    """The before-validator injects each context's dict key as its ``name``."""
    cfg = Config.model_validate(
        {
            "contexts": {
                "prod": {"type": "http", "host": "prod.example.com"},
                "staging": {"type": "http", "host": "staging.example.com"},
            },
            "current_context": "prod",
        }
    )
    assert cfg.contexts["prod"].name == "prod"
    assert cfg.contexts["staging"].name == "staging"
