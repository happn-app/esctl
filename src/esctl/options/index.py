from typing import Annotated, Iterable
import typer

from esctl.config.config import Config


def complete_index(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
    return client.indices.get(index=f"{incomplete}*").body.keys()


IndexOption = Annotated[
    list[str],
    typer.Option(
        "--index",
        "-i",
        autocompletion=complete_index,
        help="The index or indices to use",
    ),
]

IndexArgument = Annotated[
    str,
    typer.Argument(
        autocompletion=complete_index,
        help="The index to use",
    ),
]
