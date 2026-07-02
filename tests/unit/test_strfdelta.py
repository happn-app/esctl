from datetime import timedelta

from esctl.utils import strfdelta


def test_zero():
    assert strfdelta(timedelta(0)) == "00m00s"


def test_seconds_only():
    assert strfdelta(timedelta(seconds=5)) == "00m05s"


def test_minutes_and_seconds():
    assert strfdelta(timedelta(minutes=4, seconds=2)) == "04m02s"


def test_hours_fold_into_minutes():
    # The format is fixed to "{M:02}m{S:02}s", so hours/days fold into minutes.
    assert strfdelta(timedelta(hours=1, seconds=30)) == "60m30s"


def test_multi_day_folds_into_minutes():
    # 1 day = 1440 minutes; days are not a field in the format string.
    assert strfdelta(timedelta(days=1, minutes=1, seconds=1)) == "1441m01s"


def test_fractional_seconds_truncated():
    # total_seconds() is cast to int, dropping the fractional part.
    assert strfdelta(timedelta(seconds=9, milliseconds=999)) == "00m09s"
