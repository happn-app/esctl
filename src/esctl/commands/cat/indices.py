from itertools import product
from typing import Annotated, Iterable

import typer

from esctl.config import Config
from esctl.options import (
    BytesOption,
    IndexArgument,
    TimeOption,
    OutputOption,
    Result,
)

app = typer.Typer(rich_markup_mode="rich")


def formatter(column: str, value: str) -> str:
    if column == "health":
        return f"[b {value.lower()}]{value.upper()}[/]"
    return value


def complete_column(incomplete: str) -> list[tuple[str, str]]:
    columns = {
        "health": "current health status",
        "status": "open/close status",
        "index": "index name",
        "uuid": "index uuid",
        "pri": "number of primary shards",
        "rep": "number of replica shards",
        "docs.count": "available docs",
        "docs.deleted": "deleted docs",
        "creation.date": "index creation date (millisecond value)",
        "creation.date.string": "index creation date (as string)",
        "store.size": "store size of primaries & replicas",
        "pri.store.size": "store size of primaries",
        "completion.size": "size of completion",
        "pri.completion.size": "size of completion",
        "fielddata.memory_size": "used fielddata cache",
        "pri.fielddata.memory_size": "used fielddata cache",
        "fielddata.evictions": "fielddata evictions",
        "pri.fielddata.evictions": "fielddata evictions",
        "query_cache.memory_size": "used query cache",
        "pri.query_cache.memory_size": "used query cache",
        "query_cache.evictions": "query cache evictions",
        "pri.query_cache.evictions": "query cache evictions",
        "request_cache.memory_size": "used request cache",
        "pri.request_cache.memory_size": "used request cache",
        "request_cache.evictions": "request cache evictions",
        "pri.request_cache.evictions": "request cache evictions",
        "request_cache.hit_count": "request cache hit count",
        "pri.request_cache.hit_count": "request cache hit count",
        "request_cache.miss_count": "request cache miss count",
        "pri.request_cache.miss_count": "request cache miss count",
        "flush.total": "number of flushes",
        "pri.flush.total": "number of flushes",
        "flush.total_time": "time spent in flush",
        "pri.flush.total_time": "time spent in flush",
        "get.current": "number of current get ops",
        "pri.get.current": "number of current get ops",
        "get.time": "time spent in get",
        "pri.get.time": "time spent in get",
        "get.total": "number of get ops",
        "pri.get.total": "number of get ops",
        "get.exists_time": "time spent in successful gets",
        "pri.get.exists_time": "time spent in successful gets",
        "get.exists_total": "number of successful gets",
        "pri.get.exists_total": "number of successful gets",
        "get.missing_time": "time spent in failed gets",
        "pri.get.missing_time": "time spent in failed gets",
        "get.missing_total": "number of failed gets",
        "pri.get.missing_total": "number of failed gets",
        "indexing.delete_current": "number of current deletions",
        "pri.indexing.delete_current": "number of current deletions",
        "indexing.delete_time": "time spent in deletions",
        "pri.indexing.delete_time": "time spent in deletions",
        "indexing.delete_total": "number of delete ops",
        "pri.indexing.delete_total": "number of delete ops",
        "indexing.index_current": "number of current indexing ops",
        "pri.indexing.index_current": "number of current indexing ops",
        "indexing.index_time": "time spent in indexing",
        "pri.indexing.index_time": "time spent in indexing",
        "indexing.index_total": "number of indexing ops",
        "pri.indexing.index_total": "number of indexing ops",
        "indexing.index_failed": "number of failed indexing ops",
        "pri.indexing.index_failed": "number of failed indexing ops",
        "merges.current": "number of current merges",
        "pri.merges.current": "number of current merges",
        "merges.current_docs": "number of current merging docs",
        "pri.merges.current_docs": "number of current merging docs",
        "merges.current_size": "size of current merges",
        "pri.merges.current_size": "size of current merges",
        "merges.total": "number of completed merge ops",
        "pri.merges.total": "number of completed merge ops",
        "merges.total_docs": "docs merged",
        "pri.merges.total_docs": "docs merged",
        "merges.total_size": "size merged",
        "pri.merges.total_size": "size merged",
        "merges.total_time": "time spent in merges",
        "pri.merges.total_time": "time spent in merges",
        "refresh.total": "total refreshes",
        "pri.refresh.total": "total refreshes",
        "refresh.time": "time spent in refreshes",
        "pri.refresh.time": "time spent in refreshes",
        "refresh.external_total": "total external refreshes",
        "pri.refresh.external_total": "total external refreshes",
        "refresh.external_time": "time spent in external refreshes",
        "pri.refresh.external_time": "time spent in external refreshes",
        "refresh.listeners": "number of pending refresh listeners",
        "pri.refresh.listeners": "number of pending refresh listeners",
        "search.fetch_current": "current fetch phase ops",
        "pri.search.fetch_current": "current fetch phase ops",
        "search.fetch_time": "time spent in fetch phase",
        "pri.search.fetch_time": "time spent in fetch phase",
        "search.fetch_total": "total fetch ops",
        "pri.search.fetch_total": "total fetch ops",
        "search.open_contexts": "open search contexts",
        "pri.search.open_contexts": "open search contexts",
        "search.query_current": "current query phase ops",
        "pri.search.query_current": "current query phase ops",
        "search.query_time": "time spent in query phase",
        "pri.search.query_time": "time spent in query phase",
        "search.query_total": "total query phase ops",
        "pri.search.query_total": "total query phase ops",
        "search.scroll_current": "open scroll contexts",
        "pri.search.scroll_current": "open scroll contexts",
        "search.scroll_time": "time scroll contexts held open",
        "pri.search.scroll_time": "time scroll contexts held open",
        "search.scroll_total": "completed scroll contexts",
        "pri.search.scroll_total": "completed scroll contexts",
        "segments.count": "number of segments",
        "pri.segments.count": "number of segments",
        "segments.memory": "memory used by segments",
        "pri.segments.memory": "memory used by segments",
        "segments.index_writer_memory": "memory used by index writer",
        "pri.segments.index_writer_memory": "memory used by index writer",
        "segments.version_map_memory": "memory used by version map",
        "pri.segments.version_map_memory": "memory used by version map",
        "segments.fixed_bitset_memory": "memory used by fixed bit sets for nested object field types and type filters for types referred in _parent fields",
        "pri.segments.fixed_bitset_memory": "memory used by fixed bit sets for nested object field types and type filters for types referred in _parent fields",
        "warmer.current": "current warmer ops",
        "pri.warmer.current": "current warmer ops",
        "warmer.total": "total warmer ops",
        "pri.warmer.total": "total warmer ops",
        "warmer.total_time": "time spent in warmers",
        "pri.warmer.total_time": "time spent in warmers",
        "suggest.current": "number of current suggest ops",
        "pri.suggest.current": "number of current suggest ops",
        "suggest.time": "time spend in suggest",
        "pri.suggest.time": "time spend in suggest",
        "suggest.total": "number of suggest ops",
        "pri.suggest.total": "number of suggest ops",
        "memory.total": "total used memory",
        "pri.memory.total": "total user memory",
        "search.throttled": "indicates if the index is search throttled",
        "bulk.total_operations": "number of bulk shard ops",
        "pri.bulk.total_operations": "number of bulk shard ops",
        "bulk.total_time": "time spend in shard bulk",
        "pri.bulk.total_time": "time spend in shard bulk",
        "bulk.total_size_in_bytes": "total size in bytes of shard bulk",
        "pri.bulk.total_size_in_bytes": "total size in bytes of shard bulk",
        "bulk.avg_time": "average time spend in shard bulk",
        "pri.bulk.avg_time": "average time spend in shard bulk",
        "bulk.avg_size_in_bytes": "average size in bytes of shard bulk",
        "pri.bulk.avg_size_in_bytes": "average size in bytes of shard bulk",
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


@app.command(
    help="Returns high-level information about indices in a cluster, including backing indices for data streams.",
    short_help="Returns high-level information about indices in a cluster.",
)
def indices(
    ctx: typer.Context,
    index: IndexArgument = "*",
    header: Annotated[
        list[str] | None,
        typer.Option(
            "--header",
            "-h",
            help="Columns to include in the response",
            autocompletion=complete_column,
        ),
    ] = None,
    sort: SortOption = None,
    time: TimeOption | None = None,
    bytes: BytesOption | None = None,
    output: OutputOption = "table",
):
    client = Config.from_context(ctx).client
    params = {
        "h": ",".join(header) if header else None,
        "s": ",".join(sort) if sort else None,
        "time": time,
        "bytes": bytes,
        "index": index,
        "format": "json",
    }
    response = client.cat.indices(**params)
    result: Result = ctx.obj["selector"](response)
    result.print(output, formatter=formatter)
