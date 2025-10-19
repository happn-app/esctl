from itertools import product
from textwrap import dedent
from typing import Annotated, Iterable

import typer

from esctl.config import Config
from esctl.options import (
    NodeOption,
    ParentTaskIdOption,
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
        "id": "id of the task with the node",
        "action": "task action",
        "task_id": "unique task id",
        "parent_task_id": "parent task id",
        "type": "task type",
        "start_time": "start time in ms",
        "timestamp": "start time in HH:MM:SS",
        "running_time_ns": "running time ns",
        "running_time": "running time",
        "node_id": "unique node id",
        "ip": "ip address",
        "port": "bound transport port",
        "node": "node name",
        "version": "es version",
        "x_opaque_id": "X-Opaque-ID header",
    }
    return [
        (column, description)
        for column, description in columns.items()
        if column.startswith(incomplete)
    ]


def complete_sort(incomplete: str) -> Iterable[str | tuple[str, str]]:
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
        Returns information about tasks currently executing in the cluster,
        similar to the task management API.
        """
    )
)
def tasks(
    ctx: typer.Context,
    detailed: bool = False,
    header: Annotated[
        list[str] | None,
        typer.Option(
            "--header",
            "-h",
            autocompletion=complete_column,
            help="Columns to include in the response",
        ),
    ] = None,
    sort: SortOption | None = None,
    nodes: NodeOption = None,
    time: TimeOption | None = None,
    parent_task_id: ParentTaskIdOption = None,
    output: OutputOption = "table",
):
    params = {
        "h": header,
        "s": sort,
        "time": time,
        "detailed": detailed,
        "nodes": nodes,
        "parent_task_id": parent_task_id,
        "format": "json",
    }
    client = Config.from_context(ctx).client
    response = client.cat.tasks(**params)
    result: Result = ctx.obj["selector"](response)
    result.print(
        output=output,
        formatter=formatter,
    )
