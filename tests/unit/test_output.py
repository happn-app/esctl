from io import StringIO

import elastic_transport
import pytest
from rich.console import Console

from esctl.options.output import (
    Result,
    jmespath_selector,
    jsonpath_selector,
    noop_selector,
)


class FakeResponse(elastic_transport.ObjectApiResponse):
    """Minimal stand-in for elastic_transport.ObjectApiResponse."""

    def __init__(self, body):
        self._body = body


def test_make_table_from_list_of_dicts():
    r = Result([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    header, rows = r._make_table()
    assert header == ["a", "b"]
    assert rows == [{"a": 1, "b": 2}, {"a": 3, "b": 4}]


def test_make_table_excludes_headers():
    r = Result([{"a": 1, "epoch": 0, "timestamp": "x"}])
    r.exclude_headers.update({"epoch", "timestamp"})
    header, _ = r._make_table()
    assert header == ["a"]


def test_make_table_from_dict_uses_header_names():
    r = Result({"a": 1, "b": 2, "c": 3})
    r.header_names = {"a": "A", "c": "C"}
    header, rows = r._make_table()
    assert header == ["a", "c"]
    assert rows == [{"a": 1, "b": 2, "c": 3}]


def test_make_table_rejects_scalar():
    with pytest.raises(ValueError):
        Result(42)._make_table()


def test_print_csv():
    r = Result([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    r.console = Console(file=StringIO(), width=200)
    r.print("csv")
    out = r.console.file.getvalue()  # type: ignore
    assert "a,b" in out
    assert "1,2" in out
    assert "3,4" in out


def test_print_tsv():
    r = Result([{"a": 1, "b": 2}])
    r.console = Console(file=StringIO(), width=200)
    r.print("tsv")
    out = r.console.file.getvalue()  # type: ignore
    # rich's Console expands tabs to spaces on render, so match on content.
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert lines[0].split() == ["a", "b"]
    assert lines[1].split() == ["1", "2"]


def test_noop_selector_returns_body():
    result = noop_selector(pretty=True)(FakeResponse({"x": 1}))
    assert isinstance(result, Result)
    assert result.value == {"x": 1}


def test_jsonpath_selector_single_match_unwrapped():
    result = jsonpath_selector("jsonpath=$.version.number", pretty=True)(
        FakeResponse({"version": {"number": "8.13.0"}})
    )
    assert result.value == "8.13.0"


def test_jsonpath_selector_multiple_matches_list():
    result = jsonpath_selector("jsonpath=$.items[*].id", pretty=True)(
        FakeResponse({"items": [{"id": 1}, {"id": 2}]})
    )
    assert result.value == [1, 2]


def test_jmespath_selector():
    result = jmespath_selector("jmespath=version.number", pretty=True)(
        FakeResponse({"version": {"number": "9.0.1"}})
    )
    assert result.value == "9.0.1"
