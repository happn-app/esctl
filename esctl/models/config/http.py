from typing import Literal
from elasticsearch import Elasticsearch
from elasticsearch.serializer import JsonSerializer, NdjsonSerializer, TextSerializer

from esctl.models.config.base import ESConfig
from esctl.serializer import YamlSerializer


class HTTPESConfig(ESConfig):
    type: Literal["http"] = "http"
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
