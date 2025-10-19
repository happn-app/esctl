import functools
from itertools import product
from typing import Annotated, Iterable
import typer

from esctl.config import Config
from esctl.options import (
    OutputOption,
    Result,
)

app = typer.Typer(rich_markup_mode="rich")


@functools.lru_cache()
def formatter(column: str, value: str) -> str:
    match column:
        case "status":
            return f"[b {value.lower()}]{value.upper()}[/]"
        case "active_shards_percent_as_number":
            if float(value) < 50:
                return f"[b red]{value}%[/]"
            elif float(value) < 75:
                return f"[b yellow]{value}%[/]"
            else:
                return f"[b green]{value}%[/]"
        case "unassigned_shards":
            if float(value) == 0:
                return f"[b green]{value}%[/]"
            else:
                return f"[b red]{value}%[/]"
        case "initializing_shards":
            if float(value) == 0:
                return f"[b green]{value}[/]"
            else:
                return f"[b yellow]{value}[/]"
        case "relocating_shards":
            if float(value) == 0:
                return f"[b green]{value}[/]"
            else:
                return f"[b yellow]{value}[/]"
        case "task_max_waiting_in_queue_millis":
            return f"{float(value) / 1000:.2f}s"
        case _:
            return value


def complete_column(incomplete: str) -> Iterable[tuple[str, str]]:
    columns = {
        "epoch": "seconds since 1970-01-01 00:00:00",
        "timestamp": "time in HH:MM:SS",
        "cluster": "cluster name",
        "status": "health status",
        "node.total": "total number of nodes",
        "node.data": "number of nodes that can store data",
        "shards.total": "total number of shards",
        "shards.primary": "number of primary shards",
        "shards.relocating": "number of relocating shards",
        "shards.initializing": "number of initializing shards",
        "shards.unassigned": "number of unassigned shards",
        "pending_tasks": "number of pending tasks",
        "max_task_wait_time": "wait time of longest task pending",
        "active_shards_percent": "active number of shards in percent",
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
    help="Returns the health status of a cluster, similar to the cluster health API.",
    short_help="Returns the health status of a cluster.",
)
def health(
    ctx: typer.Context,
    output: OutputOption = "table",
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
):
    params = {
        "s": ",".join(sort) if sort else None,
        "h": ",".join(header) if header else None,
        "format": "json",
        "v": True,
    }
    client = Config.from_context(ctx).client
    response = client.cat.health(**params)
    result: Result = ctx.obj["selector"](response)
    if header is None:
        result.exclude_headers.update(set(["epoch", "timestamp"]))
    result.print(
        output,
        formatter=formatter,
    )
