from typing import Annotated
import typer
from rich.prompt import Confirm

from esctl.config import Config
from esctl.options import (
    OutputOption,
    Result,
)

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def reroute(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option(
            help="If true, then the request simulates the operation only and returns the resulting state.",
        ),
    ] = False,
    explain: Annotated[
        bool,
        typer.Option(
            help="If true, then the response contains an explanation of why the commands can or cannot be executed. ",
        ),
    ] = False,
    retry_failed: Annotated[
        bool,
        typer.Option(
            help="If true, then retries allocation of shards that are blocked due to too many subsequent allocation failures. ",
        ),
    ] = False,
    output: OutputOption = "json",
):
    client = Config.from_context(ctx).client
    if not dry_run:
        # Do not ask for confirmation if dry-run is enabled
        # Dry run doesn't actually do anything, just planning so it's okay
        confirm = Confirm.ask(
            "You are about to reshard the cluster, are you sure ?", default=False
        )
        if not confirm:
            typer.echo("Operation aborted.")
            raise typer.Abort()
    response = client.cluster.reroute(
        dry_run=dry_run, explain=explain, retry_failed=retry_failed
    )
    result: Result = ctx.obj["selector"](response)
    result.print(output=output)
