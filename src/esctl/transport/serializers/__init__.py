from elasticsearch8.serializer import Serializer as Serializer8
from elasticsearch9.serializer import Serializer as Serializer9

from elasticsearch8.serializer import DEFAULT_SERIALIZERS as DEFAULT_SERIALIZERS8
from elasticsearch9.serializer import DEFAULT_SERIALIZERS as DEFAULT_SERIALIZERS9

from .yaml import YamlSerializer8, YamlSerializer9


Serializer = Serializer8 | Serializer9

SERIALIZERS8 = DEFAULT_SERIALIZERS8 | {
    "application/yaml": YamlSerializer8(),
    "application/yml": YamlSerializer8(),
}
SERIALIZERS9 = DEFAULT_SERIALIZERS9 | {
    "application/yaml": YamlSerializer9(),
    "application/yml": YamlSerializer9(),
}
