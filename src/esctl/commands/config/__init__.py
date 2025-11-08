from enum import Enum
from typing import Annotated

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import typer
import typer.completion

from esctl.config import Config

from .add_context import app as add_context_app
from .cache import app as cache_app


class Shell(str, Enum):
    bash = "bash"
    zsh = "zsh"
    fish = "fish"
    powershell = "powershell"


def complete_context(ctx: typer.Context, incomplete: str):
    cfg = Config.from_context(ctx)
    return [
        context for context in cfg.contexts.keys() if context.startswith(incomplete)
    ]


app = typer.Typer(rich_markup_mode="rich")
app.add_typer(
    add_context_app,
    name="add-context",
    help="Add an ElasticSearch server to the esctl configuration file",
)
app.add_typer(
    cache_app,
    name="cache",
    help="Manage the local cache for the current context",
)


@app.command(
    name="contexts",
    help="Lists all available ES Contexts saved in the esctl configuration file",
)
def list_contexts(
    ctx: typer.Context,
    with_password: Annotated[
        bool,
        typer.Option(
            "--with-password",
            help="Show the password in the output",
        ),
    ] = False,
):
    config = Config.from_context(ctx)
    console = Console()
    http_contexts = {
        name: context
        for name, context in config.contexts.items()
        if context.type == "http"
    }
    if http_contexts:
        table = Table(
            "", "Name", "URL", "Username", "Password", title="Available Contexts"
        )
        for context_name, context in http_contexts.items():
            table.add_row(
                "" if context_name != config.current_context else "→",
                (
                    context_name
                    if context_name != config.current_context
                    else f"[b green]{context_name}[/]"
                ),
                context.url,
                context.username,
                context.password if with_password else context.censored_password,
            )
        console.print(table)
    kube_contexts = {
        name: context
        for name, context in config.contexts.items()
        if context.type == "kubernetes"
    }
    if kube_contexts:
        table = Table(
            "",
            "Name",
            "Kube Context",
            "Kube Namespace",
            "ES Name",
            title="Available Kube Contexts",
        )
        for context_name, context in kube_contexts.items():
            table.add_row(
                "" if context_name != config.current_context else "→",
                (
                    context_name
                    if context_name != config.current_context
                    else f"[b green]{context_name}[/]"
                ),
                context.kube_context or "default",
                context.kube_namespace or "default",
                context.es_name,
            )
        console.print(table)


@app.command(help="Remove an ElasticSearch server from the esctl configuration file")
def remove_context(
    ctx: typer.Context,
    context_name: Annotated[
        str,
        typer.Argument(
            help="Name of the context to remove",
            autocompletion=complete_context,
        ),
    ],
):
    Config.from_context(ctx).remove_context(context_name)
    typer.echo(f"Context {context_name} removed")


@app.command(help="Open the esctl configuration file in the default editor")
def edit():
    Config.edit()


# TODO: find a way to add aliases to commands without having to edit the config file
# @app.command(help="Adds an alias with arguments to another esctl command")
# def add_alias(
#     ctx: typer.Context,
#     alias_name: Annotated[str, typer.Argument(help="Name of the alias")],
#     command: Annotated[str, typer.Argument(help="Command to alias, e.g. cat.indices")],
# ):
#     config = Config.from_context(ctx)
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


@app.command(help="Show completion for a specific shell")
def completion(
    ctx: typer.Context,
    shell: Annotated[
        Shell,
        typer.Argument(
            help="Shell type",
        ),
    ],
):
    # Typer internal callback to show the completion script
    # This is not documented but works, the second parameter is not used but is
    # typed as a click.Parameter, instead of instanciating one, we pass None
    # It breaks the typing but works perfectly fine in this instance, hence the 'type: ignore'
    typer.completion.show_callback(ctx, None, shell)  # type: ignore


@app.command(help="Setup command to guid users through setting up esctl")
def setup(ctx: typer.Context):
    print(
        "This setup wizard will guide you through setting up esctl after installations or updates."
    )
    config = Config.from_context(ctx)
    if config.github_auth_command is None:
        github_auth_command = Prompt.ask(
            "To enable issue reporting, you need a command to authenticate with GitHub. What command do you want to use?",
            default="gh auth login",
            choices=[
                "gh auth login",
                "echo $GITHUB_TOKEN",
                "other",
            ],
        )
        if github_auth_command == "other":
            github_auth_command = Prompt.ask(
                "What command do you want to use to authenticate with GitHub?",
            )
        config.github_auth_command = github_auth_command
    if len(config.contexts) == 0:
        print(
            "To function, esctl needs at least one context to connect to an Elasticsearch cluster."
        )
        context_type = Prompt.ask(
            "What type of context do you want to add?",
            choices=list(config.context_types),
            default="http",
        )
        match context_type:
            case "http":
                config.add_context(
                    Prompt.ask("Context name", default="default"),
                    "http",
                    host=Prompt.ask("Elasticsearch host", default="localhost"),
                    port=int(Prompt.ask("Elasticsearch port", default="9200")),
                    username=Prompt.ask("Username", default=""),
                    password=Prompt.ask("Password", default="", password=True),
                )
            case "kubernetes":
                config.add_context(
                    Prompt.ask("Context name", default="default"),
                    "kubernetes",
                    kube_context=Prompt.ask("Kube context", default=""),
                    kube_namespace=Prompt.ask("Kube namespace", default="default"),
                    es_name=Prompt.ask(
                        "Elasticsearch service name", default="elasticsearch"
                    ),
                )
            case "gce":
                config.add_context(
                    Prompt.ask("Context name", default="default"),
                    "gce",
                    project_id=Prompt.ask("GCP Project ID"),
                    zone=Prompt.ask("GCP Zone", default="us-central1-a"),
                    instance_name=Prompt.ask("GCE Instance Name"),
                )
    print("Setup complete! You can now use esctl.")
