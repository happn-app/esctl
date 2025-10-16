import errno
import sys
from typing import Annotated
import typer
from ruamel.yaml import YAML
from rich import print
from pathlib import Path
import json

from esctl.transport import Cache
from esctl.config import Config


app = typer.Typer(rich_markup_mode="rich")


@app.callback(
    help="Execute a python script to interact with your cluster.",
    invoke_without_command=True,
)
def execute(
    ctx: typer.Context,
    script: Annotated[
        str,
        typer.Argument(
            help="Path to the python script to execute",
        ),
    ] = "-",
):
    conf = Config.load()
    context_name = conf.get_current_context_name(ctx)
    if conf.contexts[context_name].type == "gce":
        conf.contexts[context_name].start_ssh_tunnel()  # type: ignore
    client = conf.contexts[context_name].client
    yaml = YAML(typ="rt")
    yaml.indent(mapping=2, sequence=4, offset=2)
    context = {
        "client": client,
        "yaml": yaml,
        "json": json,
        "config": conf,
        "cache": Cache(context_name),
    }
    source = ""
    if script == "-":
        source = sys.stdin.read()
        if source.strip() == "":
            print("No script provided", file=sys.stderr)
            raise typer.Exit(errno.EINVAL)  # EINVAL: Invalid argument
        if not isinstance(source, str):
            print(f"Invalid script type: {type(source)}", file=sys.stderr)
            raise typer.Exit(errno.EINVAL)  # EINVAL: Invalid argument
    else:
        script_path = Path(script).expanduser().resolve()
        if not script_path.exists():
            print(f"Script not found: {script_path}", file=sys.stderr)
            raise typer.Exit(errno.ENOENT)  # ENOENT: No such file or directory
        if not script_path.is_file():
            print(f"Script is not a file: {script_path}", file=sys.stderr)
            raise typer.Exit(errno.EINVAL)  # EINVAL: Invalid argument
        try:
            source = script_path.read_text()
        except Exception as e:
            print(f"Failed to read script: {e}", file=sys.stderr)
            raise typer.Exit(errno.EIO)  # EIO: I/O error
    try:
        exec(source, globals=context, locals=context)
    except Exception as e:
        print(f"Error executing script: {e}", file=sys.stderr)
        raise typer.Exit(1)
