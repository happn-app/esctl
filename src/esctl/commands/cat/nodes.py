import typer

from esctl.config import Config
from esctl.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    BytesOption,
    FormatOption,
    FullIdOption,
    HeaderOption,
    IncludeUnloadedSegmentsOption,
    SortOption,
    TimeOption,
)
from esctl.selectors import select_from_context
from esctl.utils import get_cat_base_params_from_context, get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


@app.command(help="Returns information about a cluster’s nodes.")
def nodes(
    ctx: typer.Context,
    header: HeaderOption | None = None,
    sort: SortOption | None = None,
    time: TimeOption | None = None,
    bytes: BytesOption | None = None,
    full_id: FullIdOption = True,
    include_unloaded_segments: IncludeUnloadedSegmentsOption = False,
    format: FormatOption = Format.text,
):
    params = get_cat_base_params_from_context(ctx, format)
    params.update(
        {
            "h": ",".join(header) if header else None,
            "s": ",".join(sort) if sort else None,
            "time": time,
            "full_id": full_id,
            "bytes": bytes,
            "include_unloaded_segments": include_unloaded_segments,
        }
    )
    client = Config.from_context(ctx).client
    response = client.cat.nodes(**params)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=params["format"],
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
