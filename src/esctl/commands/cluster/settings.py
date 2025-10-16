from copy import deepcopy

import typer
from rich import print
from rich.prompt import Confirm

from esctl.config import Config
from esctl.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    FormatOption,
    SettingsKeyArgument,
    SettingsTransientOption,
    SettingsValueArgument,
)
from esctl.utils import get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def settings(
    ctx: typer.Context,
    settings_key: SettingsKeyArgument = "",
    settings_value: SettingsValueArgument = "",
    transient: SettingsTransientOption = False,
    format: FormatOption = Format.text,
    with_defaults: bool = True,
    filter: str | None = None,
):
    client = Config.from_context(ctx).client
    if not settings_key and not settings_value:
        # Get the current settings, without the defaults
        response = client.cluster.get_settings(
            include_defaults=with_defaults, flat_settings=True
        ).body
        all_settings: dict = deepcopy(response.get("defaults", {}))
        all_settings.update(response["persistent"])
        all_settings.update(response["transient"])
        # Filter the settings if needed
        if filter:
            all_settings = {k: v for k, v in all_settings.items() if filter in k}
        data = "key value\n" + "\n".join([f"{k} {v}" for k, v in all_settings.items()])
        pretty_print(
            data,
            format=Format.text,
            pretty=get_root_ctx(ctx).obj.get("pretty", True),
        )
        return

    if settings_key and not settings_value:
        response = client.cluster.get_settings(
            flat_settings=True,
            include_defaults=with_defaults,
        ).body
        all_settings: dict = deepcopy(response.get("defaults", {}))
        all_settings.update(response["persistent"])
        all_settings.update(response["transient"])
        # Filter the settings if needed
        if filter:
            all_settings = {k: v for k, v in all_settings.items() if filter in k}
        print(f"[blue b]{settings_key}[/]: ", all_settings[settings_key])
    settings_value, type_ = (
        settings_value.split(":", 1)
        if ":" in settings_value
        else (settings_value, "str")
    )  # type: ignore
    cast = {
        "str": str,
        "int": int,
        "float": float,
        "bool": lambda v: v.lower() in ("true", "1", "yes", "on"),
        "null": lambda v: None,
    }.get(type_, str)
    params = {settings_key: cast(settings_value)}  # type: ignore
    print(params)
    confirm = Confirm.ask(
        "You are about to change the cluster configuration, are you sure ?",
        default=False,
    )
    if not confirm:
        typer.echo("Operation aborted.")
        raise typer.Abort()
    if transient:
        response = client.cluster.put_settings(transient=params)  # type: ignore
    else:
        response = client.cluster.put_settings(persistent=params)  # type: ignore
    pretty_print(
        response,
        format=Format.json,
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
