import typer

from esctl.cache import Cache
from esctl.models.config.base import ESConfig
from esctl.utils import get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


@app.command(help="Purge the local cache for the current context")
def purge(ctx: typer.Context):
    root_ctx: typer.Context = get_root_ctx(ctx)
    conf: ESConfig = root_ctx.obj["context"]
    cache = Cache(conf.name)
    cache.clear()
    typer.echo(f"Cache purged for context {root_ctx.obj['config'].current_context}")
