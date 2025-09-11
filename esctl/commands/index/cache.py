import typer

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    FormatOption,
    IndexArgument,
)
from esctl.selectors import select_from_context

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
    client = get_client_from_ctx(ctx)
    response = client.indices.clear_cache(index=index)
    response = select_from_context(ctx, response)
    pretty_print(response, format=format)
