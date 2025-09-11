import io
import json
import re
from typing import Any, Callable

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from ruamel.yaml import YAML

from esctl.models.enums import Format


RM_WHITESPACE = re.compile(r"\s+")


def parse_row(row: str, maxsplit: int = -1) -> list[str]:
    row = RM_WHITESPACE.sub(" ", row)
    return [column.strip() for column in row.split(" ", maxsplit) if column]


def default_formatter(header: list[str], row: list[str]) -> list[str]:
    return row


def pretty_print(
    response: Any, format: Format,
    formatter: Callable[[list[str], list[str]], list[str]] | None = None,
) -> None:
    console = Console()
    if formatter is None:
        formatter = default_formatter
    if format == Format.text:
        # Table
        rows: list[str] = response.splitlines()
        header = parse_row(rows.pop(0))
        table = Table(*header)
        for row in rows:
            table.add_row(*formatter(header, parse_row(row, len(header) - 1)))
        console.print(table)
    elif format == Format.json:
        console.print(Syntax(json.dumps(response, indent=2), "json", line_numbers=True))
    elif format == Format.yaml and not isinstance(
        response, (str, int, bytes, float, bool)
    ):
        yaml = YAML()
        buffer = io.StringIO()
        yaml.dump(response, buffer)
        buffer.seek(0)
        console.print(Syntax(buffer.read(), "yaml", line_numbers=False))
    else:
        console.print(response)
