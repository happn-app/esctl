"""Drive real CAT commands through the Typer CLI against a live container."""

import importlib

import pytest
from typer.testing import CliRunner

pytestmark = pytest.mark.integration


@pytest.fixture
def app(cli_config_file):
    """Import the CLI app *after* the config file is written.

    ``esctl.cli`` binds ``cfg = Config.load()`` at import time, so we reload the
    module to pick up the freshly-written config context.
    """
    import esctl.cli as cli_module

    importlib.reload(cli_module)
    return cli_module.app


@pytest.fixture
def seed_index(http_config):
    """Create a small index so CAT commands have something to return."""
    client = http_config.client
    if client.indices.exists(index="test-index"):
        client.indices.delete(index="test-index")
    client.indices.create(index="test-index")
    client.index(index="test-index", document={"hello": "world"}, refresh=True)
    yield "test-index"


def test_cat_health(app):
    result = CliRunner().invoke(app, ["--no-cache", "-c", "test", "cat", "health"])
    assert result.exit_code == 0, result.output


def test_cat_indices_lists_seeded_index(app, seed_index):
    result = CliRunner().invoke(
        app, ["--no-cache", "-c", "test", "cat", "indices", "-o", "json"]
    )
    assert result.exit_code == 0, result.output
    assert seed_index in result.output


def test_cat_nodes(app):
    # `cat nodes` requires an explicit --header/-h column selection.
    result = CliRunner().invoke(
        app, ["--no-cache", "-c", "test", "cat", "nodes", "-h", "name"]
    )
    assert result.exit_code == 0, result.output
