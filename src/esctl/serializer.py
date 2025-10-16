import io
from typing import Any

from elasticsearch.serializer import Serializer
from ruamel.yaml import YAML


class YamlSerializer(Serializer):
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
