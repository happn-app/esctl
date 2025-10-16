import io
from typing import Any

from elasticsearch7.serializer import Serializer as Serializer7
from elasticsearch8.serializer import Serializer as Serializer8
from elasticsearch9.serializer import Serializer as Serializer9
from ruamel.yaml import YAML


class YamlSerializer7(Serializer7):
    mimetype = "application/yaml"

    def loads(self, s: str) -> Any:
        stream = io.StringIO(s)
        yaml = YAML()
        return yaml.load(stream)

    def dumps(self, data: Any) -> str:
        yaml = YAML()
        buffer = io.StringIO()
        yaml.dump(data, buffer)
        return buffer.getvalue()


class YamlSerializer8(Serializer8):
    mimetype = "application/yaml"

    def loads(self, data: bytes) -> Any:
        stream = io.BytesIO(data)
        yaml = YAML()
        return yaml.load(stream)

    def dumps(self, data: Any) -> bytes:
        yaml = YAML()
        buffer = io.BytesIO()
        yaml.dump(data, buffer)
        return buffer.getvalue()


class YamlSerializer9(Serializer9):
    mimetype = "application/yaml"

    def loads(self, data: bytes) -> Any:
        stream = io.BytesIO(data)
        yaml = YAML()
        return yaml.load(stream)

    def dumps(self, data: Any) -> bytes:
        yaml = YAML()
        buffer = io.BytesIO()
        yaml.dump(data, buffer)
        return buffer.getvalue()
