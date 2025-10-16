import errno
import functools
import os
import shlex
import shutil
import subprocess
import sys
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field, ValidationError, model_validator
from rich import print
from rich.prompt import Confirm
import typer

from esctl.constants import ESCTL_CONFIG_PATH
from esctl.config.models.http import HTTPESConfig
from esctl.config.models.kube import KubeESConfig
from esctl.config.models.gce import GCEESConfig
from esctl.transport import Elasticsearch

from .utils import get_root_ctx


class Config(BaseModel):
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
    cache_enabled: bool = Field(default=False, exclude=True)

    def __setattr__(self, name: str, value: Any):
        super().__setattr__(name, value)
        self.save()

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
        self.save

    def remove_context(self, context_name: str):
        self.contexts.pop(context_name)
        self.save()

    def add_alias(self, alias_name: str, command: str, args: dict[str, Any]):
        self.aliases[alias_name] = {"command": command, "args": args, "help": command}
        self.save()

    @functools.lru_cache()
    @staticmethod
    def load() -> "Config":
        if ESCTL_CONFIG_PATH.exists():
            try:
                return Config.model_validate_json(ESCTL_CONFIG_PATH.read_text())
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
                    Config.edit()
                    return Config.load()
                sys.exit(errno.ENOEXEC)
            except Exception as exception:
                print(f"[red bold]ERROR:[/] Failed to read config file: {exception}")
                if Confirm.ask(
                    "Do you want to edit it to fix the issue?",
                    case_sensitive=False,
                    default=True,
                ):
                    Config.edit()
                    return Config.load()
                sys.exit(errno.ENOEXEC)
        return Config(contexts={}, current_context="")

    def save(self: Self) -> None:
        ESCTL_CONFIG_PATH.write_text(self.model_dump_json(indent=2))

    @staticmethod
    def edit(lineno: int | None = None) -> None:
        common_editors = ["nvim", "vim", "emacs", "vi", "nano"]
        default = None
        for editor in common_editors:
            if shutil.which(editor):
                default = editor
                break
        if default is None:
            default = "vi"
        editor = os.getenv("EDITOR", default)
        arguments = [editor, str(ESCTL_CONFIG_PATH)]
        if editor in ["nvim", "vim", "vi"] and lineno is not None:
            arguments.insert(1, f"+{lineno}")
        subprocess.run(arguments)

    @functools.lru_cache()
    @staticmethod
    def from_context(ctx: typer.Context) -> "Config":
        root_ctx = get_root_ctx(ctx)
        if "config" not in root_ctx.obj:
            root_ctx.obj["config"] = Config.load()
        root_ctx.obj["config"].cache_enabled = bool(
            root_ctx.obj.get("cache_enabled", False)
        )
        return root_ctx.obj["config"]

    @property
    def client(self) -> Elasticsearch:
        es_config = self.contexts.get(self.current_context)
        if es_config is None:
            raise ValueError(f"Current context '{self.current_context}' not found")
        if es_config.type == "gce":
            es_config.start_ssh_tunnel()
        es_config.cache_enabled = bool(self.cache_enabled)
        return es_config.client

    def get_current_context_name(self, ctx: typer.Context | None = None) -> str:
        if ctx is not None:
            root_ctx = get_root_ctx(ctx)
            if "context" in root_ctx.obj:
                return root_ctx.obj["context"].name
        return self.current_context
