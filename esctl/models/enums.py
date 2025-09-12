from enum import Enum


class ColumnNames(str, Enum):
    cluster = "cluster"
    status = "status"
    node_total = "node.total"
    node_data = "node.data"
    shards = "shards"
    pri = "pri"
    relo = "relo"
    init = "init"
    unassign = "unassign"
    unassign_pri = "unassign.pri"
    pending_tasks = "pending_tasks"
    max_task_wait_time = "max_task_wait_time"
    active_shards_percent = "active_shards_percent"


class TimeUnit(str, Enum):
    days = "d"
    hours = "h"
    minutes = "m"
    seconds = "s"
    milliseconds = "ms"
    microseconds = "micros"
    nanoseconds = "nanos"


class Format(str, Enum):
    text = "text"
    json = "json"
    yaml = "yaml"
    smile = "smile"
    cbor = "cbor"


class ByteUnit(str, Enum):
    b = "b"
    kb = "kb"
    mb = "mb"
    gb = "gb"
    tb = "tb"
    pb = "pb"


class SizeUnit(str, Enum):
    k = "k"
    m = "m"
    g = "g"
    t = "t"
    p = "p"


class Conflict(str, Enum):
    abort = "abort"
    proceed = "proceed"


class Shell(str, Enum):
    bash = "bash"
    zsh = "zsh"
    fish = "fish"
    powershell = "powershell"
