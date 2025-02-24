from typing import Any

import typer

from esctl.models.enums import Format


def get_root_ctx(ctx: typer.Context) -> typer.Context:
    contexts = [ctx]
    while contexts[-1].parent is not None:  # Find the root context
        contexts.append(contexts[-1].parent)
    for c in contexts:
        if "context" in c.params:
            return c


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
