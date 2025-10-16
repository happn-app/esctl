import os
from pathlib import Path
import platform
from string import Template


if platform.system() == "Windows":
    XDG_CONFIG_HOME = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
else:
    XDG_CONFIG_HOME = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))

if os.getenv("ESCTL_HOME"):
    ESCTL_HOME = Path(os.environ["ESCTL_HOME"])
else:
    ESCTL_HOME = XDG_CONFIG_HOME / "esctl"

ESCTL_HOME.mkdir(exist_ok=True, parents=True)
ESCTL_CONFIG_PATH = ESCTL_HOME / "config.json"
ESCTL_TTL_CONFIG_PATH = ESCTL_HOME / "ttl.json"
ESCTL_CACHE_DB_PATH = ESCTL_HOME / "cache.db"


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
