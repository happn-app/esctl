from typing import Annotated, Iterable
import warnings

import typer

from esctl.config.config import Config


def complete_parent_task_id(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
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
    client = Config.from_context(ctx).client
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tasks = [
            tuple(split.strip() for split in line.split())
            for line in client.cat.tasks(format="text", h="task_id").body.splitlines()
        ]
        for (task_id,) in tasks:
            if task_id.startswith(incomplete):
                yield task_id


ParentTaskIdOption = Annotated[
    str | None,
    typer.Option(
        "--parent-task-id",
        help="The parent task ID to filter tasks by",
        autocompletion=complete_parent_task_id,
    ),
]

TaskIdArgument = Annotated[
    str,
    typer.Argument(
        help="The task ID to use",
        autocompletion=complete_task_id,
    ),
]
