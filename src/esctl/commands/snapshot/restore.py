from typing import Annotated, Iterable
import typer

from esctl.config import Config
from esctl.options import OutputOption, Result

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


def complete_repository(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
    repositories: list[str] = [
        repo["name"] for repo in client.snapshot.get_repository().body
    ]
    return [repo for repo in repositories if repo.startswith(incomplete)]


def complete_snapshot_name(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
    repository = ctx.params.get("repository")
    if not repository:
        return []
    snapshots = [
        snapshot["snapshot"]
        for snapshot in client.snapshot.get(
            repository=repository,
            snapshot=f"{incomplete}*",
        ).raw["snapshots"]
    ]
    snapshots.append("latest")
    return snapshots


def complete_snapshot_indices(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
    repository = ctx.params.get("repository")
    if not repository:
        return
    snapshot = ctx.params.get("snapshot")
    if not snapshot:
        snapshots = client.snapshot.get(
            repository=repository,
            snapshot="*",
        ).body["snapshots"]
        snapshot = snapshots[-1]["snapshot"] if snapshots else None
    if not snapshot:
        return

    indices = client.snapshot.get(
        repository=repository,
        snapshot=snapshot,
    ).body["snapshots"][0]["indices"]
    for index in indices:
        if index.startswith(incomplete):
            yield index


RestoreSnapshotNameArgument = Annotated[
    str,
    typer.Argument(
        help="The name of the snapshot to restore",
        autocompletion=complete_snapshot_name,
        callback=snapshot_callback,
    ),
]

RestoreSnapshotIndexOption = Annotated[
    list[str],
    typer.Option(
        "--index",
        "-i",
        help="The index to restore from the snapshot",
        autocompletion=complete_snapshot_indices,
    ),
]


@app.command(
    help="Restore a snapshot from a repository.",
)
def restore(
    ctx: typer.Context,
    repository: Annotated[
        str,
        typer.Argument(
            help="The name of the repository to restore the snapshot from",
            autocompletion=complete_repository,
        ),
    ],
    snapshot: RestoreSnapshotNameArgument = "latest",
    index: RestoreSnapshotIndexOption = ["*"],
    output: OutputOption = "json",
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
    )
    result: Result = ctx.obj["selector"](response)
    if output == "json" or output == "yaml":
        result.print(output)
        return
    else:
        result.print("json")
