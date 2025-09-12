import re
from typing import Annotated, TypedDict
from elasticsearch import BadRequestError
import typer

from esctl.config import get_client_from_ctx
from esctl.models.enums import Format
from esctl.output import pretty_print
from esctl.selectors import select_from_context


from .cache import app as cache_app
from .settings import app as settings_app

app = typer.Typer(rich_markup_mode="rich")


app.add_typer(cache_app)
app.add_typer(settings_app)

supported_field_types = [
    "text",
    "binary",
    "boolean",
    "long",
    "double",
    "date",
    "keyword",
    "constant_keyword",
    "wildcard",
]
mappings_re = re.compile(f'^(?P<name>[a-z_]+?):(?P<type>{"|".join(supported_field_types)})$')


class Mapping(TypedDict):
    type: str


def mappings_callback(value: str) -> dict[str, dict[str, Mapping]]:
    if not value:
        return {}
    mappings = value.split(",")
    parsed = {}
    for mapping in mappings:
        match = mappings_re.search(mapping)
        if not match:
            raise typer.BadParameter((
                f"Mapping '{mapping}' is not valid. It should be in the form 'field_name:field_type'. "
                f"Supported field types are {', '.join(supported_field_types)}"
            ))
        name = match.group("name")
        type = match.group("type")
        parsed[name] = {"type": type}
    return {"properties": parsed}


def index_callback(value: str) -> str:
    """
    Validate index name according to https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-indices-create#operation-indices-create-index
    """
    if value == '.' or value == '..':
        raise typer.BadParameter("Index name cannot be '.' or '..'")
    if value.startswith('-') or value.startswith('_') or value.startswith('+'):
        raise typer.BadParameter(
            f"Index name '{value}' is not valid. It should not start with '-', '_' or '+'."
        )
    if value.startswith('.'):
        raise typer.BadParameter(
            f"Index name '{value}' is not valid. It should not start with a dot ('.')."
        )
    # \, /, *, ?, ", <, >, |
    disallowed_chars = ['\\', '/', '*', '?', '"', '<', '>', '|', ' ', ',', ':', '#']
    if any(char in value for char in disallowed_chars):
        raise typer.BadParameter(
            f"Index name '{value}' is not valid. It should not contain any of {", ".join(disallowed_chars)}."
        )
    encoded = value.encode('utf-8')
    if len(encoded) > 255:
        raise typer.BadParameter(
            f"Index name '{value}' is too long. It should be less than 255 bytes."
        )
    return value


@app.command(
    help="Creates an index in a cluster.",
)
def create(
    ctx: typer.Context,
    index: Annotated[str, typer.Argument(callback=index_callback)],
    mappings: Annotated[str, typer.Argument(callback=mappings_callback, case_sensitive=True)],
    aliases: list[str] | None = None,
    number_of_shards: int = 1,
    number_of_replicas: int = 1,
):
    client = get_client_from_ctx(ctx)
    try:
        response = client.indices.create(
            index=index,
            aliases={alias: {} for alias in aliases} if aliases else None,
            settings={
                "number_of_shards": number_of_shards,
                "number_of_replicas": number_of_replicas,
            },
            mappings=mappings,  # type: ignore
        )
        response = select_from_context(ctx, response)
        pretty_print(response, format=Format.json)
    except BadRequestError as e:
        typer.secho(f"Error creating index: {e.info['error']['reason']}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
