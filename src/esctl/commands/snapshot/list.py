from contextlib import suppress
from datetime import timedelta
from typing import Annotated
import typer

from esctl.completions import complete_repository
from config import Config
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import FormatOption
from esctl.utils import get_root_ctx, strfdelta

app = typer.Typer()


def formatter(header: list[str], row: list[str]) -> list[str]:
    with suppress(ValueError):
        status_idx = header.index("state")
        if row[status_idx] == "SUCCESS":
            row[status_idx] = f"[b green]{row[status_idx]}[/]"
        elif row[status_idx] == "PARTIAL":
            row[status_idx] = f"[b yellow]{row[status_idx]}[/]"
        elif row[status_idx] == "FAILED":
            row[status_idx] = f"[b red]{row[status_idx]}[/]"
        elif row[status_idx] == "INCOMPATIBLE":
            row[status_idx] = f"[b red]{row[status_idx]}[/]"
        elif row[status_idx] == "IN_PROGRESS":
            row[status_idx] = f"[b blue]{row[status_idx]}[/]"
    with suppress(ValueError):
        shards = header.index("shards")
        percent = float(row[shards].split("%")[0])
        if percent < 50:
            row[shards] = f"[b red]{row[shards]}[/]"
        elif percent < 75:
            row[shards] = f"[b yellow]{row[shards]}[/]"
        else:
            row[shards] = f"[b green]{row[shards]}[/]"
    return row


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


@app.command(
    name="list",
    help="Lists snapshots in a repository.",
)
def _list(
    ctx: typer.Context,
    repository: Annotated[
        str, typer.Argument(autocompletion=complete_repository)
    ] = "*",
    format: FormatOption = Format.text,
):
    """
    Restore a snapshot from a repository.
    """
    client = Config.from_context(ctx).client
    snapshots = client.snapshot.get(repository=repository, snapshot="*").body[
        "snapshots"
    ]
    if format == Format.text:
        pretty_print(
            [format_snapshot_for_text(s) for s in snapshots],
            format=format,
            formatter=formatter,
            pretty=get_root_ctx(ctx).obj.get("pretty", True),
        )
    else:
        pretty_print(
            snapshots,
            format=Format.json,
            pretty=get_root_ctx(ctx).obj.get("pretty", True),
        )
