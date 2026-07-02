"""HTTP client factory against a real Elasticsearch container."""

import pytest

pytestmark = pytest.mark.integration


def test_client_connects_and_info(http_config):
    client = http_config.client
    info = client.info()
    body = info.body if hasattr(info, "body") else info
    assert body["version"]["number"].startswith("8.")


def test_version_detection_selects_es8_client(http_config):
    from elasticsearch8 import Elasticsearch as Elasticsearch8

    client = http_config.client
    # The prod fix means the probe hits the real (random) port and correctly
    # dispatches to the ES8 client class for an 8.x cluster.
    assert isinstance(client, Elasticsearch8)


def test_probe_uses_real_port_not_9200(http_config):
    # Sanity: the container port is not the hardcoded 9200. If detection still
    # used localhost:9200 this whole call would fail to connect.
    assert http_config.port != 9200
    assert http_config.client.info()
