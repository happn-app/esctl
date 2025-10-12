import typer

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    FormatOption,
    IndexArgument,
    SettingsKeyArgument,
)
from esctl.selectors import select_from_context
from esctl.utils import get_root_ctx

app = typer.Typer(
    name="settings",
    help="Manage index settings.",
)


@app.command(
    help="Get the settings of the specified index.",
)
def get(
    ctx: typer.Context,
    index: IndexArgument,
    name: SettingsKeyArgument,
    format: FormatOption = Format.text,
):
    client = get_client_from_ctx(ctx)
    response = client.indices.get_settings(index=index, name=name)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=format,
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )


@app.command(
    help="Updates the index settings of the specified index.",
)
def update(
    ctx: typer.Context,
    index: IndexArgument,
    name: SettingsKeyArgument,
    value: str = typer.Argument(
        ..., help="The value to set for the specified setting key."
    ),
    format: FormatOption = Format.text,
):
    client = get_client_from_ctx(ctx)
    body = {"settings": {name: value}}
    response = client.indices.put_settings(index=index, body=body)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=format,
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
