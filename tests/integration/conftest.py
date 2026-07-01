"""Fixtures for Elasticsearch integration tests (require Docker)."""

import pytest

from testcontainers.elasticsearch import ElasticSearchContainer

# Pin a concrete supported image. testcontainers disables xpack security for
# 8.x/9.x images, so no auth is needed against the container.
ES_IMAGE = "docker.elastic.co/elasticsearch/elasticsearch:8.15.0"


@pytest.fixture(scope="session")
def es_container():
    with ElasticSearchContainer(ES_IMAGE, mem_limit="2G") as container:
        yield container


@pytest.fixture
def es_host(es_container):
    """Hostname the container is reachable on from the test process."""
    return es_container.get_container_host_ip()


@pytest.fixture
def es_port(es_container):
    """Mapped (random) host port for the container's 9200."""
    return int(es_container.get_exposed_port(es_container.port))


@pytest.fixture
def http_config(es_host, es_port):
    """An HTTPESConfig pointing at the running container."""
    from esctl.config.models.http import HTTPESConfig

    return HTTPESConfig(type="http", name="test", host=es_host, port=es_port)


@pytest.fixture
def cli_config_file(es_host, es_port, write_config):
    """Write a Config with a single 'test' http context to ESCTL_CONFIG_PATH.

    Returns the context name to pass via ``--context``.
    """
    from esctl.config.config import Config
    from esctl.config.models.http import HTTPESConfig

    cfg = Config(
        contexts={
            "test": HTTPESConfig(type="http", name="test", host=es_host, port=es_port)
        },
        current_context="test",
    )
    write_config(cfg)
    return "test"
