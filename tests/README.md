# Tests

Three tiers, selected by marker. Install the test group first:

```sh
uv sync --group test
```

## Tier 1 — unit (`tests/unit/`, no Docker)

Pure logic: `strfdelta`, output formatting/selectors, CAT column formatters,
option enums, config models. Fast, run everywhere.

```sh
uv run --group test pytest tests/unit -m "not integration and not kube"
```

## Tier 2 — integration (`tests/integration/`, `@pytest.mark.integration`)

Spins up a real Elasticsearch via `testcontainers` and exercises
`HTTPClientFactory` (version detection → correct client class) and CAT commands
through the Typer `CliRunner`. Needs Docker.

```sh
uv run --group test pytest tests/integration -m integration
```

## Tier 3 — kube (`tests/kube/`, `@pytest.mark.kube`, slow)

Boots a real k3s cluster (`testcontainers` `K3SContainer`), deploys a plain ES
pod + credentials secret using the **ECK label conventions** (no operator), then
drives the actual Kubernetes port-forward path in `KubeClientFactory`
end-to-end. Needs Docker; slow (minutes).

```sh
uv run --group test pytest tests/kube -m kube
```

> **macOS note:** on Docker Desktop, nested containerd frequently cannot create
> pod sandboxes (`FailedCreatePodSandBox … ttrpc: closed`). The fixture detects
> this and **skips** rather than failing — this tier is meant to run for real on
> a Linux Docker host (CI). CI runs it on the nightly schedule / manual dispatch.

## Notes

- `tests/conftest.py` points `ESCTL_HOME` at a throwaway temp dir **before** any
  `esctl` import (config paths are derived at import time) and clears the
  `Config.load` / `Config.from_context` `lru_cache` between tests.
- CAT command tests reload `esctl.cli` after writing the config file because the
  module binds `cfg = Config.load()` at import time.
