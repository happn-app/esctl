from itertools import product
from typing import Annotated, Iterable
import typer

from esctl.config import Config
from esctl.options import (
    BytesOption,
    OutputOption,
    Result,
    TimeOption,
)

app = typer.Typer(rich_markup_mode="rich")


def complete_column(incomplete: str) -> list[tuple[str, str]]:
    columns = {
        "id": "unique node id",
        "pid": "process id",
        "ip": "ip address",
        "port": "bound transport port",
        "http_address": "bound http address",
        "version": "es version",
        "type": "es distribution type",
        "build": "es build hash",
        "jdk": "jdk version",
        "disk.total": "total disk space",
        "disk.used": "used disk space",
        "disk.avail": "available disk space",
        "disk.used_percent": "used disk space percentage",
        "heap.current": "used heap",
        "heap.percent": "used heap ratio",
        "heap.max": "max configured heap",
        "ram.current": "used machine memory",
        "ram.percent": "used machine memory ratio",
        "ram.max": "total machine memory",
        "file_desc.current": "used file descriptors",
        "file_desc.percent": "used file descriptor ratio",
        "file_desc.max": "max file descriptors",
        "cpu": "recent cpu usage",
        "load_1m": "1m load avg",
        "load_5m": "5m load avg",
        "load_15m": "15m load avg",
        "uptime": "node uptime",
        "node.role": "m:master eligible node, d:data node, i:ingest node, -:coordinating node only",
        "master": "*:current master",
        "name": "node name",
        "completion.size": "size of completion",
        "fielddata.memory_size": "used fielddata cache",
        "fielddata.evictions": "fielddata evictions",
        "query_cache.memory_size": "used query cache",
        "query_cache.evictions": "query cache evictions",
        "query_cache.hit_count": "query cache hit counts",
        "query_cache.miss_count": "query cache miss counts",
        "request_cache.memory_size": "used request cache",
        "request_cache.evictions": "request cache evictions",
        "request_cache.hit_count": "request cache hit counts",
        "request_cache.miss_count": "request cache miss counts",
        "flush.total": "number of flushes",
        "flush.total_time": "time spent in flush",
        "get.current": "number of current get ops",
        "get.time": "time spent in get",
        "get.total": "number of get ops",
        "get.exists_time": "time spent in successful gets",
        "get.exists_total": "number of successful gets",
        "get.missing_time": "time spent in failed gets",
        "get.missing_total": "number of failed gets",
        "indexing.delete_current": "number of current deletions",
        "indexing.delete_time": "time spent in deletions",
        "indexing.delete_total": "number of delete ops",
        "indexing.index_current": "number of current indexing ops",
        "indexing.index_time": "time spent in indexing",
        "indexing.index_total": "number of indexing ops",
        "indexing.index_failed": "number of failed indexing ops",
        "merges.current": "number of current merges",
        "merges.current_docs": "number of current merging docs",
        "merges.current_size": "size of current merges",
        "merges.total": "number of completed merge ops",
        "merges.total_docs": "docs merged",
        "merges.total_size": "size merged",
        "merges.total_time": "time spent in merges",
        "refresh.total": "total refreshes",
        "refresh.time": "time spent in refreshes",
        "refresh.external_total": "total external refreshes",
        "refresh.external_time": "time spent in external refreshes",
        "refresh.listeners": "number of pending refresh listeners",
        "script.compilations": "script compilations",
        "script.cache_evictions": "script cache evictions",
        "script.compilation_limit_triggered": "script cache compilation limit triggered",
        "search.fetch_current": "current fetch phase ops",
        "search.fetch_time": "time spent in fetch phase",
        "search.fetch_total": "total fetch ops",
        "search.open_contexts": "open search contexts",
        "search.query_current": "current query phase ops",
        "search.query_time": "time spent in query phase",
        "search.query_total": "total query phase ops",
        "search.scroll_current": "open scroll contexts",
        "search.scroll_time": "time scroll contexts held open",
        "search.scroll_total": "completed scroll contexts",
        "segments.count": "number of segments",
        "segments.memory": "memory used by segments",
        "segments.index_writer_memory": "memory used by index writer",
        "segments.version_map_memory": "memory used by version map",
        "segments.fixed_bitset_memory": "memory used by fixed bit sets for nested object field types and type filters for types referred in _parent fields",
        "suggest.current": "number of current suggest ops",
        "suggest.time": "time spend in suggest",
        "suggest.total": "number of suggest ops",
        "bulk.total_operations": "number of bulk shard ops",
        "bulk.total_time": "time spend in shard bulk",
        "bulk.total_size_in_bytes": "total size in bytes of shard bulk",
        "bulk.avg_time": "average time spend in shard bulk",
        "bulk.avg_size_in_bytes": "average size in bytes of shard bulk",
        "shard_stats.total_count": "number of shards assigned",
        "mappings.total_count": "number of mappings",
        "mappings.total_estimated_overhead_in_bytes": "estimated overhead in bytes of mappings",
    }
    return [
        (column, description)
        for column, description in columns.items()
        if column.startswith(incomplete)
    ]


def complete_sort(
    ctx: typer.Context, incomplete: str
) -> Iterable[str | tuple[str, str]]:
    columns = list(complete_column(incomplete.split(":")[0]))
    orders = ["asc", "desc"]
    return [
        (f"{column}:{order}", description)
        for (column, description), order in product(columns, orders)
        if column.startswith(incomplete.split(":")[0])
    ]


SortOption = Annotated[
    list[str] | None,
    typer.Option(
        "--sort",
        "-s",
        autocompletion=complete_sort,
        help="How to sort the response",
    ),
]


@app.command(help="Returns information about a cluster’s nodes.")
def nodes(
    ctx: typer.Context,
    header: Annotated[
        list[str] | None,
        typer.Option(
            "--header",
            "-h",
            autocompletion=complete_column,
            help="Columns to include in the response",
        ),
    ],
    sort: SortOption = None,
    time: TimeOption | None = None,
    bytes: BytesOption | None = None,
    full_id: Annotated[
        bool,
        typer.Option(
            help=(
                "If true, the node ID is displayed in full. Defaults to false, "
                "which means the node ID is displayed in short form."
            ),
        ),
    ] = True,
    include_unloaded_segments: Annotated[
        bool,
        typer.Option(
            "--include-unloaded-segments",
            help=(
                "If true, the response includes information from segments "
                "that are not loaded into memory. Defaults to false. "
            ),
        ),
    ] = False,
    output: OutputOption = "table",
):
    params = {
        "h": ",".join(header) if header else None,
        "s": ",".join(sort) if sort else None,
        "time": time,
        "full_id": full_id,
        "bytes": bytes,
        "include_unloaded_segments": include_unloaded_segments,
        "format": "json",
    }
    client = Config.from_context(ctx).client
    response = client.cat.nodes(**params)
    result: Result = ctx.obj["selector"](response)
    result.print(output)
