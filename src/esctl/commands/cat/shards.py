from contextlib import suppress
from textwrap import dedent

import typer

from config import Config
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    BytesOption,
    FormatOption,
    HeaderOption,
    IndexOption,
    SortOption,
    TimeOption,
)
from esctl.selectors import select_from_context
from esctl.utils import get_cat_base_params_from_context, get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


def formatter(header: list[str], row: list[str]) -> list[str]:
    with suppress(ValueError):
        state_idx = header.index("state")
        if row[state_idx] == "STARTED":
            row[state_idx] = f"[b green]{row[state_idx]}[/]"
        elif row[state_idx] == "RELOCATING":
            row[state_idx] = f"[b yellow]{row[state_idx]}[/]"
        elif row[state_idx] == "INITIALIZING":
            row[state_idx] = f"[b blue]{row[state_idx]}[/]"
        elif row[state_idx] == "UNASSIGNED":
            row[state_idx] = f"[b red]{row[state_idx]}[/]"
    return row


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
    header: HeaderOption | None = None,
    sort: SortOption | None = None,
    time: TimeOption | None = None,
    bytes: BytesOption | None = None,
    format: FormatOption = Format.text,
):
    params = get_cat_base_params_from_context(ctx, format)
    params.update(
        {
            "h": header,
            "s": sort,
            "time": time,
            "bytes": bytes,
            "index": index,
        }
    )
    client = Config.from_context(ctx).client
    response = client.cat.shards(**params)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=params["format"],
        formatter=formatter,
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
