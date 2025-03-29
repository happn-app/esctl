from elasticsearch import Elasticsearch
from pydantic import BaseModel


class ESConfig(BaseModel):
    @property
    def client(self) -> Elasticsearch:
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def basic_auth(self) -> tuple[str, str] | None:
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def censored_password(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def from_context_name(cls, context_name: str) -> "ESConfig":
        from esctl.config import read_config
        conf = read_config()
        return conf.contexts[context_name]
