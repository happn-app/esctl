import importlib
import logging
from typing import Annotated, Any, Callable

import elasticsearch8
import elasticsearch9
import typer
from rich.logging import RichHandler
from rich import print


from esctl.commands.cat import app as cat_app
from esctl.commands.cluster import app as cluster_app
from esctl.commands.config import app as config_app
from esctl.commands.tasks import app as task_app
from esctl.commands.index import app as index_app
from esctl.commands.reindex import app as reindex_app
from esctl.commands.troubleshoot import app as troubleshoot_app
from esctl.commands.snapshot import app as snapshot_app
from esctl.commands.shell import app as shell_app
from esctl.commands._exec import app as exec_app
from esctl.options.output import OutputOption
from esctl.config import Config, ESConfigType
from esctl.utils import try_create_github_issue


class CustomTyper(typer.Typer):
    def __call__(self, *args, **kwargs):
        token = cfg.github_auth
        try:
            super(CustomTyper, self).__call__(*args, **kwargs)
        except (KeyboardInterrupt, typer.Exit):
            raise
        except tuple(
            getattr(elasticsearch8.exceptions, s)
            for s in elasticsearch8.exceptions.__all__
        ) as e:
            try_create_github_issue(
                e, token, ".".join(str(part) for part in elasticsearch8.__version__)
            )
            raise
        except tuple(
            getattr(elasticsearch9.exceptions, s)
            for s in elasticsearch9.exceptions.__all__
        ) as e:
            try_create_github_issue(
                e, token, ".".join(str(part) for part in elasticsearch9.__version__)
            )
            raise
        except Exception as e:
            try_create_github_issue(e, token, "unknown")
            raise


app = CustomTyper(rich_markup_mode="rich")
setattr(cat_app, "root", app)
setattr(cluster_app, "root", app)
setattr(config_app, "root", app)
setattr(task_app, "root", app)
setattr(index_app, "root", app)
setattr(reindex_app, "root", app)
setattr(troubleshoot_app, "root", app)
setattr(snapshot_app, "root", app)
setattr(shell_app, "root", app)
setattr(exec_app, "root", app)

app.add_typer(
    cat_app,
    name="cat",
    help="Compact and aligned text (CAT) APIs for Elasticsearch",
)
app.add_typer(
    cluster_app,
    name="cluster",
    help="Elasticsearch Cluster management APIs",
)
app.add_typer(
    config_app,
    name="config",
    help="Manage esctl configuration",
)
app.add_typer(
    task_app,
    name="task",
    help="Elasticsearch Task management APIs",
)
app.add_typer(
    index_app,
    name="index",
    help="Elasticsearch Index management APIs",
)
app.add_typer(
    reindex_app,
    name="reindex",
    help="Reindex from one index to another",
)
app.add_typer(
    troubleshoot_app,
    name="troubleshoot",
    help="Troubleshoot Elasticsearch cluster issues",
)
app.add_typer(
    snapshot_app,
    name="snapshot",
    help="Elasticsearch Snapshot and Restore APIs",
)
app.add_typer(
    shell_app,
    name="shell",
    help="Start an interactive shell to interact with your cluster",
)
app.add_typer(
    exec_app,
    name="exec",
    help="Execute a python script to interact with your cluster",
)

cfg = Config.load()


def alias_factory(command: str, args: Any):
    def callback(ctx: typer.Context):
        module = importlib.import_module(f".{command}", package="esctl.commands")
        cmd_name = command.split(".")[-1]
        cmd: Callable = getattr(module, cmd_name)
        ctx.invoke(cmd, ctx, **args)

    return callback


for alias_name, alias in cfg.aliases.items():
    app.command(alias_name, help=alias["help"], short_help=alias["help"])(
        alias_factory(alias["command"], alias["args"])
    )


def exit_handler(conf: ESConfigType | None):
    if conf is None:
        return
    if conf.type == "gce":
        conf.stop_ssh_tunnel()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    context: Annotated[
        str | None,
        typer.Option(
            "--context",
            "-c",
            autocompletion=lambda incomplete: (
                context for context in cfg.contexts if incomplete in context
            ),
            help="Elasticsearch cluster to use",
            envvar="ESCTL_CONTEXT",
        ),
    ] = None,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            min=0,
            max=4,
            help="Increase verbosity level",
        ),
    ] = 0,
    output: OutputOption = "table",
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty/--no-pretty",
            help="Pretty print the output",
        ),
    ] = True,
    cache: Annotated[
        bool,
        typer.Option(
            "--cache/--no-cache",
            help="Enable or disable HTTP response caching. Caching is enabled by default.",
        ),
    ] = True,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            is_flag=True,
            help="Prints version information and exit.",
        ),
    ] = False,
):
    if context is not None:
        cfg.current_context = context

    if cfg.current_context not in cfg.contexts:
        print(
            f"[red]Error:[/] Context [b]{cfg.current_context}[/] not found in configuration."
        )
        raise typer.Exit(code=1)
    conf: ESConfigType = cfg.contexts[cfg.current_context]
    if version:
        from esctl import __version__ as esctl_version
        from kubernetes import __version__ as k8s_version
        import sys

        info = conf.client.info()
        if isinstance(info, dict):
            es_version = info.get("version", {}).get("number", "unknown")
        else:
            es_version = info.body.get("version", {}).get("number", "unknown")

        print(f"esctl version         : [blue]{esctl_version}[/]")
        print(f"Current Context       : [blue]{conf.name}[/]")
        print(f"Elasticsearch version : [blue]{es_version}[/]")
        print(f"Kubernetes version    : [blue]{k8s_version}[/]")
        print(f"Python version        : [blue]{sys.version}[/]")
        print("License                : [blue]Apache-2.0[/]")
        raise typer.Exit()
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
    ctx.obj = {
        "config": cfg,
        "cache_enabled": bool(cache),
        "context": conf,
        "verbosity": verbose,
        "logger": logger,
        "output": output,
        "pretty": bool(pretty),
    }
    ctx.call_on_close(lambda: exit_handler(conf))


if __name__ == "__main__":
    try:
        app()
    # except (typer.Exit, typer.Abort, SystemExit, KeyboardInterrupt):
    #     raise
    except Exception as e:
        token = cfg.github_auth
        try_create_github_issue(e, token, "unknown")
        raise
