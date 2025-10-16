import typer

from esctl.config import Config
from esctl.output import pretty_print
from esctl.params import (
    NodeOption,
    ParentTaskIdOption,
    TaskIdArgument,
)
from esctl.selectors import select_from_context
from esctl.utils import get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


@app.command(
    help="Cancels a running task.",
)
def cancel(
    ctx: typer.Context,
    task_id: TaskIdArgument,
    parent_task_id: ParentTaskIdOption | None = None,
    wait_for_completion: bool = False,
    actions: list[str] | None = None,
    nodes: NodeOption | None = None,
):
    params = {
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "wait_for_completion": wait_for_completion,
        "actions": actions,
        "nodes": nodes,
    }
    client = Config.from_context(ctx).client
    response = client.tasks.cancel(**params).raw
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=params["format"],
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
