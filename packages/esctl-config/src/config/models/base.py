from transport import Elasticsearch
from pydantic import BaseModel, Field


class ESConfig(BaseModel):
    name: str = Field(exclude=True)
    cache_enabled: bool = Field(exclude=True, default=False)

    @property
    def client(self) -> Elasticsearch:
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def basic_auth(self) -> tuple[str, str] | None:
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def censored_password(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")
