"""Fixtures for the Kubernetes port-forward path (require Docker; slow).

Boots a real k3s cluster via testcontainers, then reproduces the ECK label
conventions (pod + credentials secret) that ``KubeNodeClassFactory`` looks for
in ``src/esctl/transport/transport.py`` — WITHOUT running the ECK operator.
"""

import base64
import os
import tempfile
import time

import pytest
import yaml

from testcontainers.k3s import K3SContainer

K3S_IMAGE = "rancher/k3s:v1.31.5-k3s1"
ES_IMAGE = "docker.elastic.co/elasticsearch/elasticsearch:8.15.0"

NAMESPACE = "default"
ES_NAME = "testcluster"
ES_USERNAME = "elastic"
ES_PASSWORD = "testpassword"

CLUSTER_LABEL = "elasticsearch.k8s.elastic.co/cluster-name"


@pytest.fixture
def namespace():
    return NAMESPACE


@pytest.fixture
def es_name():
    return ES_NAME


@pytest.fixture(scope="session")
def k3s_container():
    with K3SContainer(K3S_IMAGE) as container:
        yield container


@pytest.fixture(scope="session")
def kubeconfig_file(k3s_container):
    """Write k3s kubeconfig to a temp file and point KUBECONFIG at it.

    esctl's KubeNodeClassFactory calls ``load_kube_config(context=...)`` which
    reads $KUBECONFIG, so the production code path runs unmodified.
    """
    cfg_yaml = k3s_container.config_yaml()
    path = os.path.join(tempfile.mkdtemp(prefix="k3s-kubeconfig-"), "config")
    with open(path, "w") as fh:
        fh.write(cfg_yaml)
    prev = os.environ.get("KUBECONFIG")
    os.environ["KUBECONFIG"] = path
    yield path, cfg_yaml
    if prev is None:
        os.environ.pop("KUBECONFIG", None)
    else:
        os.environ["KUBECONFIG"] = prev


@pytest.fixture(scope="session")
def kube_context_name(kubeconfig_file):
    _, cfg_yaml = kubeconfig_file
    return yaml.safe_load(cfg_yaml)["current-context"]


@pytest.fixture(scope="session")
def k8s_api(kubeconfig_file):
    from kubernetes import client as kube_client
    from kubernetes import config as kube_config

    path, _ = kubeconfig_file
    kube_config.load_kube_config(config_file=path)
    return kube_client.CoreV1Api()


@pytest.fixture(scope="session")
def deployed_es(k8s_api):
    """Create the credentials secret + ES pod with ECK labels; wait for Ready."""
    from kubernetes import client as kube_client

    # Secret: name must contain "elastic-user"; key = username, value = b64(password).
    secret = kube_client.V1Secret(
        metadata=kube_client.V1ObjectMeta(
            name=f"{ES_NAME}-es-elastic-user",
            namespace=NAMESPACE,
            labels={
                CLUSTER_LABEL: ES_NAME,
                "eck.k8s.elastic.co/credentials": "true",
            },
        ),
        data={
            ES_USERNAME: base64.b64encode(ES_PASSWORD.encode()).decode(),
        },
    )
    k8s_api.create_namespaced_secret(namespace=NAMESPACE, body=secret)

    pod = kube_client.V1Pod(
        metadata=kube_client.V1ObjectMeta(
            name=f"{ES_NAME}-es-master-0",
            namespace=NAMESPACE,
            labels={
                CLUSTER_LABEL: ES_NAME,
                "elasticsearch.k8s.elastic.co/node-master": "true",
            },
        ),
        spec=kube_client.V1PodSpec(
            containers=[
                kube_client.V1Container(
                    name="elasticsearch",
                    image=ES_IMAGE,
                    ports=[kube_client.V1ContainerPort(container_port=9200)],
                    env=[
                        # single-node turns bootstrap checks into warnings, so
                        # vm.max_map_count etc. won't block startup in CI.
                        kube_client.V1EnvVar("discovery.type", "single-node"),
                        kube_client.V1EnvVar("xpack.security.enabled", "false"),
                        kube_client.V1EnvVar("ES_JAVA_OPTS", "-Xms512m -Xmx512m"),
                    ],
                    readiness_probe=kube_client.V1Probe(
                        http_get=kube_client.V1HTTPGetAction(port=9200, path="/"),
                        initial_delay_seconds=20,
                        period_seconds=5,
                        failure_threshold=30,
                    ),
                )
            ],
        ),
    )
    k8s_api.create_namespaced_pod(namespace=NAMESPACE, body=pod)

    _wait_pod_ready(k8s_api, f"{ES_NAME}-es-master-0", timeout=420)
    return ES_NAME


def _wait_pod_ready(k8s_api, pod_name, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pod = k8s_api.read_namespaced_pod(name=pod_name, namespace=NAMESPACE)
        conds = pod.status.conditions or []
        if any(c.type == "Ready" and c.status == "True" for c in conds):
            return
        time.sleep(3)

    # Distinguish an environment limitation from a real failure. Nested
    # containerd on Docker Desktop (macOS) frequently cannot create pod
    # sandboxes ("FailedCreatePodSandBox ... ttrpc: closed") — that is not a
    # bug in esctl, so skip rather than fail. On Linux CI the pod runs for real.
    events = k8s_api.list_namespaced_event(namespace=NAMESPACE).items
    msgs = [
        e.message or "" for e in events if pod_name in (e.involved_object.name or "")
    ]
    if any("FailedCreatePodSandBox" in (e.reason or "") for e in events):
        pytest.skip(
            "k3s runtime cannot create pod sandboxes on this host "
            "(known Docker Desktop / nested-containerd limitation); "
            "this test runs on a Linux CI Docker host. "
            f"Events: {msgs}"
        )
    raise TimeoutError(f"Pod {pod_name} not Ready within {timeout}s. Events: {msgs}")
