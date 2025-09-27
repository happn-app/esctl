import os
from pathlib import Path


def get_esctl_config_path() -> Path:
    return get_esctl_home() / "config.json"


def get_esctl_home() -> Path:
    if os.getenv("ESCONFIG"):
        return Path(os.environ["ESCONFIG"])
    HOME = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    CONFIG_DIR = HOME / "esctl"
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(exist_ok=True, parents=True)
    return CONFIG_DIR
