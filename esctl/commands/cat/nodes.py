import typer

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
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
from esctl.utils import get_cat_base_params_from_context

app = typer.Typer()


@app.command(help="Returns information about a cluster’s nodes.")
def nodes(
    ctx: typer.Context,
    header: HeaderOption = None,
    sort: SortOption = None,
    time: TimeOption = None,
    bytes: BytesOption = None,
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
    client = get_client_from_ctx(ctx)
    response = client.cat.nodes(**params)
    response = select_from_context(ctx, response)
    pretty_print(response, format=params["format"])
