from itertools import product
from typing import Iterable
import warnings

import typer

from esctl.config import get_client_from_ctx, read_config


def complete_column(ctx: typer.Context, incomplete: str) -> Iterable[str | tuple[str, str]]:
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


def complete_sort(ctx: typer.Context, incomplete: str) -> Iterable[str | tuple[str, str]]:
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
    nodes = [n["name"] for n in client.cat.nodes(format="json", h=["name"]).body] # type: ignore
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
            for line in client.cat.tasks(format="text", h="task_id,parent_task_id").body.splitlines()
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
        for task_id, in tasks:
            if task_id.startswith(incomplete):
                yield task_id
