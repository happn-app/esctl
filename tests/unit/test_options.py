import pytest

from esctl.options.time import TimeUnit
from esctl.options.bytes import ByteUnit


@pytest.mark.parametrize(
    "name,value",
    [
        ("days", "d"),
        ("hours", "h"),
        ("minutes", "m"),
        ("seconds", "s"),
        ("milliseconds", "ms"),
        ("microseconds", "micros"),
        ("nanoseconds", "nanos"),
    ],
)
def test_time_unit_values(name, value):
    assert TimeUnit[name].value == value
    # str-Enum: the member compares/serializes as its string value.
    assert TimeUnit(value) == value


@pytest.mark.parametrize("value", ["b", "kb", "mb", "gb", "tb", "pb"])
def test_byte_unit_values(value):
    assert ByteUnit(value).value == value


def test_invalid_time_unit():
    with pytest.raises(ValueError):
        TimeUnit("weeks")


def test_invalid_byte_unit():
    with pytest.raises(ValueError):
        ByteUnit("zb")
