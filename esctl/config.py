import errno
import os
from pathlib import Path
import sys
from typing import Annotated, Any

from elasticsearch import Elasticsearch
from pydantic import BaseModel, Field
from rich import print
import typer

from esctl.models.config.http import HTTPESConfig
from esctl.models.config.kube import KubeESConfig
from esctl.models.config.gce import GCEESConfig
from esctl.utils import get_root_ctx


class Config(BaseModel):
    config_path: Path
    contexts: dict[
        str, Annotated[HTTPESConfig | KubeESConfig | GCEESConfig, Field(discriminator="type")]
    ]
    current_context: str
    aliases: dict[str, Any] = {}

    def __setattr__(self, name: str, value: Any):
        super().__setattr__(name, value)
        save_config(self)

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


def get_esctl_config_path() -> Path:
    return get_esctl_home() / "config.json"


def get_esctl_home() -> Path:
    if os.getenv("ESCONFIG"):
        return Path(os.environ["ESCONFIG"])
    HOME = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    CONFIG_DIR = HOME / "esctl"
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(exist_ok=True, parents=True)
    return CONFIG_DIR


def read_config() -> Config:
    config_path = get_esctl_config_path()
    if config_path.exists():
        return Config.model_validate_json(config_path.read_text())
    return Config(config_path=config_path, contexts={}, current_context="")


def save_config(config: Config):
    config_path = get_esctl_config_path()
    config_path.write_text(config.model_dump_json(indent=2))


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
    return es_config.client
