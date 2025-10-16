from textwrap import dedent

import typer

from esctl.config import Config
from esctl.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    ActiveOnlyOption,
    BytesOption,
    DetailedOption,
    FormatOption,
    HeaderOption,
    IndexOption,
    SortOption,
    TimeOption,
)
from esctl.selectors import select_from_context
from esctl.utils import get_cat_base_params_from_context, get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


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
    header: HeaderOption | None = None,
    sort: SortOption | None = None,
    time: TimeOption | None = None,
    bytes: BytesOption | None = None,
    detailed: DetailedOption | None = False,
    index: IndexOption | None = None,
    active_only: ActiveOnlyOption = False,
    format: FormatOption = Format.text,
):
    params = get_cat_base_params_from_context(ctx, format)
    params.update(
        {
            "h": ",".join(header) if header else None,
            "s": ",".join(sort) if sort else None,
            "time": time,
            "active_only": active_only,
            "bytes": bytes,
            "detailed": detailed,
            "index": index,
        }
    )
    client = Config.from_context(ctx).client
    response = client.cat.recovery(**params)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=params["format"],
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
