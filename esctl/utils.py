from string import Formatter
from datetime import timedelta
from typing import Any

import typer

from esctl.models.enums import Format


def get_root_ctx(ctx: typer.Context) -> typer.Context:
    contexts = [ctx]
    while contexts[-1].parent is not None:  # Find the root context
        contexts.append(contexts[-1].parent)  # type: ignore
    for c in contexts:
        if "context" in c.params:
            return c
    raise ValueError("No root context found")


def get_cat_base_params_from_context(
    ctx: typer.Context, format: Format
) -> dict[str, Any]:
    ctx = get_root_ctx(ctx)
    has_json_select = (
        ctx.params.get("jsonpath") is not None or ctx.params.get("jmespath") is not None
    )
    has_yaml_select = ctx.params.get("yamlpath") is not None
    pretty = ctx.params.get("pretty", True)
    if has_json_select:
        format = Format.json
    if has_yaml_select:
        format = Format.yaml
    return {
        "format": format,
        "pretty": True,
        "v": format == Format.text and not has_json_select and pretty,
    }


def strfdelta(tdelta: timedelta):
    """Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    The fmt argument allows custom formatting to be specified.  Fields can
    include seconds, minutes, hours, days, and weeks.  Each field is optional.

    Some examples:
        '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s' (default)
        '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
        '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
        '{H}h {S}s'                       --> '72h 800s'

    The inputtype argument allows tdelta to be a regular number instead of the
    default, which is a datetime.timedelta object.  Valid inputtype strings:
        's', 'seconds',
        'm', 'minutes',
        'h', 'hours',
        'd', 'days',
        'w', 'weeks'
    """

    remainder = int(tdelta.total_seconds())
    fmt='{M:02}m{S:02}s'
    # Convert tdelta to integer seconds.

    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ('W', 'D', 'H', 'M', 'S')
    constants = {'W': 604800, 'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)
