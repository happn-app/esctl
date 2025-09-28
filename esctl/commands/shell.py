import io
import os
from textwrap import dedent
from IPython import start_ipython  # type: ignore
from IPython.terminal.prompts import Prompts, Token  # type: ignore
from rich.console import Console
from traitlets.config import Config
import typer
from ruamel.yaml import YAML
from pathlib import Path
import json

from esctl.cache import Cache
from esctl.config import get_current_context_from_ctx, read_config
from esctl.constants import get_esctl_home


app = typer.Typer(rich_markup_mode="rich")


class EsctlPrompts(Prompts):
    def __init__(self, shell, context_name: str):
        super().__init__(shell)
        self._ctx = context_name

    # Input prompt: e.g. "[prod] In [7]: "
    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Prompt, f"[{self._ctx}] In ["),
            (Token.PromptNum, str(self.shell.execution_count)),
            (Token.Prompt, "]: "),
        ]

    # Continuation prompt for multi-line inputs
    def continuation_prompt_tokens(self, width=None, *, lineno=None, wrap_count=None):
        return [
            (Token.Prompt, f"[{self._ctx}] In ["),
            (Token.PromptNum, str(self.shell.execution_count)),
            (Token.Prompt, "]> "),
        ]

    # Output prompt: e.g. "[prod] Out[7]: "
    def out_prompt_tokens(self):
        return [
            (Token.OutPrompt, f"[{self._ctx}] Out["),
            (Token.OutPromptNum, str(self.shell.execution_count)),
            (Token.OutPrompt, "]: "),
        ]


def rich_to_ansi(markup: str) -> str:
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, color_system="truecolor")
    console.print(markup, end="")
    return buf.getvalue()


@app.callback(
    help="Start a shell to interact with your cluster.",
    invoke_without_command=True,
)
def shell(
    ctx: typer.Context,
):
    conf = read_config()
    context_name = get_current_context_from_ctx(ctx)
    if conf.contexts[context_name].type == "gce":
        conf.contexts[context_name].start_ssh_tunnel()  # type: ignore
    client = conf.contexts[context_name].client
    ipython_dir = get_esctl_home() / "ipython" / context_name
    if not ipython_dir.exists():
        ipython_dir.mkdir(parents=True, exist_ok=True)
    working_directory = ipython_dir / "working_dir"
    if not working_directory.exists():
        working_directory.mkdir(parents=True, exist_ok=True)
    yaml = YAML(typ="rt")
    yaml.indent(mapping=2, sequence=4, offset=2)
    context = {
        "client": client,
        "yaml": yaml,
        "json": json,
        "config": conf,
        "cache": Cache(context_name),
        "Path": Path,
        "cwd": working_directory,
    }
    es_version = client.info().get("version", {}).get("number", "unknown")
    editor = os.getenv("EDITOR", "vi")
    # Configure banner + prompts
    c = Config()

    # pass the context name to the prompt class via a tiny wrapper factory
    # IPython expects a class, so we set a lambda that closes over context_name
    # using a subclass factory pattern:
    class _Factory(EsctlPrompts):
        def __init__(self, shell):
            super().__init__(shell, context_name)

    c.TerminalInteractiveShell.prompts_class = _Factory
    banner = dedent(
        f"""
    esctl interactive shell for context: [bold blue]{context_name}[/] (ES [bold green]{es_version}[/])
    Available: {', '.join(context.keys())}
    [b]F2[/] to edit cell in [yellow]{editor}[/]
    """.strip(
            "\n"
        )
    )
    c.TerminalInteractiveShell.banner1 = rich_to_ansi(banner)
    c.TerminalInteractiveShell.term_title = True
    c.TerminalInteractiveShell.confirm_exit = False
    c.TerminalInteractiveShell.enable_history_search = True
    c.TerminalInteractiveShell.term_title_format = f"esctl [{context_name}]"

    start_ipython(
        argv=[
            "--banner",
            "--no-tip",
            f"--ipython-dir={str(ipython_dir)}",
        ],
        user_ns=context,
        config=c,
    )
