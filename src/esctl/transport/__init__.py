from elasticsearch7 import Elasticsearch as Elasticsearch7
from elasticsearch8 import Elasticsearch as Elasticsearch8
from elasticsearch9 import Elasticsearch as Elasticsearch9
from elastic_transport import NodeConfig, Transport

from .transport import KubeNodeClassFactory, HTTPNodeClassFactory
from .serializers import SERIALIZERS7, SERIALIZERS8, SERIALIZERS9
from .cache import Cache


Elasticsearch = Elasticsearch7 | Elasticsearch8 | Elasticsearch9


def KubeClientFactory(
    context_name: str,
    cache_enabled: bool,
    kube_context: str,
    kube_namespace: str,
    es_name: str,
) -> Elasticsearch:
    Node = KubeNodeClassFactory(
        context_name=context_name,
        cache_enabled=cache_enabled,
        kube_context=kube_context,
        kube_namespace=kube_namespace,
        es_name=es_name,
    )
    transport = Transport(
        node_configs=[NodeConfig("http", "localhost", 9200)], node_class=Node
    )
    response = transport.perform_request("GET", "/")
    # Already JSON decoded
    version = response.body["version"]["number"]
    major = next(int(part) for part in version.split("."))
    match major:
        case 7:
            return Elasticsearch7(
                "http://127.0.0.1:9200",
                node_class=Node,
                serializers=SERIALIZERS7,
            )
        case 8:
            return Elasticsearch8(
                "http://127.0.0.1:9200",
                node_class=Node,
                serializers=SERIALIZERS8,
            )
        case 9:
            return Elasticsearch9(
                "http://127.0.0.1:9200",
                node_class=Node,
                serializers=SERIALIZERS9,
            )
        case _:
            raise ValueError(f"Unsupported Elasticsearch major version: {major}")


def HTTPClientFactory(
    context_name: str,
    cache_enabled: bool,
    host: str,
    username: str | None,
    password: str | None,
) -> Elasticsearch:
    Node = HTTPNodeClassFactory(
        context_name=context_name,
        cache_enabled=cache_enabled,
        username=username,
        password=password,
    )
    transport = Transport(
        node_configs=[NodeConfig("http", "localhost", 9200)], node_class=Node
    )
    response = transport.perform_request("GET", "/")
    # Already JSON decoded
    version = response.body["version"]["number"]
    major = next(int(part) for part in version.split("."))
    match major:
        case 7:
            return Elasticsearch7(
                host,
                node_class=Node,
                serializers=SERIALIZERS7,
            )
        case 8:
            return Elasticsearch8(
                host,
                node_class=Node,
                serializers=SERIALIZERS8,
            )
        case 9:
            return Elasticsearch9(
                host,
                node_class=Node,
                serializers=SERIALIZERS9,
            )
        case _:
            raise ValueError(f"Unsupported Elasticsearch major version: {major}")


__all__ = (
    "Elasticsearch",
    "Cache",
    "KubeClientFactory",
    "HTTPClientFactory",
    "KubeNodeClassFactory",
    "HTTPNodeClassFactory",
)
