from itertools import product
from textwrap import dedent
from typing import Annotated, Iterable

import typer

from esctl.config import Config
from esctl.options import (
    BytesOption,
    OutputOption,
    Result,
    IndexOption,
    TimeOption,
)

app = typer.Typer(rich_markup_mode="rich")


def complete_column(incomplete: str) -> list[tuple[str, str]]:
    columns = {
        "index": "index name",
        "shard": "shard name",
        "start_time": "recovery start time",
        "start_time_millis": "recovery start time in epoch milliseconds",
        "stop_time": "recovery stop time",
        "stop_time_millis": "recovery stop time in epoch milliseconds",
        "time": "recovery time",
        "type": "recovery type",
        "stage": "recovery stage",
        "source_host": "source host",
        "source_node": "source node name",
        "target_host": "target host",
        "target_node": "target node name",
        "repository": "repository",
        "snapshot": "snapshot",
        "files": "number of files to recover",
        "files_recovered": "files recovered",
        "files_percent": "percent of files recovered",
        "files_total": "total number of files",
        "bytes": "number of bytes to recover",
        "bytes_recovered": "bytes recovered",
        "bytes_percent": "percent of bytes recovered",
        "bytes_total": "total number of bytes",
        "translog_ops": "number of translog ops to recover",
        "translog_ops_recovered": "translog ops recovered",
        "translog_ops_percent": "percent of translog ops recovered",
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
        Returns information about ongoing and completed shard recoveries, similar to the index recovery API.
        For data streams, the API returns information about the stream’s backing indices.
    """
    )
)
def recovery(
    ctx: typer.Context,
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
    detailed: Annotated[
        bool | None,
        typer.Option(
            help="If true, the response includes detailed information about shard recovery. Defaults to false.",
        ),
    ] = False,
    index: IndexOption | None = None,
    active_only: Annotated[
        bool,
        typer.Option(
            help="If true, the response includes only ongoing recoveries. Defaults to false.",
        ),
    ] = False,
    output: OutputOption = "table",
):
    params = {
        "h": ",".join(header) if header else None,
        "s": ",".join(sort) if sort else None,
        "time": time,
        "active_only": active_only,
        "bytes": bytes,
        "detailed": detailed,
        "index": index,
        "format": "json",
    }

    client = Config.from_context(ctx).client
    response = client.cat.recovery(**params)
    result: Result = ctx.obj["selector"](response)
    result.print(output)
