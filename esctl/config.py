import os
from pathlib import Path
from typing import Any

import typer
from elasticsearch import Elasticsearch
from elasticsearch.serializer import JsonSerializer, NdjsonSerializer, TextSerializer
from pydantic import BaseModel

from esctl.serializer import YamlSerializer
from esctl.utils import get_root_ctx


class ESConfig(BaseModel):
    host: str
    username: str | None = None
    password: str | None = None
    port: int = 9200

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def basic_auth(self) -> tuple[str, str] | None:
        if self.username is None or self.password is None:
            return None
        return (self.username, self.password)

    @property
    def censored_password(self) -> str:
        return self.password[:4] + "*" * (len(self.password) - 4)

    @property
    def client(self) -> Elasticsearch:
        return Elasticsearch(
            self.url,
            basic_auth=self.basic_auth,
            serializers={
                JsonSerializer.mimetype: JsonSerializer(),
                TextSerializer.mimetype: TextSerializer(),
                NdjsonSerializer.mimetype: NdjsonSerializer(),
                "application/yaml": YamlSerializer(),
                "application/yml": YamlSerializer(),
            },
        )

    @classmethod
    def from_context_name(cls, context_name: str) -> "ESConfig":
        conf = read_config()
        return conf.contexts[context_name]


class Config(BaseModel):
    config_path: Path
    contexts: dict[str, ESConfig]
    current_context: str
    aliases: dict[str, Any] = {}

    def __setattr__(self, name: str, value: Any):
        super().__setattr__(name, value)
        save_config(self)

    def add_context(
        self,
        context_name: str,
        host: str,
        port: int,
        username: str = None,
        password: str = None,
    ):
        self.contexts[context_name] = ESConfig(
            host=host,
            port=port,
            username=username,
            password=password,
        )
        save_config(self)

    def remove_context(self, context_name: str):
        self.contexts.pop(context_name)
        save_config(self)

    def add_alias(self, alias_name: str, command: str, args: dict[str, Any]):
        self.aliases[alias_name] = {"command": command, "args": args, "help": command}
        save_config(self)


def get_esctl_config_path() -> Path:
    if os.getenv("ESCONFIG"):
        return Path(os.getenv("ESCONFIG"))
    HOME = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    CONFIG_DIR = HOME / "esctl"
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(exist_ok=True, parents=True)
    return CONFIG_DIR / "config.json"


def read_config() -> Config:
    config_path = get_esctl_config_path()
    if config_path.exists():
        return Config.model_validate_json(config_path.read_text())
    return Config(config_path=config_path, contexts={}, current_context="")


def save_config(config: Config):
    config.config_path.write_text(config.model_dump_json(indent=2))


def get_client_from_ctx(ctx: typer.Context) -> Elasticsearch:
    root_ctx = get_root_ctx(ctx)
    context_name = root_ctx.params["context"]
    if context_name is None:
        context_name = read_config().current_context
    return ESConfig.from_context_name(context_name).client
