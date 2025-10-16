from contextlib import suppress

import typer
from esctl.config import Config

from esctl.enums import Format
from esctl.output import pretty_print
from esctl.params import (
    BytesOption,
    FormatOption,
    HeaderOption,
    LocalOnlyOption,
    SortOption,
)
from esctl.selectors import select_from_context
from esctl.utils import get_cat_base_params_from_context, get_root_ctx

app = typer.Typer(rich_markup_mode="rich")


def formatter(header: list[str], row: list[str]) -> list[str]:
    with suppress(ValueError):
        disk_percent_idx = header.index("disk.percent")
        disk_percent = float(row[disk_percent_idx].replace("%", ""))
        if disk_percent < 75:
            row[disk_percent_idx] = f"[b green]{row[disk_percent_idx]}[/]"
        elif disk_percent < 85:
            row[disk_percent_idx] = f"[b yellow]{row[disk_percent_idx]}[/]"
        else:
            row[disk_percent_idx] = f"[b red]{row[disk_percent_idx]}[/]"
    return row


@app.command(
    help="Returns the health status of a cluster, similar to the cluster health API.",
    short_help="Returns the health status of a cluster.",
)
def allocation(
    ctx: typer.Context,
    header: HeaderOption | None = None,
    sort: SortOption | None = None,
    bytes: BytesOption | None = None,
    format: FormatOption = Format.text,
    local_only: LocalOnlyOption = False,
):
    params = get_cat_base_params_from_context(ctx, format)
    params.update(
        {
            "h": ",".join(header) if header else None,
            "s": ",".join(sort) if sort else None,
            "bytes": bytes,
            "local": local_only,
        }
    )
    client = Config.from_context(ctx).client
    response = client.cat.allocation(**params)
    response = select_from_context(ctx, response)
    pretty_print(
        response,
        format=params["format"],
        formatter=formatter,
        pretty=get_root_ctx(ctx).obj.get("pretty", True),
    )
