import re
from typing import Annotated, TypedDict
import elasticsearch8
import elasticsearch9
import typer

from esctl.config import Config
from esctl.options.output import OutputOption, Result


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
mappings_re = re.compile(
    f"^(?P<name>[a-z_]+?):(?P<type>{'|'.join(supported_field_types)})$"
)


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
            raise typer.BadParameter(
                (
                    f"Mapping '{mapping}' is not valid. It should be in the form 'field_name:field_type'. "
                    f"Supported field types are {', '.join(supported_field_types)}"
                )
            )
        name = match.group("name")
        type = match.group("type")
        parsed[name] = {"type": type}
    return {"properties": parsed}


def index_callback(value: str) -> str:
    """
    Validate index name according to https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-indices-create#operation-indices-create-index
    """
    if value == "." or value == "..":
        raise typer.BadParameter("Index name cannot be '.' or '..'")
    if value.startswith("-") or value.startswith("_") or value.startswith("+"):
        raise typer.BadParameter(
            f"Index name '{value}' is not valid. It should not start with '-', '_' or '+'."
        )
    if value.startswith("."):
        raise typer.BadParameter(
            f"Index name '{value}' is not valid. It should not start with a dot ('.')."
        )
    # \, /, *, ?, ", <, >, |
    disallowed_chars = ["\\", "/", "*", "?", '"', "<", ">", "|", " ", ",", ":", "#"]
    if any(char in value for char in disallowed_chars):
        raise typer.BadParameter(
            f"Index name '{value}' is not valid. It should not contain any of {', '.join(disallowed_chars)}."
        )
    encoded = value.encode("utf-8")
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
    index: Annotated[
        str,
        typer.Argument(
            help="Name of the index to create",
            callback=index_callback,
        ),
    ],
    mappings: Annotated[
        str,
        typer.Argument(
            help="Mappings for the index in the form 'field_name:field_type,another_field:field_type'",
            callback=mappings_callback,
            case_sensitive=True,
        ),
    ],
    aliases: Annotated[
        list[str] | None,
        typer.Option(
            help="Aliases to add for this index",
        ),
    ] = None,
    number_of_shards: Annotated[
        int,
        typer.Option(
            help="Number of primary shards for this index",
            min=1,
        ),
    ] = 1,
    number_of_replicas: Annotated[
        int,
        typer.Option(
            help="Number of replica shards for this index",
            min=1,
        ),
    ] = 1,
    output: OutputOption = "json",
):
    client = Config.from_context(ctx).client
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
        result: Result = ctx.obj["selector"](response)
        result.print(output)
    except (elasticsearch8.BadRequestError, elasticsearch9.BadRequestError) as e:
        typer.secho(
            f"Error creating index: {e.info['error']['reason']}", fg=typer.colors.RED
        )
        raise typer.Exit(code=1) from e
