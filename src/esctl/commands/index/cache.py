import typer

from esctl.config import Config
from esctl.options import (
    IndexArgument,
    OutputOption,
    Result,
)

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
    output: OutputOption = "json",
):
    client = Config.from_context(ctx).client
    response = client.indices.clear_cache(index=index)
    result: Result = ctx.obj["selector"](response)
    result.print(output)
