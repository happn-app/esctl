import typer

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    ExplainIncludeDiskInfoOption,
    ExplainIncludeYesDecisionsOption,
    ExplainPrimaryShardOption,
    IndexOption,
    NodeOption,
    ShardOption,
)
from esctl.utils import get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


@app.command(help="Provides an explanation for a shard’s current allocation.")
def allocation_explain(
    ctx: typer.Context,
    include_disk_info: ExplainIncludeDiskInfoOption = False,
    include_yes_decisions: ExplainIncludeYesDecisionsOption = False,
    node: NodeOption | None = None,
    shard: ShardOption | None = None,
    index: IndexOption | None = None,
    primary: ExplainPrimaryShardOption = False,
):
    client = get_client_from_ctx(ctx)
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
    ).raw
    pretty_print(
        response,
        format=Format.json,
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
