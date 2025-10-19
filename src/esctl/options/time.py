from enum import Enum
from typing import Annotated

import typer


class TimeUnit(str, Enum):
    days = "d"
    hours = "h"
    minutes = "m"
    seconds = "s"
    milliseconds = "ms"
    microseconds = "micros"
    nanoseconds = "nanos"


TimeOption = Annotated[
    TimeUnit,
    typer.Option(
        "--time",
        "-t",
        help="Time unit to use in the response",
    ),
]
