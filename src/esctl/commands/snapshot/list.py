from datetime import timedelta
from typing import Annotated, Iterable
import typer

from esctl.config import Config
from esctl.options import OutputOption, Result
from esctl.utils import strfdelta

app = typer.Typer()


def formatter(column: str, value: str) -> str:
    if column == "state":
        match value:
            case "SUCCESS":
                return "[b green]SUCCESS[/]"
            case "PARTIAL":
                return "[b yellow]PARTIAL[/]"
            case "FAILED":
                return "[b red]FAILED[/]"
            case "INCOMPATIBLE":
                return "[b red]INCOMPATIBLE[/]"
            case "IN_PROGRESS":
                return "[b blue]IN_PROGRESS[/]"
    if column == "shards":
        percent = float(value.split("%")[0])
        if percent < 50:
            return f"[b red]{value}[/]"
        elif percent < 75:
            return f"[b yellow]{value}[/]"
        else:
            return f"[b green]{value}[/]"
    return value


def format_snapshot_for_text(snapshot: dict) -> dict:
    """Format a snapshot dictionary for text output."""
    shard_percent = snapshot.get("shards", {}).get("successful", 0) / snapshot.get(
        "shards", {}
    ).get("total", 1)
    duration = strfdelta(timedelta(milliseconds=snapshot.get("duration_in_millis", 0)))
    formatted = {
        "snapshot": snapshot.get("snapshot", ""),
        "repo": snapshot.get("repository", ""),
        "state": snapshot.get("state", ""),
        "indices": ",".join(
            sorted(
                index
                for index in snapshot.get("indices", [])
                if not index.startswith(".")
            )
        ),
        "shards": f"{shard_percent:.0%} ({snapshot.get('shards', {}).get('successful', 0)}/{snapshot.get('shards', {}).get('total', 0)})",
        "start_time": snapshot.get("start_time", ""),
        "end_time": snapshot.get("end_time", ""),
        "duration": duration,
    }
    return formatted


def complete_repository(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    client = Config.from_context(ctx).client
    repositories: list[str] = [
        repo["name"] for repo in client.snapshot.get_repository().body
    ]
    return [repo for repo in repositories if repo.startswith(incomplete)]


@app.command(
    name="list",
    help="Lists snapshots in a repository.",
)
def _list(
    ctx: typer.Context,
    repository: Annotated[
        str,
        typer.Argument(
            help="Repository to fetch snapshot list from",
            autocompletion=complete_repository,
        ),
    ] = "*",
    output: OutputOption = "json",
):
    """
    Restore a snapshot from a repository.
    """
    client = Config.from_context(ctx).client
    snapshots = client.snapshot.get(repository=repository, snapshot="*")
    result: Result = ctx.obj["selector"](snapshots)
    if output == "json" or output == "yaml":
        result.print(output)
        return
    result.value = [
        format_snapshot_for_text(s) for s in snapshots.body.get("snapshots", [])
    ]
