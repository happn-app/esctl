import typer

from esctl.config import get_client_from_ctx
from esctl.params import IndexOption

app = typer.Typer()


@app.command(
    help="Restore a snapshot from a repository.",
)
def restore(
    ctx: typer.Context,
    repository: str,
    snapshot: str,
    index: IndexOption = None,
):
    """
    Restore a snapshot from a repository.
    """
    client = get_client_from_ctx(ctx)
    if not repository:
        return
    snapshot = ctx.params.get("snapshot")
    if not snapshot:
        snapshots = client.snapshot.get(repository=repository, snapshot="*", format="json").body["snapshots"]
        snapshot = snapshots[-1]["snapshot"] if snapshots else None
    if not snapshot:
        return

    index = client.snapshot.get(repository=repository, snapshot=snapshot, format="json").body["snapshots"][0]["indices"]
    response = client.snapshot.restore(
        repository=repository,
        snapshot=snapshot,
        indices=index,
    ).raw
    response = select_from_context(ctx, response)
    pretty_print(response, format=Format.json)
