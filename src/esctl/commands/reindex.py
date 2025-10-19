from enum import Enum
from typing import Annotated
import typer

from esctl.config import Config
from esctl.options import IndexArgument, OutputOption, Result

app = typer.Typer(rich_markup_mode="rich")


class Conflict(str, Enum):
    abort = "abort"
    proceed = "proceed"


@app.callback(
    help="Reindex a set of documents from one index to another.",
    invoke_without_command=True,
)
def reindex(
    ctx: typer.Context,
    source: IndexArgument,
    dest: IndexArgument,
    wait_for_completion: bool = False,
    refresh: bool = False,
    slices: Annotated[
        int | None,
        typer.Option(
            "--slices",
            "-s",
            help="The number of slices to use for the reindexing operation. Defaults to 'auto'.",
        ),
    ] = None,
    require_alias: bool = False,
    conflicts: Conflict = Conflict.abort,
    output: OutputOption = "json",
):
    source_dict = {
        "index": source,
    }
    dest_dict = {
        "index": dest,
    }
    if slices is None:
        slices = "auto"  # type: ignore
    client = Config.from_context(ctx).client
    response = client.reindex(
        dest=dest_dict,
        source=source_dict,
        conflicts=conflicts,
        refresh=refresh,
        wait_for_completion=wait_for_completion,
        slices=slices,
        require_alias=require_alias,
    )
    result: Result = ctx.obj["selector"](response)
    if output == "json" or output == "yaml":
        result.print(output)
    else:
        result.print("json")
