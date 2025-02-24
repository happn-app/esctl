import os
import shutil
import subprocess

from rich.console import Console
from rich.table import Table
import typer
from typing_extensions import Annotated

from esctl.completions import complete_context
from esctl.config import Config

app = typer.Typer()


@app.command(
    name="contexts",
    help="Lists all available ES Contexts saved in the esctl configuration file",
)
def list_contexts(
    ctx: typer.Context,
    with_password: Annotated[bool, typer.Option(
        "--with-password",
        help="Show the password in the output",
    )] = False,
):
    config: Config = ctx.obj["config"]
    console = Console()
    table = Table("", "Name", "URL", "Username", "Password", title="Available Contexts")
    for context_name, context in config.contexts.items():
        table.add_row(
            "" if context_name != config.current_context else "→",
            context_name if context_name != config.current_context else f"[b green]{context_name}[/]",
            context.url,
            context.username,
            context.password if with_password else context.censored_password,
        )
    console.print(table)


@app.command(help="Add an ElasticSearch server to the esctl configuration file")
def add_context(
    ctx: typer.Context,
    context_name: Annotated[str, typer.Argument(help="Name of the context")],
    host: Annotated[
        str, typer.Option("--host", "-h", help="Hostname of the cluster")
    ] = "localhost",
    port: Annotated[
        int, typer.Option("--port", "-p", help="Port the ES master listens on")
    ] = 9200,
    username: Annotated[
        str,
        typer.Option(
            "--username",
            "-u",
            help="Username of the user to connect as, using basic auth",
        ),
    ] = None,
    password: Annotated[
        str,
        typer.Option(
            "--password",
            "-p",
            help="Password of the user to connect as, using basic auth",
        ),
    ] = None,
):
    ctx.obj["config"].add_context(context_name, host, port, username, password)
    typer.echo(f"Context {context_name} added")


@app.command(help="Remove an ElasticSearch server from the esctl configuration file")
def remove_context(
    ctx: typer.Context,
    context_name: Annotated[str, typer.Argument(autocompletion=complete_context)],
):
    ctx.obj["config"].remove_context(context_name)
    typer.echo(f"Context {context_name} removed")


@app.command(help="Open the esctl configuration file in the default editor")
def edit(ctx: typer.Context):
    common_editors = ["nvim", "vim", "emacs", "vi", "nano"]
    default = None
    for editor in common_editors:
        if shutil.which(editor):
            default = editor
            break
    editor = os.getenv("EDITOR", default)
    subprocess.run([editor, str(ctx.obj["config"].config_path)])


# TODO: find a way to add aliases to commands without having to edit the config file
# @app.command(help="Adds an alias with arguments to another esctl command")
# def add_alias(
#     ctx: typer.Context,
#     alias_name: Annotated[str, typer.Argument(help="Name of the alias")],
#     command: Annotated[str, typer.Argument(help="Command to alias, e.g. cat.indices")],
# ):
#     config: Config = ctx.obj["config"]
#     print(f"Adding an alias for [b blue]{command}[/]")
#     arguments = {}
#     command_callback = getattr(
#         importlib.import_module(f".{command}", package="esctl.commands"),
#         command.split(".")[-1],
#     )
#     info = None
#     for part in command.split("."):
#         print("type(info) ------- ", type(info))
#         attr_name = "registered_groups" if info is None or hasattr(info, "typer_instance") else "registered_commands"
#         typer_instance = app.root
#         if info is not None:
#             typer_instance = info.typer_instance
#         print("vars(ti)   ---- ", vars(typer_instance))
#         print("attr name: ", attr_name)
#         print("groups? ", [c.name for c in typer_instance.registered_groups])
#         info = next(grp for grp in getattr(typer_instance, attr_name, []) if grp.name == part)

#     print(info)

#     # while Confirm.ask("Do you want to add an argument to the alias?"):
#     #     argument_name = Prompt.ask("Argument name")
#     #     argument_value = Prompt.ask("Argument value")
#     #     arguments[argument_name] = argument
#     # config.add_alias(alias_name, command, arguments)
#     # typer.echo(f"Alias {alias_name} added")
