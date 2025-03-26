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

app = typer.Typer()


@app.command(help="Provides an explanation for a shard’s current allocation.")
def allocation_explain(
    ctx: typer.Context,
    include_disk_info: ExplainIncludeDiskInfoOption = False,
    include_yes_decisions: ExplainIncludeYesDecisionsOption = False,
    node: NodeOption = None,
    shard: ShardOption = None,
    index: IndexOption = None,
    primary: ExplainPrimaryShardOption = False,
):
    client = get_client_from_ctx(ctx)
    response = client.cluster.allocation_explain(
        include_disk_info=include_disk_info,
        include_yes_decisions=include_yes_decisions,
        current_node=node,
        shard=shard,
        index=index,
        primary=primary,
    ).raw
    pretty_print(response, format=Format.json)
