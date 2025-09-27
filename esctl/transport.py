import time
from elastic_transport import HttpHeaders, NodeConfig, Urllib3HttpNode
from elastic_transport._node._base import NodeApiResponse
from elastic_transport.client_utils import DefaultType

from esctl.cache import Cache


class CacheHttpNode(Urllib3HttpNode):
    def __init__(self, config: NodeConfig, context_name: str):
        super().__init__(config)
        self.cache = Cache(context_name)

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
            return super().perform_request(method, target, body, headers, request_timeout)
        start_time = time.time()
        response = self.cache.get(method, target, headers)
        if response is not None:
            response.meta.duration = time.time() - start_time
            response.meta.node = self.config
            return response
        response = super().perform_request(method, target, body, headers, request_timeout)
        self.cache.set(method, target, response, headers=headers, ttl=Cache.get_ttl(f"{method.upper()} {target}"))
        return response
