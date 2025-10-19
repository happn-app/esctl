from typing_extensions import Annotated
import typer

from esctl.config import Config

app = typer.Typer(rich_markup_mode="rich")


@app.command(help="Add an HTTP context")
def http(
    ctx: typer.Context,
    context_name: Annotated[str, typer.Argument(help="Name of the context")],
    host: Annotated[
        str, typer.Option("--host", "-h", help="Hostname of the cluster")
    ] = "localhost",
    port: Annotated[
        int, typer.Option("--port", "-p", help="Port the ES master listens on")
    ] = 9200,
    username: (
        Annotated[
            str,
            typer.Option(
                "--username",
                "-u",
                help="Username of the user to connect as, using basic auth",
            ),
        ]
        | None
    ) = None,
    password: (
        Annotated[
            str,
            typer.Option(
                "--password",
                "-p",
                help="Password of the user to connect as, using basic auth",
                envvar="ESCTL_PASSWORD",
            ),
        ]
        | None
    ) = None,
):
    config = Config.load()
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
    ctx: typer.Context,
    context_name: Annotated[str, typer.Argument(help="Name of the context")],
    namespace: Annotated[
        str,
        typer.Option(
            "--namespace",
            "-n",
            help="Namespace of the Kubernetes cluster",
        ),
    ] = "default",
    context: (
        Annotated[
            str,
            typer.Option(
                "--context",
                "-c",
                help="Context, in the kubeconfig file for the kubernetes cluster",
            ),
        ]
        | None
    ) = None,
    es_name: (
        Annotated[
            str,
            typer.Option(
                "--es-name",
                "-e",
                help="Name of the Elasticsearch cluster in Kubernetes",
            ),
        ]
        | None
    ) = None,
):
    config = Config.load()
    config.add_context(
        context_name,
        "kubernetes",
        kube_namespace=namespace,
        kube_context=context,
        es_name=es_name,
    )
    typer.echo(f"Context {context_name} added for Kubernetes cluster in {namespace}")


@app.command(help="Add a GCE context")
def gce(
    ctx: typer.Context,
    context_name: Annotated[str, typer.Argument(help="Name of the context")],
    project: Annotated[str, typer.Option("--project", "-p", help="GCP Project ID")],
    zone: Annotated[
        str, typer.Option("--zone", "-z", help="GCP Zone of the ES cluster")
    ],
    instance: Annotated[
        str, typer.Option("--instance", "-i", help="GCE Instance name of the ES node")
    ],
    port: Annotated[
        int, typer.Option("--port", "-P", help="Port the ES master listens on")
    ] = 9200,
    target_port: Annotated[
        int,
        typer.Option(
            "--target-port",
            "-p",
            help="Local port to use for the SSH tunnel to the ES node",
        ),
    ] = 9200,
    username: Annotated[
        str,
        typer.Option(
            "--username",
            "-u",
            help="Username of the user to connect as, using basic auth",
        ),
    ] = "",
    password: Annotated[
        str,
        typer.Option(
            "--password",
            "-p",
            help="Password of the user to connect as, using basic auth",
            envvar="ESCTL_PASSWORD",
        ),
    ] = "",
):
    config = Config.load()
    config.add_context(
        context_name,
        "gce",
        project_id=project,
        zone=zone,
        vm_name=instance,
        port=port,
        target_port=target_port,
        username=username,
        password=password,
    )
    typer.echo(f"Context {context_name} added for GCE instance {instance}")
