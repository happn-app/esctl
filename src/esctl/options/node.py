from typing import Annotated, Iterable
import typer

from esctl.config.config import Config


def complete_node(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
    nodes = [n["name"] for n in client.nodes.info().body["nodes"].values()]
    return [node for node in nodes if node.startswith(incomplete)]


NodeOption = Annotated[
    str | None,
    typer.Option(
        "--node",
        "-n",
        autocompletion=complete_node,
        help="The node name to use.",
    ),
]
