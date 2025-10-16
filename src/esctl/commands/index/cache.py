import typer

from config import Config
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    FormatOption,
    IndexArgument,
)
from esctl.selectors import select_from_context
from esctl.utils import get_root_ctx

app = typer.Typer(
    name="cache",
    help="Manage index cache.",
)


@app.command(
    help="Clears the cache of the specified index.",
)
def clear(
    ctx: typer.Context,
    index: IndexArgument,
    format: FormatOption = Format.text,
):
    client = Config.from_context(ctx).client
    response = client.indices.clear_cache(index=index)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=format,
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
