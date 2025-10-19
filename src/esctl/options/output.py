import csv
from io import StringIO
import json
from typing import Annotated, Any, Callable, Iterable

from elastic_transport import ObjectApiResponse
from jmespath import compile as compile_jmespath
from jsonpath_ng import parse as parse_jsonpath
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from ruamel.yaml import YAML
import typer

from esctl.config.utils import get_root_ctx

OUTPUT_FORMATS = (
    "json",
    "yaml",
    "table",
    "csv",
    "tsv",
    "jsonpath=",
    "jmespath=",
)


def _default_formatter(_: str, value: str) -> str:
    return value


class Result:
    def __init__(self, value: Any, pretty: bool = True):
        self.value = value
        self.pretty = pretty
        # Use to map column names to pretty headers, e.g. "node.id" -> "Node ID"
        self.header_names: dict[str, str] = {}
        # Use to exclude certain headers from the output (e.g. internal fields)
        self.exclude_headers: set[str] = set()
        self.console = Console()

    def _print_json(self) -> None:
        self.console.print(
            Syntax(json.dumps(self.value, indent=2), "json", line_numbers=True)
        )

    def _print_yaml(self) -> None:
        yaml = YAML()
        yaml.default_flow_style = False

        stream = StringIO()
        yaml.dump(self.value, stream)
        stream.seek(0)
        if self.pretty:
            self.console.print(Syntax(stream.getvalue(), "yaml", line_numbers=True))
        else:
            self.console.print(stream.getvalue())

    def _make_table(self) -> tuple[list[str], list[dict]]:
        if isinstance(self.value, list) and all(
            isinstance(item, dict) for item in self.value
        ):
            # Assume that all dicts have uniform keys
            header = list(self.value[0].keys()) if self.value else []
            return [h for h in header if h not in self.exclude_headers], self.value
        elif isinstance(self.value, dict):
            return [h for h in self.value.keys() if h in self.header_names], [
                self.value
            ]
        else:
            raise ValueError("Cannot convert value to table format")

    def _print_csv(self) -> None:
        stream = StringIO()
        writer = csv.writer(stream)
        header, table = self._make_table()
        writer.writerow([self.header_names.get(h, h) for h in header])
        for row in table:
            writer.writerow([row.get(col, "") for col in header])
        self.console.print(stream.getvalue())

    def _print_tsv(self) -> None:
        stream = StringIO()
        writer = csv.writer(stream, delimiter="\t")
        header, table = self._make_table()
        writer.writerow([self.header_names.get(h, h) for h in header])
        for row in table:
            writer.writerow([row.get(col, "") for col in header])
        self.console.print(stream.getvalue())

    def _print_table(
        self,
        formatter: Callable[[str, str], str] | None = None,
    ) -> None:
        if formatter is None:
            formatter = _default_formatter
        header, table = self._make_table()
        rich_table = Table(*[self.header_names.get(h, h) for h in header])
        for row in table:
            rich_table.add_row(
                *[formatter(col, str(row.get(col, ""))) for col in header]
            )
        self.console.print(rich_table)

    def print(
        self,
        output: str,
        formatter: Callable[[str, str], str] | None = None,
    ) -> None:
        match output:
            case "json" if self.pretty:
                self._print_json()
            case "json" if not self.pretty:
                print(json.dumps(self.value))
            case "yaml":
                self._print_yaml()
            case "table":
                self._print_table(formatter)
            case "csv":
                self._print_csv()
            case "tsv":
                self._print_tsv()
            case _:
                print(self.value)


def complete_output(ctx: typer.Context, incomplete: str) -> Iterable[str]:
    for fmt in OUTPUT_FORMATS:
        if fmt.startswith(incomplete):
            yield fmt


def noop_selector(pretty: bool) -> Callable[[ObjectApiResponse], Result]:
    def selector(response: ObjectApiResponse) -> Result:
        return Result(response.body, pretty)

    return selector


def jsonpath_selector(
    jsonpath: str, pretty: bool
) -> Callable[[ObjectApiResponse], Result]:
    def selector(response: ObjectApiResponse) -> Any:
        value = parse_jsonpath(jsonpath[len("jsonpath=") :]).find(response.body)
        if isinstance(value, Iterable):
            value = [match.value for match in value]
            if len(value) == 1:
                return Result(value[0], pretty)
            return Result(value, pretty)
        else:
            return Result(value.value, pretty)

    return selector


def jmespath_selector(
    jmespath: str, pretty: bool
) -> Callable[[ObjectApiResponse], Result]:
    def selector(response: ObjectApiResponse) -> Any:
        return Result(
            compile_jmespath(jmespath[len("jmespath=") :]).search(response.body),
            pretty,
        )

    return selector


def validate_output(ctx: typer.Context, value: str | None) -> str:
    if ctx.obj is None:
        ctx.obj = {}
    root_ctx = get_root_ctx(ctx)
    pretty: bool = root_ctx.obj.get("pretty", True)
    ctx.obj["selector"] = noop_selector(pretty)
    if value is None:
        return "table"

    if not any(value.startswith(fmt) for fmt in OUTPUT_FORMATS):
        raise typer.BadParameter(
            f"Invalid output format: {value}. Must be one of: {', '.join(OUTPUT_FORMATS)}"
        )

    if value.startswith("jsonpath"):
        ctx.obj["selector"] = jsonpath_selector(value, pretty)
        return "json"

    if value.startswith("jmespath"):
        ctx.obj["selector"] = jmespath_selector(value, pretty)
        return "json"
    return value


OutputOption = Annotated[
    str,
    typer.Option(
        "-o",
        "--output",
        help="Output format. One of: (json, yaml, table, csv, tsv, jsonpath=EXPR, jmespath=EXPR)",
        autocompletion=complete_output,
        callback=validate_output,
    ),
]
