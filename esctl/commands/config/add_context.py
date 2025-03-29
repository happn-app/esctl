from typing_extensions import Annotated
import typer

from esctl.config import read_config

app = typer.Typer()

@app.command(help="Add an HTTP context")
def http(
    context_name: Annotated[str, typer.Argument(help="Name of the context")],
    host: Annotated[
        str, typer.Option("--host", "-h", help="Hostname of the cluster")
    ] = "localhost",
    port: Annotated[
        int, typer.Option("--port", "-p", help="Port the ES master listens on")
    ] = 9200,
    username: Annotated[
        str,
        typer.Option(
            "--username",
            "-u",
            help="Username of the user to connect as, using basic auth",
        ),
    ] = None,
    password: Annotated[
        str,
        typer.Option(
            "--password",
            "-p",
            help="Password of the user to connect as, using basic auth",
        ),
    ] = None,
):
    config = read_config()
    config.add_context(
        context_name,
        "http",
        host=host,
        port=port,
        username=username,
        password=password,
    )
    typer.echo(f"Context {context_name} added for Elasticsearch at {host}:{port}")


@app.command(help="Add a Kubernetes context")
def kubernetes(
    context_name: Annotated[str, typer.Argument(help="Name of the context")],
    namespace: Annotated[
        str,
        typer.Option(
            "--namespace",
            "-n",
            help="Namespace of the Kubernetes cluster",
        ),
    ] = "default",
    context: Annotated[
        str,
        typer.Option(
            "--context",
            "-c",
            help="Context, in the kubeconfig file for the kubernetes cluster",
        ),
    ] = None,
    es_name: Annotated[
        str,
        typer.Option(
            "--es-name",
            "-e",
            help="Name of the Elasticsearch cluster in Kubernetes",
        ),
    ] = None,
):
    config = read_config()
    config.add_context(
        context_name,
        "kubernetes",
        kube_namespace=namespace,
        kube_context=context,
        es_name=es_name,
    )
    typer.echo(f"Context {context_name} added for Kubernetes cluster in {namespace}")
