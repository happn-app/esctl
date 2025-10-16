from typing import Literal

from transport import Elasticsearch, KubeClientFactory

from .base import ESConfig


class KubeESConfig(ESConfig):
    type: Literal["kubernetes"] = "kubernetes"

    kube_context: str | None = None
    kube_namespace: str | None = None
    es_name: str | None = None

    @property
    def censored_password(self) -> str:
        return "*********"

    @property
    def client(self) -> Elasticsearch:
        if (
            self.kube_context is None
            or self.kube_namespace is None
            or self.es_name is None
        ):
            raise ValueError(
                "kube_context, kube_namespace and es_name must be set for kubernetes contexts"
            )
        return KubeClientFactory(
            self.name,
            self.cache_enabled,
            self.kube_context,
            self.kube_namespace,
            self.es_name,
        )
