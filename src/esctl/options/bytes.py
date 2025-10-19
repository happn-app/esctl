from enum import Enum
from typing import Annotated

import typer


class ByteUnit(str, Enum):
    b = "b"
    kb = "kb"
    mb = "mb"
    gb = "gb"
    tb = "tb"
    pb = "pb"


BytesOption = Annotated[
    ByteUnit,
    typer.Option(
        "--bytes",
        "-b",
        help="Unit used to display byte values",
    ),
]
