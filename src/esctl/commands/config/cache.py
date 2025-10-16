from http import HTTPMethod
from typing import Annotated
import orjson
import typer

from esctl.transport import Cache
from esctl.config import get_root_ctx, ESConfigType
from esctl.constants import ESCTL_TTL_CONFIG_PATH

app = typer.Typer(rich_markup_mode="rich")


@app.command(help="Purge the local cache for the current context")
def purge(ctx: typer.Context):
    root_ctx: typer.Context = get_root_ctx(ctx)
    conf: ESConfigType = root_ctx.obj["context"]
    cache = Cache(conf.name)
    cache.clear()
    typer.echo(f"Cache purged for context {root_ctx.obj['config'].current_context}")


@app.command(help="Set TTL for a given ES API call")
def ttl(
    method: HTTPMethod = typer.Argument(help="HTTP method, e.g. GET, HEAD"),
    target: str = typer.Argument(help="API endpoint, e.g. /_cluster/health"),
    ttl: int = typer.Argument(help="TTL in seconds, e.g. 300 for 5 minutes"),
    match_all: Annotated[
        bool,
        typer.Option(
            "--match-all/--no-match-all",
            help="Should the pattern match query params and fragments as well",
        ),
    ] = False,
):
    ttls = orjson.loads(ESCTL_TTL_CONFIG_PATH.read_bytes() or b"{}")
    qp_pattern = r"(\?.*)?(#.*)?" if match_all else ""
    pattern = rf"^{method.upper()} {target}{qp_pattern}$"
    original = ttls.get(pattern)
    if original is not None:
        typer.echo(
            f"Overriding existing TTL of {original} seconds for pattern '{pattern}'"
        )
    ttls[pattern] = ttl
    ESCTL_TTL_CONFIG_PATH.write_bytes(orjson.dumps(ttls, option=orjson.OPT_INDENT_2))
    typer.echo(f"Set TTL for pattern '{pattern}' to {ttl} seconds")
