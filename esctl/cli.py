import importlib
import logging
from typing import Annotated

import typer
from jmespath import compile as compile_jmespath
from jsonpath_ng import parse as parse_jsonpath
from rich.logging import RichHandler
from rich import print
from yamlpath import YAMLPath

from esctl.params import ContextOption, JMESPathOption, JSONPathOption, PrettyOption, VerboseOption, YAMLPathOption

from .commands.cat import app as cat_app
from .commands.cluster import app as cluster_app
from .commands.config import app as config_app
from .commands.tasks import app as task_app
from .commands.index import app as index_app
from .commands.reindex import app as reindex_app
from .commands.troubleshoot import app as troubleshoot_app
from .config import read_config

app = typer.Typer(rich_markup_mode="rich")
setattr(cat_app, "root", app)
setattr(cluster_app, "root", app)
setattr(config_app, "root", app)
setattr(task_app, "root", app)
setattr(index_app, "root", app)

app.add_typer(
    cat_app,
    name="cat",
    help="Compact and aligned text (CAT) APIs for Elasticsearch",
)
app.add_typer(cluster_app, name="cluster", help="Elasticsearch Cluster management APIs")
app.add_typer(config_app, name="config", help="Manage esctl configuration")
app.add_typer(task_app, name="task", help="Elasticsearch Task management APIs")
app.add_typer(index_app, name="index", help="Elasticsearch Index management APIs")
app.add_typer(reindex_app, name="reindex", help="Reindex from one index to another")
app.add_typer(troubleshoot_app, name="troubleshoot", help="Troubleshoot Elasticsearch cluster issues")

cfg = read_config()


def alias_factory(command: str, args: list[str]):
    def callback(ctx: typer.Context):
        module = importlib.import_module(f".{command}", package="esctl.commands")
        cmd_name = command.split(".")[-1]
        cmd = getattr(module, cmd_name)
        ctx.invoke(cmd, ctx, **args)  # type: ignore

    return callback


for alias_name, alias in cfg.aliases.items():
    app.command(alias_name, help=alias["help"], short_help=alias["help"])(
        alias_factory(alias["command"], alias["args"])
    )


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    context: ContextOption | None = None,
    verbose: VerboseOption = 0,
    jsonpath: JSONPathOption | None = None,
    jmespath: JMESPathOption | None = None,
    yamlpath: YAMLPathOption | None = None,
    pretty: PrettyOption = True,
    version: Annotated[bool, typer.Option("--version", is_flag=True)] = False,
):
    if version:
        from esctl import __version__ as esctl_version
        from elasticsearch._version import __versionstr__ as es_version
        from kubernetes import __version__ as k8s_version
        import sys

        print(f"esctl version         : [blue]{esctl_version}[/]")
        print(f"Elasticsearch version : [blue]{es_version}[/]")
        print(f"Kubernetes version    : [blue]{k8s_version}[/]")
        print(f"Python version        : [blue]{sys.version}[/]")
        raise typer.Exit()
    # Make jsonpath, jmespath and yamlpath mutually exclusive
    if len([arg for arg in (jsonpath, jmespath, yamlpath) if arg]) > 1:
        raise typer.BadParameter(
            "--jsonpath, --jmespath and --yamlpath are mutually exclusive"
        )
    level = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
        4: logging.NOTSET,
    }[verbose]
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(markup=True, rich_tracebacks=True)],
    )
    logger = logging.getLogger("esctl")

    if context is not None:
        cfg.current_context = context

    conf = cfg.contexts.get(cfg.current_context)

    ctx.obj = {
        "config": cfg,
        "context": conf,
        "verbosity": verbose,
        "logger": logger,
        "jsonpath": jsonpath,
        "jmespath": jmespath,
        "yamlpath": yamlpath,
        "pretty": pretty,
    }
    ctx.obj["jsonpath"] = parse_jsonpath(jsonpath) if jsonpath else None
    ctx.obj["jmespath"] = compile_jmespath(jmespath) if jmespath else None
    ctx.obj["yamlpath"] = YAMLPath(yamlpath) if yamlpath else None


if __name__ == "__main__":
    app()
