from typing import Annotated
import typer

from esctl.config import Config
from esctl.options import (
    IndexOption,
    NodeOption,
    ShardOption,
    OutputOption,
    Result,
)

app = typer.Typer(rich_markup_mode="rich")


@app.command(help="Provides an explanation for a shard’s current allocation.")
def allocation_explain(
    ctx: typer.Context,
    include_disk_info: Annotated[
        bool,
        typer.Option(
            "--include-disk-info",
            "--disk-info",
            "-d",
            help="Returns information about disk usage and shard sizes.",
        ),
    ] = False,
    include_yes_decisions: Annotated[
        bool,
        typer.Option(
            "--include-yes-decisions",
            "--yes-decisions",
            "-y",
            help="Returns YES decisions in explanation.",
        ),
    ] = False,
    node: NodeOption | None = None,
    shard: ShardOption | None = None,
    index: IndexOption | None = None,
    primary: Annotated[
        bool,
        typer.Option(
            "--primary",
            "-p",
            help="Returns explanation for the primary shard for the given shard ID",
        ),
    ] = False,
    output: OutputOption = "json",
):
    client = Config.from_context(ctx).client
    if index is not None and len(index) > 1:
        typer.echo("Error: Only one index can be specified.", err=True)
        raise typer.Exit(code=1)
    index_ = index[0] if index else None
    response = client.cluster.allocation_explain(
        include_disk_info=include_disk_info,
        include_yes_decisions=include_yes_decisions,
        current_node=node,
        shard=shard,
        index=index_,
        primary=primary,
    )
    result: Result = ctx.obj["selector"](response)
    result.print(output=output)
