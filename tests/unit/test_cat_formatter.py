from esctl.commands.cat.aliases import formatter


def test_status_wraps_in_color_markup():
    assert formatter("status", "green") == "[b green]GREEN[/]"
    assert formatter("status", "RED") == "[b red]RED[/]"


def test_active_shards_percent_thresholds():
    assert formatter("active_shards_percent_as_number", "10") == "[b red]10%[/]"
    assert formatter("active_shards_percent_as_number", "60") == "[b yellow]60%[/]"
    assert formatter("active_shards_percent_as_number", "75") == "[b green]75%[/]"
    assert formatter("active_shards_percent_as_number", "100") == "[b green]100%[/]"


def test_unassigned_shards():
    assert formatter("unassigned_shards", "0") == "[b green]0%[/]"
    assert formatter("unassigned_shards", "3") == "[b red]3%[/]"


def test_initializing_and_relocating_shards():
    assert formatter("initializing_shards", "0") == "[b green]0[/]"
    assert formatter("initializing_shards", "2") == "[b yellow]2[/]"
    assert formatter("relocating_shards", "0") == "[b green]0[/]"
    assert formatter("relocating_shards", "1") == "[b yellow]1[/]"


def test_task_max_waiting_millis_to_seconds():
    assert formatter("task_max_waiting_in_queue_millis", "1500") == "1.50s"


def test_unknown_column_passthrough():
    assert formatter("some.other.column", "value") == "value"
