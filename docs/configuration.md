---
tags:
  - Configuration
  - Setup
title: Configuration
---

## Contexts

`esctl` contexts are just names for different elasticsearch clusters.

!!!info
    The name `context` instead of something like `cluster` was chosen to be more similar
    to existing `ctl` command-line tools, like `kubectl`.

A context has always a type, which can be one of:

- `http`
- `kubernetes`
- `gce`

### HTTP Contexts

HTTP contexts are the simplest ones, here is an example:

```json
{
  "contexts": {
    "local": {
      "type": "http",
      "host": "localhost",
      "port": 9200,
      "username": "",
      "password": ""
    }
  }
}
```

Username and password should be set to your desired elasticsearch username/password combo
for basic authentication. Leave them as empty strings to connect to an ES cluster without
authentication, such as one deployed locally with `docker` for instance.

### Kubernetes Contexts

Kubernetes contexts are for ES Clusters running on Kubernetes with the ECK Operator, here
is an example:

```json
{
  "contexts": {
    "kubernetes": {
      "type": "kubernetes",
      "kube_context": "prod",
      "kube_namespace": "default",
      "es_name": "test"
    }
  }
}
```

This context will fetch the `elastic` superuser's credentials from the `<es_name>-es-elastic-user`
kubernetes secret. It will also automatically port forward to the cluster using kubernetes' port-forward API.

### GCE Contexts

GCE contexts are for ES Clusters made manually on Google Compute Engine instances, here is an example:

```json
{
  "contexts": {
    "gce": {
      "type": "gce",
      "vm_name": "my_gce_instance",
      "zone": "europe-west1-c",
      "username": null,
      "password": null,
      "port": 9200,
      "target_port": 9200,
      "project_id": "gcp-project-id"
    }
  }
}
```

It is recommended to choose a different target port for each of your GCE contexts. This is so
that you can have multiple `esctl` connections open in different terminals.

## Current Context

This configuration option is just saved here as a way to hold on to the last used context.
Do not set manually, or set it to the name of one of your defined contexts.

## Aliases

!!!warning
    Aliases are an `alpha` feature, use at your own discretion!

Aliases are a way to save common `esctl` commands and flags in easy shorthands.

Here is an example alias:

```json
{
  "aliases": {
    "alias-name": {
      "command": "cat.health",
      "help": "",
      "args": {
        "header": [
          "status",
          "cluster"
        ]
      }
    }
  }
}
```

The alias `command` is just the module path relative to the `esctl.commands` submodule. The
`args` is just a dictionnary of arguments as expected by the given command's keyword arguments.

!!!info
    All alias names should be unique and should not shadow any of `esctl`'s base commands
    (i.e. `config`, `snapshots`, `troubleshoot` etc)

## Github Auth Command

This is a command that should be executed by `esctl` to fetch a GitHub API token, to enable
auto-reporting of crashes and exceptions in a github issue.

Common values are either `gh auth token` (if you have installed the github CLI), `echo $GITHUB_TOKEN`
if you have set a PAT in the `GITHUB_TOKEN` environment variable, or `cat ~/.github_token` if you have
saved a PAT in the `~/.github_token` file.

It is recommended to install the github CLI and set this as `gh auth token` if you want to enable
crash auto-reports.

If you want to disable this feature, set this option to `null`.
