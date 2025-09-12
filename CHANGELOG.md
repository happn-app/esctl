# Changelog

## 1.5.0

- Added commands
  - index cache delete
  - index settings
  - index create
  - troubleshoot
  - reindex

## 0.2.1

- Added commands
  - tasks
    - cancel

## 0.2.0

- Added `kubernetes` integration into `esctl`
- Added fix for ES server versions <7.10.0
- Added commands
  - config
    - add-context
      - kubernetes
      - http
  - cat
    - tasks

## 0.1.0

- Added commands
  - cat
    - health
    - indices
    - nodes
    - allocation
    - shards
  - cluster
    - allocation-explain
    - reroute
    - settings
  - config
    - add-context
    - remove-context
    - edit
    - contexts
- Added yamlpath option
- Added jmespath option
- Added jsonpath option
- Added value completions from ES context
