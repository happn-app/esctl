from itertools import product
from typing import Iterable
import warnings

import typer

from esctl.config import get_client_from_ctx, read_config


def complete_column(
    ctx: typer.Context, incomplete: str
) -> Iterable[str | tuple[str, str]]:
    client = get_client_from_ctx(ctx)
    command_name: str = ctx.command.name or ""
    response: str = getattr(client.cat, command_name)(help=True).body
    columns = [
        {
            "name": column.split("|")[0].strip(),
            "aliases": column.split("|")[1].strip().split(","),
            "description": column.split("|")[2].strip(),
        }
        for column in response.splitlines()
    ]
    for column in columns:
        if column["name"].lower().startswith(incomplete) or any(
            incomplete in alias for alias in column["aliases"]
        ):
            yield (column["name"], column["description"])


def complete_sort(
    ctx: typer.Context, incomplete: str
) -> Iterable[str | tuple[str, str]]:
    columns = list(complete_column(ctx, incomplete.split(":")[0]))
    orders = ["asc", "desc"]
    return [
        (f"{column}:{order}", description)
        for (column, description), order in product(columns, orders)
        if column.startswith(incomplete.split(":")[0])
    ]


def complete_index(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
    indices = client.cat.indices(format="text", h="index").body.splitlines()
    for index in indices:
        if index.startswith(incomplete):
            yield index


def complete_node(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
    nodes = [n["name"] for n in client.nodes.info().body["nodes"].values()]
    for node in nodes:
        if node.startswith(incomplete):
            yield node


def complete_shard(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
    index = ctx.params.get("index", ctx.params.get("indices", None))
    shards = client.cat.shards(format="text", h="shard", index=index).body.splitlines()
    for shard in shards:
        if shard.startswith(incomplete):
            yield shard


def complete_context(incomplete: str):
    cfg = read_config()
    return [
        context for context in cfg.contexts.keys() if context.startswith(incomplete)
    ]


def complete_settings_key(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
    settings = client.cluster.get_settings(
        include_defaults=True, flat_settings=True
    ).body
    setting_keys = set(settings["defaults"].keys())
    setting_keys.update(settings["persistent"].keys())
    setting_keys.update(settings["transient"].keys())
    for key in setting_keys:
        if key.startswith(incomplete):
            yield key


def complete_parent_task_id(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tasks_with_parents = [
            tuple(split.strip() for split in line.split())
            for line in client.cat.tasks(
                format="text", h="task_id,parent_task_id"
            ).body.splitlines()
        ]
        for task_id, parent_task_id in tasks_with_parents:
            if parent_task_id != "-":
                continue
            if task_id.startswith(incomplete):
                yield task_id


def complete_task_id(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tasks = [
            tuple(split.strip() for split in line.split())
            for line in client.cat.tasks(format="text", h="task_id").body.splitlines()
        ]
        for (task_id,) in tasks:
            if task_id.startswith(incomplete):
                yield task_id


def complete_repository(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
    repositories = [repo["name"] for repo in client.snapshot.get_repository().body]
    for repository in repositories:
        if repository.startswith(incomplete):
            yield repository


def complete_snapshot_name(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
    repository = ctx.params.get("repository")
    if not repository:
        return
    snapshots = [
        snapshot["snapshot"]
        for snapshot in client.snapshot.get(
            repository=repository,
            snapshot="*",
        ).raw["snapshots"]
    ]
    for snapshot in snapshots:
        if snapshot.startswith(incomplete):
            yield snapshot


def complete_snapshot_indices(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = get_client_from_ctx(ctx)
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
