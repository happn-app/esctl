import time
from typing import Annotated, Iterable

from rich import print
import typer

from esctl.config import Config
from esctl.options import OutputOption, Result

app = typer.Typer()


def complete_repository(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
    return [
        repo
        for repo in client.snapshot.get_repository(name=f"{incomplete}*").body
        if repo.startswith(incomplete)
    ]


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
        ).body["snapshots"]
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
    include_system_indices: Annotated[
        bool,
        typer.Option(
            "--include-system-indices/--no-include-system-indices",
            help="Whether to include system indices in the restore",
        ),
    ] = False,
    index: RestoreSnapshotIndexOption | None = None,
    close_all: Annotated[
        bool,
        typer.Option(
            "--close-all/--no-close-all",
            help="Whether to close all open indices before restoring the snapshot",
        ),
    ] = True,
    reroute: Annotated[
        bool,
        typer.Option(
            "--reroute/--no-reroute",
            help="Whether to reroute shards after restoring the snapshot",
        ),
    ] = True,
    recreate_repository: Annotated[
        bool,
        typer.Option(
            "--recreate-repository/--no-recreate-repository",
            help="Whether to recreate the repository before restoring the snapshot",
        ),
    ] = False,
    output: OutputOption = "json",
):
    """
    Restore a snapshot from a repository.
    """
    client = Config.from_context(ctx).client

    if snapshot == "latest" and recreate_repository:
        start = time.time()
        repository_config = client.snapshot.get_repository(name=repository).body[
            repository
        ]
        # Recreate the repository
        client.snapshot.delete_repository(name=repository)
        client.snapshot.create_repository(
            name=repository,
            body={
                "type": repository_config["type"],
                "settings": repository_config["settings"],
            },
        )
        print(f"Recreated repository in [b blue]{time.time() - start:.2f}[/]s")

    if snapshot == "latest":
        start = time.time()
        snapshot = next(
            iter(
                client.snapshot.get(
                    repository=repository,
                    snapshot="*",
                    sort="start_time",
                    order="desc",
                ).body["snapshots"]
            )
        )["snapshot"]
        print(
            (
                f"Resolved latest snapshot to [b green]{snapshot}[/] in repository "
                f"[b purple]{repository}[/] in [b blue]{time.time() - start:.2f}[/]s"
            )
        )

    indices = index
    if indices is None:
        if include_system_indices:
            indices = ["*"]
        else:
            indices = ["*", "-.*"]

    if close_all:
        start = time.time()
        open_indices = client.indices.get_alias(index="*").body.keys()
        for idx in open_indices:
            client.indices.close(index=idx)
        print(
            f"Closed all open indices before restoring the snapshot in [b blue]{time.time() - start:.2f}[/]s"
        )
    start = time.time()
    response = client.snapshot.restore(
        repository=repository,
        snapshot=snapshot,
        indices=indices,
    )
    print(
        (
            f"Restored snapshot [b green]{snapshot}[/] from repository "
            f"[b purple]{repository}[/] completed in [b blue]{time.time() - start:.2f}[/]s"
        )
    )
    result: Result = ctx.obj["selector"](response)
    if output == "json" or output == "yaml":
        result.print(output)
        return
    else:
        result.print("json")
    if reroute:
        start = time.time()
        client.cluster.reroute(retry_failed=True)
        print(
            (
                f"Rerouted cluster after restoring snapshot [b green]{snapshot}[/b] "
                f"from repository [b purple]{repository}[/]in [b blue]{time.time() - start:.2f}[/]s"
            )
        )
