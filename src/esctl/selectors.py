from collections.abc import Iterable
from typing import Any

import elastic_transport
import typer
from yamlpath import Processor, YAMLPath
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers.nodecoords import NodeCoords


def select_from_context(ctx: typer.Context, value: Any) -> Any:
    contexts = [ctx]
    while contexts[-1].parent is not None:  # Find the root context
        contexts.append(contexts[-1].parent)  # type: ignore
    root_ctx = contexts[-2]
    if root_ctx.obj["jmespath"] is not None:
        return root_ctx.obj["jmespath"].search(value.body)
    if root_ctx.obj["jsonpath"] is not None:
        value = root_ctx.obj["jsonpath"].find(value.body)
        if isinstance(value, Iterable):
            value = [match.value for match in value]
            if len(value) == 1:
                return value[0]
            return value
        else:
            return value.value
    if root_ctx.obj["yamlpath"] is not None:
        yamlpath: YAMLPath = root_ctx.obj["yamlpath"]
        if isinstance(value, elastic_transport.ListApiResponse):
            value = list(value.body)
        else:
            value = dict(value)

        processor = Processor(root_ctx.obj["logger"], data=value)
        try:
            for node_coordinate in processor.get_nodes(yamlpath, mustexist=True):
                assert isinstance(node_coordinate, NodeCoords)
                return node_coordinate.node
        except YAMLPathException as ex:
            # If merely retrieving data, this exception may be deemed non-critical
            # unless your later code absolutely depends upon a result.
            root_ctx.obj["logger"].error(ex)
            return ""
    return value.raw
