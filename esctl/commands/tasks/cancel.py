import typer

from esctl.config import get_client_from_ctx
from esctl.output import pretty_print
from esctl.params import (
    NodeOption,
    ParentTaskIdOption,
    TaskIdArgument,
)
from esctl.selectors import select_from_context

app = typer.Typer()


@app.command(
    help="Cancels a running task.",
)
def cancel(
    ctx: typer.Context,
    task_id: TaskIdArgument,
    parent_task_id: ParentTaskIdOption = None,
    wait_for_completion: bool = False,
    actions: list[str] = None,
    nodes: NodeOption = None,
):
    params = {
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "wait_for_completion": wait_for_completion,
        "actions": actions,
        "nodes": nodes,
    }
    client = get_client_from_ctx(ctx)
    response = client.tasks.cancel(**params).raw
    response = select_from_context(ctx, response)
    pretty_print(response, format=params["format"])
