---
tags:
  - Core
title: Cache
---

`esctl` makes use of a caching database whenever the `--no-cache` flag is absent.

This database is a simple SQLite3 DB, with one table per esctl context.

The cache intervenes whenever esctl tries to make an API call to the Elasticsearch API.
Due to the fact that there is no `ETag/If-None-Match` support in the Elasticsearch API,
caching is limited to a simple TTL cache.

Use of caching is opt-out, for performance reasons, especially when using tab-completion.
Since caching is per-context there is no risk of caching leaks to other contexts. The
default TTL is 5 minutes.

## Configuring Cache TTL

Configuring the TTL for individual requests beyond the default of 5 minutes is straightforward,
as the cache expects a `ttl.json` config file in esctl's home directory. The format is as follows:

```json
{
  "GET /_cat/health/.+$": 3600
}
```

Each entry in the config is a python regular expression pattern mapped to a TTL in seconds.
The cache key is composed of the HTTP method and the target of the API call. Any valid python
regular expression is usable as a key in the `ttl.json` configuration file.

The TTL is used only when the cached response is set in the database. In other words, changing the TTL
value in the `ttl.json` configuration file will only take effect after the current cache expires.
