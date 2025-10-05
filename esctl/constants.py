import os
from pathlib import Path
from string import Template


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


ISSUE_TEMPLATE = Template("""# An exception of type `$exception_type` occurred.

## Message
$exception_message

## Traceback
```python-traceback
$exception_traceback
```

## Environment
- esctl version: $esctl_version
- Elasticsearch version: $es_version
- Kubernetes version: $k8s_version
- Python version: $python_version
- OS: $os_info
- License: Apache-2.0

## Command
`$command`

""")
