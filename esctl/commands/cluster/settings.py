from copy import deepcopy

import typer
from rich import print
from rich.prompt import Confirm

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    FormatOption,
    SettingsKeyArgument,
    SettingsTransientOption,
    SettingsValueArgument,
)

app = typer.Typer()


@app.command()
def settings(
    ctx: typer.Context,
    settings_key: SettingsKeyArgument = None,
    settings_value: SettingsValueArgument = None,
    transient: SettingsTransientOption = False,
    format: FormatOption = Format.text,
):
    client = get_client_from_ctx(ctx)
    if settings_key is None and settings_value is None:
        # Get the current settings, without the defaults
        response = client.cluster.get_settings(
            include_defaults=True, flat_settings=True
        ).body
        all_settings: dict = deepcopy(response["defaults"])
        all_settings.update(response["persistent"])
        all_settings.update(response["transient"])
        data = "key value\n" + "\n".join([f"{k} {v}" for k, v in all_settings.items()])
        pretty_print(data, format=Format.text)
        return

    if settings_key is not None and settings_value is None:
        response = client.cluster.get_settings(
            flat_settings=True, include_defaults=True
        ).body
        all_settings: dict = deepcopy(response["default"])
        all_settings.update(response["persistent"])
        all_settings.update(response["transient"])
        print(f"[blue b]{settings_key}[/]: ", all_settings[settings_key])

    if settings_key is None and settings_value is not None:
        # How did you get here ???
        raise typer.BadParameter("You must provide a settings key")

    confirm = Confirm.ask(
        "You are about to change the cluster configuration, are you sure ?",
        default=False,
    )
    if not confirm:
        typer.echo("Operation aborted.")
        raise typer.Abort()
    param_key = "transient" if transient else "persistent"
    params = {param_key: {settings_key: settings_value}}
    response = client.cluster.put_settings(**params)
    pretty_print(response, format=Format.json)
