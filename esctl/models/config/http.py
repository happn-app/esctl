from typing import Literal

from elastic_transport import NodeConfig, Urllib3HttpNode
from elasticsearch import Elasticsearch
from elasticsearch.serializer import JsonSerializer, NdjsonSerializer, TextSerializer
import urllib3
from urllib3.connection import HTTPConnection as Urllib3HTTPConnection

from esctl.models.config.base import ESConfig
from esctl.serializer import YamlSerializer


class HTTPConnection(Urllib3HTTPConnection):
    def getresponse(self) -> urllib3.HTTPResponse:
        response = super().getresponse()
        # Hack around the fact that ES raises an exception if the
        # X-Elastic-Product header is not set, claiming an "unsupported product"
        # 100% is to not have AWS' version of ES be compatible with the client
        # library. Incidentally, this also breaks if trying to query a server
        # with version 7.10.0 or lower.
        response.headers["X-Elastic-Product"] = "Elasticsearch"
        return response


class HTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):
    ConnectionCls = HTTPConnection


class HTTPNode(Urllib3HttpNode):
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        kw = self.pool.conn_kw
        self.pool = HTTPConnectionPool(
            config.host,
            port=config.port,
            timeout=urllib3.Timeout(total=config.request_timeout),
            maxsize=config.connections_per_node,
            block=True,
            **kw,
        )


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
            node_class=HTTPNode,
            serializers={
                JsonSerializer.mimetype: JsonSerializer(),
                TextSerializer.mimetype: TextSerializer(),
                NdjsonSerializer.mimetype: NdjsonSerializer(),
                "application/yaml": YamlSerializer(),
                "application/yml": YamlSerializer(),
            },
        )
