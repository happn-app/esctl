from typing import Literal

from transport import Elasticsearch, HTTPClientFactory

from .base import ESConfig


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
        if self.password is None:
            return ""
        return self.password[:4] + "*" * (len(self.password) - 4)

    @property
    def client(self) -> Elasticsearch:
        return HTTPClientFactory(
            self.name,
            self.cache_enabled,
            self.url,
            self.username,
            self.password,
        )
