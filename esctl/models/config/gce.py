import os
import signal
import socket
import subprocess
import time
from typing import Literal

from elastic_transport import NodeConfig, Urllib3HttpNode
from elasticsearch import Elasticsearch
from elasticsearch.serializer import JsonSerializer, NdjsonSerializer, TextSerializer
import urllib3
from urllib3.connection import HTTPConnection as Urllib3HTTPConnection

from esctl.models.config.base import ESConfig
from esctl.serializer import YamlSerializer


_GCE_SSH_PROCESS = None


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
    ConnectionCls = HTTPConnection  # type: ignore


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


class GCEESConfig(ESConfig):
    type: Literal["gce"] = "gce"
    vm_name: str
    project_id: str
    zone: str
    username: str | None = None
    password: str | None = None
    port: int = 9200
    target_port: int = 9200

    @property
    def url(self) -> str:
        return f"http://localhost:{self.target_port}"

    @property
    def basic_auth(self) -> tuple[str, str] | None:
        if self.username is None or self.password is None:
            return None
        return (self.username, self.password)

    @property
    def censored_password(self) -> str:
        if self.password is None:
            return ""
        return self.password[:4] + "*" * (len(self.password) - 4)

    def _wait_port(self, host: str, port: int, timeout: float = 10.0) -> bool:
        """Wait until TCP port is connectable or timeout."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with socket.socket() as s:
                s.settimeout(0.5)
                try:
                    s.connect((host, port))
                    return True
                except OSError:
                    time.sleep(0.01)
        return False

    def start_ssh_tunnel(self) -> None:
        global _GCE_SSH_PROCESS
        if _GCE_SSH_PROCESS is not None and _GCE_SSH_PROCESS.poll() is None:
            return  # Tunnel already running
        process = subprocess.Popen([
                "gcloud", "compute", "ssh",
                f"--ssh-flag=-N -L {self.port}:localhost:{self.target_port}",
                f"--project={self.project_id}",
                f"--zone={self.zone}",
                self.vm_name,
            ],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )

        _GCE_SSH_PROCESS = process
        self._wait_port("localhost", self.target_port, timeout=10.0)
        return

    def stop_ssh_tunnel(self) -> None:
        global _GCE_SSH_PROCESS
        if _GCE_SSH_PROCESS is not None:
            os.killpg(os.getpgid(_GCE_SSH_PROCESS.pid), signal.SIGKILL)
            _GCE_SSH_PROCESS.wait()
            _GCE_SSH_PROCESS = None

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
