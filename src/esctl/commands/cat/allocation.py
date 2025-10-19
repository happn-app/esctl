from itertools import product
from typing import Annotated, Iterable
import typer
from esctl.config import Config

from esctl.options import (
    OutputOption,
    Result,
    BytesOption,
)


app = typer.Typer(rich_markup_mode="rich")


def formatter(column: str, value: str) -> str:
    if column == "disk.percent":
        disk_percent = float(value.replace("%", ""))
        if disk_percent < 75:
            return f"[b green]{value}[/]"
        elif disk_percent < 85:
            return f"[b yellow]{value}[/]"
        else:
            return f"[b red]{value}[/]"
    return value


def complete_column(incomplete: str) -> list[tuple[str, str]]:
    columns = {
        "shards": "number of shards on node",
        "disk.indices": "disk used by ES indices",
        "disk.used": "disk used (total, not just ES)",
        "disk.avail": "disk available",
        "disk.total": "total capacity of all volumes",
        "disk.percent": "percent disk used",
        "host": "host of node",
        "ip": "ip of node",
        "node": "name of node",
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
def allocation(
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
    bytes: BytesOption | None = None,
    local_only: Annotated[
        bool,
        typer.Option(
            help=(
                "If true, the request retrieves information from the local node only. "
                "Defaults to false, which means information is retrieved from the master node."
            ),
        ),
    ] = False,
    output: OutputOption = "table",
):
    params = {
        "s": ",".join(sort) if sort else None,
        "h": ",".join(header) if header else None,
        "bytes": bytes,
        "local": local_only,
        "format": "json",
        "v": True,
    }
    client = Config.from_context(ctx).client
    response = client.cat.allocation(**params)
    result: Result = ctx.obj["selector"](response)
    result.print(
        output=output,
        formatter=formatter,
    )
