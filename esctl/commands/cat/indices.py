from contextlib import suppress

import typer
from elasticsearch import Elasticsearch

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    BytesOption,
    FormatOption,
    HeaderOption,
    IndexArgument,
    SortOption,
    TimeOption,
)
from esctl.selectors import select_from_context
from esctl.utils import get_cat_base_params_from_context

app = typer.Typer(rich_markup_mode="rich")


def formatter(header: list[str], row: list[str]) -> list[str]:
    with suppress(ValueError):
        health_idx = header.index("health")
        if row[health_idx] == "green":
            row[health_idx] = f"[b green]{row[health_idx]}[/]"
        elif row[health_idx] == "yellow":
            row[health_idx] = f"[b yellow]{row[health_idx]}[/]"
        elif row[health_idx] == "red":
            row[health_idx] = f"[b red]{row[health_idx]}[/]"
    return row


@app.command(
    help="Returns high-level information about indices in a cluster, including backing indices for data streams.",
    short_help="Returns high-level information about indices in a cluster.",
)
def indices(
    ctx: typer.Context,
    index: IndexArgument = '*',
    header: HeaderOption | None = None,
    sort: SortOption | None = None,
    time: TimeOption | None = None,
    bytes: BytesOption | None = None,
    format: FormatOption = Format.text,
):
    client: Elasticsearch = get_client_from_ctx(ctx)
    params = get_cat_base_params_from_context(ctx, format)
    params.update(
        {
            "h": ",".join(header) if header else None,
            "s": ",".join(sort) if sort else None,
            "time": time,
            "bytes": bytes,
            "index": index,
        }
    )
    response = client.cat.indices(**params)
    response = select_from_context(ctx, response)
    pretty_print(response, format=params["format"], formatter=formatter)
