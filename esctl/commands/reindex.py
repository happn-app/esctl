import typer

from esctl.config import get_client_from_ctx
from esctl.models.enums import Conflict, Format
from esctl.output import pretty_print
from esctl.params import IndexArgument
from esctl.selectors import select_from_context

app = typer.Typer(rich_markup_mode="rich")

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
    slices: int | None = None,
    require_alias: bool = False,
    conflicts: Conflict = Conflict.abort,
):
    source_dict = {
        "index": source,
    }
    dest_dict = {
        "index": dest,
    }
    if slices is None:
        slices = "auto"  # type: ignore
    client = get_client_from_ctx(ctx)
    response = client.reindex(
        dest=dest_dict,
        source=source_dict,
        conflicts=conflicts,
        refresh=refresh,
        wait_for_completion=wait_for_completion,
        slices=slices,
        require_alias=require_alias,
    ).raw
    response = select_from_context(ctx, response)
    pretty_print(response, format=Format.json)
