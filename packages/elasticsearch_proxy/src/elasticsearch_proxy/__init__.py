from elasticsearch7_proxy import Elasticsearch as ES7
from elasticsearch8_proxy import Elasticsearch as ES8
from elasticsearch9_proxy.src.elasticsearch9_proxy import Elasticsearch as ES9

def get_client() -> ES9 | ES8 | ES7:
