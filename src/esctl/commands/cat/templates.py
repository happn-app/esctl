from itertools import product
from typing import Annotated, Iterable
import typer

from esctl.config import Config
from esctl.options import (
    OutputOption,
    Result,
)

app = typer.Typer(rich_markup_mode="rich")


def complete_column(incomplete: str) -> list[tuple[str, str]]:
    columns = {
        "name": "template name",
        "index_patterns": "template index patterns",
        "order": "template application order/priority number",
        "version": "version",
        "composed_of": "component templates comprising index template",
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
    help="Lists the templates in the cluster.",
)
def templates(
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
    sort: SortOption | None = None,
    output: OutputOption = "table",
):
    params = {
        "h": ",".join(header) if header else None,
        "s": ",".join(sort) if sort else None,
        "format": "json",
    }
    client = Config.from_context(ctx).client
    response = client.cat.templates(**params)
    result: Result = ctx.obj["selector"](response)
    result.print(output)
