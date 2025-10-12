import typer

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    FormatOption,
    HeaderOption,
    SortOption,
)
from esctl.selectors import select_from_context
from esctl.utils import get_cat_base_params_from_context, get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


@app.command(
    help="Lists the templates in the cluster.",
)
def templates(
    ctx: typer.Context,
    header: HeaderOption | None = None,
    sort: SortOption | None = None,
    format: FormatOption = Format.text,
):
    params = get_cat_base_params_from_context(ctx, format)
    params.update(
        {
            "h": ",".join(header) if header else None,
            "s": ",".join(sort) if sort else None,
        }
    )
    client = get_client_from_ctx(ctx)
    response = client.cat.templates(**params)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=params["format"],
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
