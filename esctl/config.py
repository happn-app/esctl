import errno
import functools
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Annotated, Any

from elasticsearch import Elasticsearch
from pydantic import BaseModel, Field, ValidationError, model_validator
from rich import print
from rich.prompt import Confirm
import typer

from esctl.constants import get_esctl_config_path
from esctl.models.config.http import HTTPESConfig
from esctl.models.config.kube import KubeESConfig
from esctl.models.config.gce import GCEESConfig
from esctl.utils import get_root_ctx


class Config(BaseModel):
    config_path: Path = Field(exclude=True)
    contexts: dict[
        str,
        Annotated[
            HTTPESConfig | KubeESConfig | GCEESConfig, Field(discriminator="type")
        ],
    ]
    current_context: str
    aliases: dict[str, Any] = {}
    github_auth_command: str | None = None
    context_types: tuple[str, ...] = Field(
        exclude=True, default=("http", "kubernetes", "gce")
    )

    def __setattr__(self, name: str, value: Any):
        super().__setattr__(name, value)
        save_config(self)

    @property
    def github_auth(self) -> str | None:
        if self.github_auth_command:
            try:
                return (
                    subprocess.check_output(shlex.split(self.github_auth_command))
                    .decode("utf-8")
                    .strip()
                )
            except subprocess.CalledProcessError as e:
                print(f"[red bold]ERROR:[/] Failed to get GitHub auth token: {e}")
                return None
        return None

    @model_validator(mode="before")
    @classmethod
    def _inject_context_names(cls, v: Any):
        if isinstance(v, dict) and isinstance(v.get("contexts"), dict):
            new_contexts: dict[str, Any] = {}
            for k, ctx in v["contexts"].items():
                # If the serialized ctx is a dict, add name unless already present
                if isinstance(ctx, dict) and "name" not in ctx:
                    ctx = {**ctx, "name": k}
                new_contexts[k] = ctx
            v = {**v, "contexts": new_contexts}
        return v

    def add_context(
        self,
        context_name: str,
        context_type: str,
        /,
        **kwargs,
    ):
        if context_name in self.contexts:
            raise ValueError(f"Context {context_name} already exists")
        if context_type == "http":
            self.contexts[context_name] = HTTPESConfig(type="http", **kwargs)
        elif context_type == "kubernetes":
            self.contexts[context_name] = KubeESConfig(type="kubernetes", **kwargs)
        elif context_type == "gce":
            self.contexts[context_name] = GCEESConfig(type="gce", **kwargs)
        save_config(self)

    def remove_context(self, context_name: str):
        self.contexts.pop(context_name)
        save_config(self)

    def add_alias(self, alias_name: str, command: str, args: dict[str, Any]):
        self.aliases[alias_name] = {"command": command, "args": args, "help": command}
        save_config(self)


@functools.lru_cache()
def read_config() -> Config:
    config_path = get_esctl_config_path()
    if config_path.exists():
        try:
            return Config.model_validate_json(config_path.read_text())
        except ValidationError as exception:
            print("[red bold]ERROR:[/] Failed to read config file")
            for error in exception.errors():
                print(
                    f"  -  {error['msg']}: [b]{'.'.join(str(loc) for loc in error['loc'])}[/]"
                )
            if Confirm.ask(
                "Do you want to edit it to fix the issue?",
                case_sensitive=False,
                default=True,
            ):
                edit_config()
                return read_config()
            sys.exit(errno.ENOEXEC)
        except Exception as exception:
            print(f"[red bold]ERROR:[/] Failed to read config file: {exception}")
            if Confirm.ask(
                "Do you want to edit it to fix the issue?",
                case_sensitive=False,
                default=True,
            ):
                edit_config()
                return read_config()
            sys.exit(errno.ENOEXEC)
    return Config(config_path=config_path, contexts={}, current_context="")


def save_config(config: Config):
    config_path = get_esctl_config_path()
    config_path.write_text(config.model_dump_json(indent=2))


def edit_config(lineno: int | None = None):
    common_editors = ["nvim", "vim", "emacs", "vi", "nano"]
    default = None
    for editor in common_editors:
        if shutil.which(editor):
            default = editor
            break
    if default is None:
        default = "vi"
    editor = os.getenv("EDITOR", default)
    arguments = [editor, str(get_esctl_config_path())]
    if editor in ["nvim", "vim", "vi"] and lineno is not None:
        arguments.insert(1, f"+{lineno}")
    subprocess.run(arguments)


def get_current_context_from_ctx(ctx: typer.Context) -> str:
    root_ctx = get_root_ctx(ctx)
    context_name = root_ctx.params["context"]
    conf = read_config()
    if context_name is None:
        context_name = conf.current_context
    if context_name not in conf.contexts:
        print(f"[red bold]ERROR:[/] Context not found: {context_name}", file=sys.stderr)
        sys.exit(errno.ENOEXEC)
    return context_name


def get_client_from_ctx(ctx: typer.Context) -> Elasticsearch:
    conf = read_config()
    context_name = get_current_context_from_ctx(ctx)
    es_config = conf.contexts[context_name]
    if isinstance(es_config, GCEESConfig) or es_config.type == "gce":
        es_config.start_ssh_tunnel()
    es_config.cache_enabled = bool(ctx.obj.get("cache_enabled", False))
    return es_config.client
