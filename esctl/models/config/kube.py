from base64 import b64decode
import socket
from typing import Literal, Type

from elasticsearch import Elasticsearch
from elasticsearch.serializer import JsonSerializer, NdjsonSerializer, TextSerializer
from elastic_transport import NodeConfig, Transport, Urllib3HttpNode
from kubernetes import client as kube_client
from kubernetes import config as kube_config
from kubernetes.stream import portforward
from kubernetes.stream.ws_client import PortForward
import urllib3
from urllib3.connection import HTTPConnection

from esctl.models.config.base import ESConfig
from esctl.serializer import YamlSerializer


def KubeNodeClassFactory(
    kube_context: str,
    kube_namespace: str,
    es_name: str,
) -> Type[Transport]:
    kube_config.load_kube_config(context=kube_context)
    k8s_api = kube_client.CoreV1Api()
    pod_name = next(
        pod.metadata.name for pod in k8s_api.list_namespaced_pod(
            namespace=kube_namespace,
            label_selector=",".join((
                f"elasticsearch.k8s.elastic.co/cluster-name={es_name}",
                "elasticsearch.k8s.elastic.co/node-master=true",
            ))
        ).items
    )

    class KubeHTTPConnection(HTTPConnection):
        def _new_conn(self) -> socket.socket:
            pf: PortForward = portforward(
                k8s_api.connect_get_namespaced_pod_portforward,
                pod_name,
                kube_namespace,
                ports=str(self.port),
            )
            pf.socket(self.port)
            return pf.socket(self.port)

        def getresponse(self) -> urllib3.HTTPResponse:
            response = super().getresponse()
            # Hack around the fact that ES raises an exception if the
            # X-Elastic-Product header is not set, claiming an "unsupported product"
            # 100% is to not have AWS' version of ES be compatible with the client
            # library. Incidentally, this also breaks if trying to query a server
            # with version 7.10.0 or lower.
            response.headers["X-Elastic-Product"] = "Elasticsearch"
            return response

    class KubePortForwardConnectionPool(urllib3.connectionpool.HTTPConnectionPool):
        ConnectionCls = KubeHTTPConnection

    class KubeHttpNode(Urllib3HttpNode):
        def __init__(self, config: NodeConfig):
            super().__init__(config)
            kw = self.pool.conn_kw
            self.pool = KubePortForwardConnectionPool(
                config.host,
                port=config.port,
                timeout=urllib3.Timeout(total=config.request_timeout),
                maxsize=config.connections_per_node,
                block=True,
                **kw,
            )

    return KubeHttpNode


class KubeESConfig(ESConfig):
    type: Literal["kubernetes"] = "kubernetes"

    kube_context: str | None = None
    kube_namespace: str | None = None
    es_name: str | None = None

    @property
    def basic_auth(self) -> tuple[str, str]:
        kube_config.load_kube_config(context=self.kube_context)
        k8s_client = kube_client.CoreV1Api()
        secrets = k8s_client.list_namespaced_secret(
            namespace=self.kube_namespace,
            label_selector=",".join((
                f"elasticsearch.k8s.elastic.co/cluster-name={self.es_name}",
                "eck.k8s.elastic.co/credentials=true",
            )),
        )
        elastic_secret = next(secret.data for secret in secrets.items if "elastic-user" in secret.metadata.name)
        username = next(iter(elastic_secret.keys()))
        password = b64decode(next(iter(elastic_secret.values()))).decode("utf-8")
        return (username, password)

    @property
    def censored_password(self) -> str:
        _, password = self.basic_auth
        return password[:4] + "*" * (len(password) - 4)

    @property
    def client(self) -> Elasticsearch:
        return Elasticsearch(
            "http://127.0.0.1:9200",
            basic_auth=self.basic_auth,
            node_class=KubeNodeClassFactory(
                self.kube_context,
                self.kube_namespace,
                self.es_name,
            ),
            serializers={
                JsonSerializer.mimetype: JsonSerializer(),
                TextSerializer.mimetype: TextSerializer(),
                NdjsonSerializer.mimetype: NdjsonSerializer(),
                "application/yaml": YamlSerializer(),
                "application/yml": YamlSerializer(),
            },
        )
