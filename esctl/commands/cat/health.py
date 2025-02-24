from contextlib import suppress

import typer

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.params import FormatOption, HeaderOption, SortOption, TimeOption
from esctl.selectors import select_from_context
from esctl.utils import get_cat_base_params_from_context

app = typer.Typer()


def formatter(header: list[str], row: list[str]) -> list[str]:
    with suppress(ValueError):
        status_idx = header.index("status")
        if row[status_idx] == "green":
            row[status_idx] = f"[b green]{row[status_idx]}[/]"
        elif row[status_idx] == "yellow":
            row[status_idx] = f"[b yellow]{row[status_idx]}[/]"
        elif row[status_idx] == "red":
            row[status_idx] = f"[b red]{row[status_idx]}[/]"
    with suppress(ValueError):
        active_shards_percent_idx = header.index("active_shards_percent")
        active_shards_percent_as_number = float(
            row[active_shards_percent_idx].replace("%", "")
        )
        if active_shards_percent_as_number < 50:
            row[active_shards_percent_idx] = (
                f"[b red]{row[active_shards_percent_idx]}[/]"
            )
        elif active_shards_percent_as_number < 75:
            row[active_shards_percent_idx] = (
                f"[b yellow]{row[active_shards_percent_idx]}[/]"
            )
        else:
            row[active_shards_percent_idx] = (
                f"[b green]{row[active_shards_percent_idx]}[/]"
            )
    with suppress(ValueError):
        unassign_idx = header.index("unassign")
        if row[unassign_idx] == "0":
            row[unassign_idx] = f"[b green]{row[unassign_idx]}[/]"
        else:
            row[unassign_idx] = f"[b red]{row[unassign_idx]}[/]"
    return row


@app.command(
    help="Returns the health status of a cluster, similar to the cluster health API.",
    short_help="Returns the health status of a cluster.",
)
def health(
    ctx: typer.Context,
    header: HeaderOption = None,
    sort: SortOption = None,
    time: TimeOption = None,
    ts: bool = False,
    format: FormatOption = Format.text,
):
    params = get_cat_base_params_from_context(ctx, format)
    params.update(
        {
            "h": ",".join(header) if header else None,
            "s": ",".join(sort) if sort else None,
            "time": time,
            "ts": ts,
        }
    )
    client = get_client_from_ctx(ctx)
    response = client.cat.health(**params)
    response = select_from_context(ctx, response)
    pretty_print(response, format=params["format"], formatter=formatter)
