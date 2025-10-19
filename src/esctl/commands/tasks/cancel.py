import typer

from esctl.config import Config
from esctl.options import (
    NodeOption,
    ParentTaskIdOption,
    TaskIdArgument,
    OutputOption,
    Result,
)

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
    output: OutputOption = "table",
):
    params = {
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "wait_for_completion": wait_for_completion,
        "actions": actions,
        "nodes": nodes,
    }
    client = Config.from_context(ctx).client
    response = client.tasks.cancel(**params)
    result: Result = ctx.obj["selector"](response)
    result.print(output=output)
