import typer
from rich.prompt import Confirm

from config import Config
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    RerouteDryRunOption,
    RerouteExplainOption,
    RerouteRetryFailedOption,
)

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def reroute(
    ctx: typer.Context,
    dry_run: RerouteDryRunOption = False,
    explain: RerouteExplainOption = False,
    retry_failed: RerouteRetryFailedOption = False,
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
    ).raw
    pretty_print(response, format=Format.json)
