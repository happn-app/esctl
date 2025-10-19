from itertools import product
from textwrap import dedent
from typing import Annotated, Iterable

import typer

from esctl.config import Config
from esctl.options import (
    BytesOption,
    IndexOption,
    TimeOption,
    OutputOption,
    Result,
)

app = typer.Typer(rich_markup_mode="rich")


def formatter(column: str, value: str) -> str:
    if column == "state":
        if value == "STARTED":
            return "[b green]STARTED[/]"
        elif value == "RELOCATING":
            return "[b yellow]RELOCATING[/]"
        elif value == "INITIALIZING":
            return "[b blue]INITIALIZING[/]"
        elif value == "UNASSIGNED":
            return "[b red]UNASSIGNED[/]"
    return value


def complete_column(incomplete: str) -> list[tuple[str, str]]:
    columns = {
        "index": "index name",
        "shard": "shard name",
        "prirep": "primary or replica",
        "state": "shard state",
        "docs": "number of docs in shard",
        "store": "store size of shard (how much disk it uses)",
        "ip": "ip of node where it lives",
        "id": "unique id of node where it lives",
        "node": "name of node where it lives",
        "sync_id": "sync id",
        "unassigned.reason": "reason shard became unassigned",
        "unassigned.at": "time shard became unassigned (UTC)",
        "unassigned.for": "time has been unassigned",
        "unassigned.details": "additional details as to why the shard became unassigned",
        "recoverysource.type": "recovery source type",
        "completion.size": "size of completion",
        "fielddata.memory_size": "used fielddata cache",
        "fielddata.evictions": "fielddata evictions",
        "query_cache.memory_size": "used query cache",
        "query_cache.evictions": "query cache evictions",
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
        "seq_no.max": "max sequence number",
        "seq_no.local_checkpoint": "local checkpoint",
        "seq_no.global_checkpoint": "global checkpoint",
        "warmer.current": "current warmer ops",
        "warmer.total": "total warmer ops",
        "warmer.total_time": "time spent in warmers",
        "path.data": "shard data path",
        "path.state": "shard state path",
        "bulk.total_operations": "number of bulk shard ops",
        "bulk.total_time": "time spend in shard bulk",
        "bulk.total_size_in_bytes": "total size in bytes of shard bulk",
        "bulk.avg_time": "average time spend in shard bulk",
        "bulk.avg_size_in_bytes": "avg size in bytes of shard bulk",
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
    help=dedent(
        """
        The shards command is the detailed view of what nodes contain which shards.
        It will tell you if it’s a primary or replica, the number of docs,
        the bytes it takes on disk, and the node where it’s located.
    """
    )
)
def shards(
    ctx: typer.Context,
    index: IndexOption | None = None,
    header: Annotated[
        list[str] | None,
        typer.Option(
            "--header",
            "-h",
            autocompletion=complete_column,
            help="Columns to include in the response",
        ),
    ] = None,
    sort: SortOption = None,
    time: TimeOption | None = None,
    bytes: BytesOption | None = None,
    output: OutputOption = "table",
):
    params = {
        "h": header,
        "s": sort,
        "time": time,
        "bytes": bytes,
        "index": index,
        "format": "json",
    }
    client = Config.from_context(ctx).client
    response = client.cat.shards(**params)
    result: Result = ctx.obj["selector"](response)
    result.print(output=output, formatter=formatter)
