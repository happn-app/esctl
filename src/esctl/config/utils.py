import functools

import typer


@functools.lru_cache()
def get_root_ctx(ctx: typer.Context) -> typer.Context:
    contexts = [ctx]
    while contexts[-1].parent is not None:  # Find the root context
        contexts.append(contexts[-1].parent)  # type: ignore
    for c in contexts:
        if "context" in c.params:
            return c
    raise ValueError("No root context found")
