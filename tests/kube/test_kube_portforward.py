"""End-to-end test of the Kubernetes port-forward connection path (slow)."""

import pytest

pytestmark = pytest.mark.kube


def _kube_config(kube_context_name, namespace, es_name):
    from esctl.config.models.kube import KubeESConfig

    return KubeESConfig(
        type="kubernetes",
        name="test",
        kube_context=kube_context_name,
        kube_namespace=namespace,
        es_name=es_name,
    )


def test_portforward_client_connects(
    deployed_es, kube_context_name, namespace, es_name
):
    """Finds pod by label, reads secret, port-forwards, detects version, queries."""
    config = _kube_config(kube_context_name, namespace, es_name)
    client = config.client
    info = client.info()
    body = info.body if hasattr(info, "body") else info
    assert body["version"]["number"].startswith("8.")


def test_portforward_cat_health(deployed_es, kube_context_name, namespace, es_name):
    client = _kube_config(kube_context_name, namespace, es_name).client
    health = client.cat.health(format="json")
    body = health.body if hasattr(health, "body") else health
    assert len(body) >= 1


def test_no_matching_pod_raises(deployed_es, kube_context_name, namespace):
    """A cluster name with no matching pod fails fast at pod lookup."""
    with pytest.raises(StopIteration):
        _kube_config(kube_context_name, namespace, "does-not-exist").client
