from base64 import b64decode, b64encode
import socket
import time
from typing import Type

from elastic_transport import HttpHeaders, NodeConfig, Urllib3HttpNode
from elastic_transport._node._base import NodeApiResponse
from elastic_transport.client_utils import DefaultType
from kubernetes import client as kube_client
from kubernetes import config as kube_config
from kubernetes.stream import portforward
from kubernetes.stream.ws_client import PortForward
import urllib3
from urllib3.connection import HTTPConnection as Urllib3HTTPConnection

from .cache import Cache


class CacheHttpNode(Urllib3HttpNode):
    def __init__(self, config: NodeConfig, context_name: str, cache_enabled: bool):
        super().__init__(config)
        self.cache = Cache(context_name, enabled=cache_enabled)

    def perform_request(
        self,
        method: str,
        target: str,
        body: bytes | None = None,
        headers: HttpHeaders | None = None,
        request_timeout: DefaultType | float | None = None,
    ) -> NodeApiResponse:
        if method.upper() not in ("GET", "HEAD"):
            # Only cache GET and HEAD requests, pass through others
            # Don't want to cache update requests, obviously
            return super().perform_request(
                method, target, body, headers, request_timeout
            )
        start_time = time.time()
        response = self.cache.get(method, target, headers)
        if response is not None:
            response.meta.duration = time.time() - start_time
            response.meta.node = self.config
            return response
        response = super().perform_request(
            method, target, body, headers, request_timeout
        )
        self.cache.set(
            method,
            target,
            response,
            headers=headers,
            ttl=Cache.get_ttl(f"{method.upper()} {target}"),
        )
        return response


class HTTPConnection(Urllib3HTTPConnection):
    def getresponse(self) -> urllib3.HTTPResponse:
        response = super().getresponse()
        # Hack around the fact that ES raises an exception if the
        # X-Elastic-Product header is not set, claiming an "unsupported product"
        # 100% is to not have AWS' version of ES be compatible with the client
        # library. Incidentally, this also breaks if trying to query a server
        # with version 7.10.0 or lower.
        if "X-Elastic-Product" not in response.headers:
            # Only add it if not already present
            # Otherwise, X-Elastic-Product will be "Elasticsearch,Elasticsearch"
            # The check in the ES Client library is for equality, not inclusion
            response.headers["X-Elastic-Product"] = "Elasticsearch"
        return response


class HTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):
    ConnectionCls = HTTPConnection  # type: ignore


def HTTPNodeClassFactory(
    context_name: str,
    cache_enabled: bool,
    username: str | None,
    password: str | None,
) -> type[CacheHttpNode]:
    class HTTPNode(CacheHttpNode):
        def __init__(self, config: NodeConfig):
            super().__init__(config, context_name, cache_enabled)
            kw = self.pool.conn_kw
            if username is not None and password is not None:
                auth = b64encode(f"{username}:{password}".encode("utf-8")).decode(
                    "utf-8"
                )
                self._headers["Authorization"] = f"Basic {auth}"
            self.pool = HTTPConnectionPool(
                config.host,
                port=config.port,
                timeout=urllib3.Timeout(total=config.request_timeout),
                maxsize=config.connections_per_node,
                block=True,
                **kw,
            )

    return HTTPNode


def KubeNodeClassFactory(
    context_name: str,
    cache_enabled: bool,
    kube_context: str,
    kube_namespace: str,
    es_name: str,
) -> Type[CacheHttpNode]:
    kube_config.load_kube_config(context=kube_context)
    k8s_api = kube_client.CoreV1Api()
    pod_name = next(
        pod.metadata.name
        for pod in k8s_api.list_namespaced_pod(
            namespace=kube_namespace,
            label_selector=",".join(
                (
                    f"elasticsearch.k8s.elastic.co/cluster-name={es_name}",
                    "elasticsearch.k8s.elastic.co/node-master=true",
                )
            ),
        ).items
    )

    secrets = k8s_api.list_namespaced_secret(
        namespace=kube_namespace,
        label_selector=",".join(
            (
                f"elasticsearch.k8s.elastic.co/cluster-name={es_name}",
                "eck.k8s.elastic.co/credentials=true",
            )
        ),
    )
    elastic_secret = next(
        secret.data
        for secret in secrets.items
        if "elastic-user" in secret.metadata.name
    )
    username = next(iter(elastic_secret.keys()))
    password = b64decode(next(iter(elastic_secret.values()))).decode("utf-8")

    class KubeHTTPConnection(HTTPConnection):
        def _new_conn(self) -> socket.socket:
            pf: PortForward = portforward(
                k8s_api.connect_get_namespaced_pod_portforward,
                pod_name,
                kube_namespace,
                ports=str(self.port),
            )
            return pf.socket(self.port)

    class KubePortForwardConnectionPool(urllib3.connectionpool.HTTPConnectionPool):
        ConnectionCls = KubeHTTPConnection  # type: ignore

    class KubeHttpNode(CacheHttpNode):
        basic_auth = (username, password)

        def __init__(self, config: NodeConfig):
            super().__init__(config, context_name, cache_enabled)
            kw = self.pool.conn_kw
            auth = b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
            self._headers["Authorization"] = f"Basic {auth}"
            self.pool = KubePortForwardConnectionPool(
                config.host,
                port=config.port,
                timeout=urllib3.Timeout(total=config.request_timeout),
                maxsize=config.connections_per_node,
                block=True,
                **kw,
            )

    return KubeHttpNode
