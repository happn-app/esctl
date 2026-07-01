"""Shared pytest configuration.

CRITICAL: ``esctl.constants`` runs ``ESCTL_HOME.mkdir(...)`` at import time and
derives every config path from ``ESCTL_HOME``. We must point it at a throwaway
directory *before* any ``esctl`` module is imported. pytest imports this conftest
before collecting/importing test modules, so setting the env var here (at module
import time, not inside a fixture) is early enough.
"""

import os
import tempfile
from pathlib import Path

# Isolate esctl's config/cache from the developer's real ~/.config/esctl.
_ESCTL_TMP_HOME = Path(tempfile.mkdtemp(prefix="esctl-tests-"))
os.environ["ESCTL_HOME"] = str(_ESCTL_TMP_HOME)

import pytest  # noqa: E402


@pytest.fixture
def esctl_home() -> Path:
    """The temporary ESCTL_HOME used for the test session."""
    return _ESCTL_TMP_HOME


@pytest.fixture(autouse=True)
def _reset_config_caches():
    """Clear lru_cache on Config.load / Config.from_context between tests.

    Both are cached (src/esctl/config/config.py) and would otherwise leak a
    stale Config across tests that write different config files.
    """
    yield
    try:
        from esctl.config.config import Config

        Config.load.cache_clear()
        Config.from_context.cache_clear()
    except Exception:
        # esctl may not have been imported in a given test; nothing to clear.
        pass


@pytest.fixture
def write_config():
    """Return a helper that writes a Config to ESCTL_CONFIG_PATH and returns it.

    Clears the load cache so the fresh file is read back on the next load.
    """

    def _write(config):
        from esctl.config.config import Config

        config.save()
        Config.load.cache_clear()
        Config.from_context.cache_clear()
        return config

    return _write
