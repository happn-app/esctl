import re
import sqlite3
import time
from typing import Any, Mapping, Optional

import blake3
from elastic_transport import ApiResponseMeta
from elastic_transport._node._base import NodeApiResponse
import orjson

from esctl.constants import ESCTL_CACHE_DB_PATH, ESCTL_TTL_CONFIG_PATH


US = "\x1f"  # unit separator; never appears in JSON


def _canon_json(obj: Any) -> str:
    """Deterministic, compact JSON (sorted keys, no extra spaces)."""
    return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS).decode("utf-8")


def _canon_headers(headers: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Lowercase header names; keep original order irrelevant."""
    if not headers:
        return {}
    return {str(k).lower(): headers[k] for k in headers if k.lower() != "authorization"}


def _make_cache_key(
    method: str,
    target: str,
    headers_c: str,
) -> bytes:
    h = blake3.blake3()
    h.update(method.encode("utf-8"))
    h.update(US.encode())
    h.update(target.encode("utf-8"))
    h.update(US.encode())
    h.update(headers_c.encode("utf-8"))
    return h.digest()  # 32 bytes


def _serialize(response: NodeApiResponse) -> str:
    return _canon_json(
        {
            "status": response.meta.status,
            "headers": dict(response.meta.headers),
            "http_version": response.meta.http_version,
            "body": response.body.decode("utf-8", errors="replace"),
        }
    )


def _deserialize(s: str) -> NodeApiResponse:
    d = orjson.loads(s)
    return NodeApiResponse(
        body=d["body"].encode("utf-8"),
        meta=ApiResponseMeta(
            status=d["status"],
            headers=d["headers"],
            http_version=d["http_version"],
            node=None,  # type: ignore[arg-type]
            duration=0.0,  # type: ignore[arg-type
        ),
    )


class Cache:
    @staticmethod
    def get_ttl(key: str) -> int:
        """Return TTL in seconds for a given cache key."""
        cache_config_path = ESCTL_TTL_CONFIG_PATH
        if not cache_config_path.exists():
            return 300  # default 5 minutes
        cache_config = orjson.loads(cache_config_path.read_bytes())
        for pattern, ttl in cache_config.items():
            if re.search(pattern, key):
                return int(ttl)
        else:
            return 300  # default 5 minutes

    def __init__(self, context_name: str, enabled: bool = True):
        self.db_path = ESCTL_CACHE_DB_PATH
        self.enabled = enabled
        self.conn = sqlite3.connect(self.db_path, autocommit=True)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA temp_store=MEMORY;")
        self.conn.execute("PRAGMA mmap_size=268435456;")  # 256 MiB, safe default
        self.context_name = re.sub(r"[^a-zA-Z0-9_]", "_", context_name)
        self._initialize_db()

    def _initialize_db(self):
        with self.conn:
            self.conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS http_cache_{self.context_name} (
                    cache_key     BLOB PRIMARY KEY,      -- 32 bytes blake3
                    method        TEXT NOT NULL,
                    target          TEXT NOT NULL,
                    headers_json  TEXT NOT NULL,
                    response      TEXT NOT NULL,
                    stored_at     INTEGER NOT NULL,       -- epoch seconds
                    ttl           INTEGER NOT NULL        -- seconds
                ) WITHOUT ROWID;
            """
            )
        with self.conn:
            # Helpful secondary index if you ever want to purge by method/target.
            self.conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS http_cache_{self.context_name}_method_target
                ON http_cache_{self.context_name}(method, target);
            """
            )

    def get(
        self,
        method: str,
        target: str,
        headers: Optional[Mapping[str, Any]] = None,
    ) -> Optional[NodeApiResponse]:
        """Return cached response if fresh, else None (and evict if expired)."""
        if method.upper() not in ("GET", "HEAD"):
            return None
        if not self.enabled:
            return None
        headers_c = _canon_json(_canon_headers(headers))
        key = _make_cache_key(method, target, headers_c)

        row = self.conn.execute(
            "SELECT response, stored_at, ttl, headers_json "
            "FROM http_cache WHERE cache_key = ?;",
            (key,),
        ).fetchone()

        if not row:
            return None

        response, stored_at, ttl, headers_c_db = row

        # Paranoia check to guard against theoretical hash collisions
        if headers_c_db != headers_c:
            # Collision or inconsistent canonicalization -> act as a miss
            return None

        if int(time.time()) < stored_at + int(ttl):
            return _deserialize(response)

        # Expired: evict and miss
        self.delete(method, target, headers=headers)
        return None

    def set(
        self,
        method: str,
        target: str,
        response: NodeApiResponse,
        *,
        headers: Optional[Mapping[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Insert/refresh cache entry."""
        if method.upper() not in ("GET", "HEAD"):
            return
        if not self.enabled:
            return
        headers_c = _canon_json(_canon_headers(headers))
        key = _make_cache_key(method, target, headers_c)
        ttl = int(ttl if ttl is not None else 300)  # default 5 minutes
        response_str = _serialize(response)
        with self.conn:
            self.conn.execute(
                f"INSERT OR REPLACE INTO http_cache_{self.context_name} "
                "(cache_key, method, target, headers_json, response, stored_at, ttl) "
                "VALUES (?, ?, ?, ?, ?, ?, ?);",
                (key, method, target, headers_c, response_str, int(time.time()), ttl),
            )

    def delete(
        self,
        method: str,
        target: str,
        *,
        headers: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Remove a single cache entry."""
        headers_c = _canon_json(_canon_headers(headers))
        key = _make_cache_key(method, target, headers_c)
        with self.conn:
            self.conn.execute(
                f"DELETE FROM http_cache_{self.context_name} WHERE cache_key = ?;",
                (key,),
            )

    def clear(self) -> None:
        with self.conn:
            self.conn.execute(f"DELETE FROM http_cache_{self.context_name};")
