from elasticsearch7.serializer import Serializer as Serializer7
from elasticsearch8.serializer import Serializer as Serializer8
from elasticsearch9.serializer import Serializer as Serializer9

from elasticsearch7.serializer import DEFAULT_SERIALIZERS as DEFAULT_SERIALIZERS7
from elasticsearch8.serializer import DEFAULT_SERIALIZERS as DEFAULT_SERIALIZERS8
from elasticsearch9.serializer import DEFAULT_SERIALIZERS as DEFAULT_SERIALIZERS9

from .yaml import YamlSerializer7, YamlSerializer8, YamlSerializer9


Serializer = Serializer7 | Serializer8 | Serializer9

SERIALIZERS7 = DEFAULT_SERIALIZERS7 | {
    "application/yaml": YamlSerializer7(),
    "application/yml": YamlSerializer7(),
}
SERIALIZERS8 = DEFAULT_SERIALIZERS8 | {
    "application/yaml": YamlSerializer8(),
    "application/yml": YamlSerializer8(),
}
SERIALIZERS9 = DEFAULT_SERIALIZERS9 | {
    "application/yaml": YamlSerializer9(),
    "application/yml": YamlSerializer9(),
}
