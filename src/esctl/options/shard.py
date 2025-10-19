from typing import Annotated, Iterable
import typer

from esctl.config.config import Config


def complete_shard(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
    index = ctx.params.get("index", ctx.params.get("indices", None))
    shards = client.cat.shards(format="text", h="shard", index=index).body.splitlines()
    for shard in shards:
        if shard.startswith(incomplete):
            yield shard


ShardOption = Annotated[
    int | None,
    typer.Option(
        "--shard",
        "-s",
        autocompletion=complete_shard,
        help="The shard ID to use",
    ),
]
