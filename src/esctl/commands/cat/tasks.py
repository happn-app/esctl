from contextlib import suppress
from textwrap import dedent

import typer

from config import Config
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    FormatOption,
    HeaderOption,
    NodeOption,
    ParentTaskIdOption,
    SortOption,
    TimeOption,
)
from esctl.selectors import select_from_context
from esctl.utils import get_cat_base_params_from_context, get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


def formatter(header: list[str], row: list[str]) -> list[str]:
    with suppress(ValueError):
        state_idx = header.index("state")
        if row[state_idx] == "STARTED":
            row[state_idx] = f"[b green]{row[state_idx]}[/]"
        elif row[state_idx] == "RELOCATING":
            row[state_idx] = f"[b yellow]{row[state_idx]}[/]"
        elif row[state_idx] == "INITIALIZING":
            row[state_idx] = f"[b blue]{row[state_idx]}[/]"
        elif row[state_idx] == "UNASSIGNED":
            row[state_idx] = f"[b red]{row[state_idx]}[/]"
    return row


@app.command(
    help=dedent(
        """
        Returns information about tasks currently executing in the cluster,
        similar to the task management API.
        """
    )
)
def tasks(
    ctx: typer.Context,
    detailed: bool = False,
    header: HeaderOption | None = None,
    sort: SortOption | None = None,
    format: FormatOption = Format.text,
    nodes: NodeOption | None = None,
    time: TimeOption | None = None,
    parent_task_id: ParentTaskIdOption | None = None,
):
    params = get_cat_base_params_from_context(ctx, format)
    params.update(
        {
            "h": header,
            "s": sort,
            "time": time,
            "detailed": detailed,
            "nodes": nodes,
            "parent_task_id": parent_task_id,
        }
    )
    client = Config.from_context(ctx).client
    response = client.cat.tasks(**params)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=params["format"],
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
