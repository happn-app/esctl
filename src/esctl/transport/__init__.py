from urllib.parse import urlparse

from elasticsearch8 import Elasticsearch as Elasticsearch8
from elasticsearch9 import Elasticsearch as Elasticsearch9
from elastic_transport import NodeConfig, Transport

from .transport import KubeNodeClassFactory, HTTPNodeClassFactory
from .serializers import SERIALIZERS8, SERIALIZERS9
from .cache import Cache


Elasticsearch = Elasticsearch8 | Elasticsearch9


def _detect_major_version(node_class: type, scheme: str, host: str, port: int) -> int:
    """Probe ``GET /`` on the target and return the ES major version.

    The probe uses the *actual* target host/port so version detection works
    against any endpoint (not just localhost:9200).
    """
    transport = Transport(
        node_configs=[NodeConfig(scheme, host, port)], node_class=node_class
    )
    response = transport.perform_request("GET", "/")
    # Already JSON decoded
    version = response.body["version"]["number"]
    return next(int(part) for part in version.split("."))


def KubeClientFactory(
    context_name: str,
    cache_enabled: bool,
    kube_context: str,
    kube_namespace: str,
    es_name: str,
    in_cluster: bool = False,
) -> Elasticsearch:
    Node = KubeNodeClassFactory(
        context_name=context_name,
        cache_enabled=cache_enabled,
        kube_context=kube_context,
        kube_namespace=kube_namespace,
        es_name=es_name,
        in_cluster=in_cluster,
    )
    # The port-forward binds ES on localhost:9200, so probe there.
    major = _detect_major_version(Node, "http", "localhost", 9200)
    match major:
        case 7:
            return Elasticsearch9(
                "http://127.0.0.1:9200",
                node_class=Node,
                serializers=SERIALIZERS9,
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
    # Probe the real endpoint, not a hardcoded localhost:9200.
    parsed = urlparse(host)
    scheme = parsed.scheme or "http"
    probe_host = parsed.hostname or "localhost"
    probe_port = parsed.port or (443 if scheme == "https" else 9200)
    major = _detect_major_version(Node, scheme, probe_host, probe_port)
    match major:
        case 7:
            return Elasticsearch8(
                host,
                node_class=Node,
                serializers=SERIALIZERS8,
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
