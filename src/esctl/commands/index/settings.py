import json
from typing import Annotated
import typer

from esctl.config import Config
from esctl.options import (
    IndexArgument,
    OutputOption,
    Result,
)

app = typer.Typer(
    name="settings",
    help="Manage index settings.",
)


def complete_settings_key(incomplete: str) -> list[str]:
    settings_keys = [
        "index.analysis.analyzer.autocomplete.char_filter",
        "index.analysis.analyzer.autocomplete.filter",
        "index.analysis.analyzer.autocomplete.tokenizer",
        "index.analysis.analyzer.autocomplete.type",
        "index.analysis.analyzer.search_autocomplete.char_filter",
        "index.analysis.analyzer.search_autocomplete.filter",
        "index.analysis.analyzer.search_autocomplete.tokenizer",
        "index.analysis.analyzer.search_autocomplete.type",
        "index.analysis.tokenizer.autocomplete_tokenizer.max_gram",
        "index.analysis.tokenizer.autocomplete_tokenizer.min_gram",
        "index.analysis.tokenizer.autocomplete_tokenizer.token_chars",
        "index.analysis.tokenizer.autocomplete_tokenizer.type",
        "index.creation_date",
        "index.number_of_replicas",
        "index.number_of_shards",
        "index.provided_name",
        "index.routing.allocation.include._tier_preference",
        "index.uuid",
        "index.version.created",
    ]
    return [key for key in settings_keys if key.startswith(incomplete)]


SettingsKeyArgument = Annotated[
    str,
    typer.Argument(
        help="The setting key to get or update.",
        autocompletion=complete_settings_key,
    ),
]


@app.command(
    help="Get the settings of the specified index.",
)
def get(
    ctx: typer.Context,
    index: IndexArgument,
    name: SettingsKeyArgument,
    output: OutputOption = "table",
    with_defaults: Annotated[
        bool,
        typer.Option(
            "--with-defaults/--no-with-defaults", help="Include default settings."
        ),
    ] = False,
):
    client = Config.from_context(ctx).client
    response = client.indices.get_settings(
        index=index,
        name=name,
        flat_settings=True,
        include_defaults=with_defaults,
    )
    result: Result = ctx.obj["selector"](response)
    if output == "json" or output == "yaml":
        result.print(output)
        return
    # For table or text output, we need to iterate over the response to get the settings for each index.
    result.value = [
        {
            "index": index_name,
            "key": key,
            "value": json.dumps(value),
        }
        for index_name, settings in response.body.items()
        for key, value in settings["settings"].items()
    ]


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
    output: OutputOption = "json",
):
    client = Config.from_context(ctx).client
    settings = {name: value}
    response = client.indices.put_settings(index=index, settings=settings)
    result: Result = ctx.obj["selector"](response)
    if output == "json" or output == "yaml":
        result.print(output)
    else:
        result.print("json")  # Default to json for structured output?
