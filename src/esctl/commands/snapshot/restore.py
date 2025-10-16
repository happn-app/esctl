from typing import Annotated
import typer

from esctl.config import Config
from esctl.enums import Format
from esctl.output import pretty_print
from esctl.params import IndexOption
from esctl.selectors import select_from_context
from esctl.utils import get_root_ctx

app = typer.Typer()


def snapshot_callback(ctx: typer.Context, value: str) -> str:
    if value != "latest":
        return value
    client = Config.from_context(ctx).client
    repository: str = ctx.params["repository"]
    snapshots = client.snapshot.get(repository=repository, snapshot="*").body[
        "snapshots"
    ]
    snapshot = snapshots[-1]["snapshot"] if snapshots else None  # type: ignore
    if snapshot is None:
        raise typer.BadParameter(f"No snapshots found in repository {repository}")
    return snapshot


@app.command(
    help="Restore a snapshot from a repository.",
)
def restore(
    ctx: typer.Context,
    repository: str,
    snapshot: Annotated[str, typer.Argument(callback=snapshot_callback)] = "latest",
    index: IndexOption | None = None,
):
    """
    Restore a snapshot from a repository.
    """
    client = Config.from_context(ctx).client
    if not repository:
        return

    index = client.snapshot.get(repository=repository, snapshot=snapshot).body[
        "snapshots"
    ][0]["indices"]
    response = client.snapshot.restore(
        repository=repository,
        snapshot=snapshot,
        indices=index,
    ).raw
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=Format.json,
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
