from typing import Optional
import typer
from typing_extensions import Annotated

from esctl.completions import (
    complete_column,
    complete_context,
    complete_index,
    complete_node,
    complete_parent_task_id,
    complete_settings_key,
    complete_shard,
    complete_snapshot_indices,
    complete_sort,
    complete_task_id,
    complete_repository,
    complete_snapshot_name,
)
from esctl.models.enums import ByteUnit, Format, TimeUnit

IncludeUnloadedSegmentsOption = Annotated[
    bool,
    typer.Option(
        "--include-unloaded-segments",
        help="If true, the response includes information from segments that are not loaded into memory. Defaults to false. ",
    )
]
TimestampOption = Annotated[
    bool,
    typer.Option(
        "--no-timestamp",
        "--no-ts",
        is_flag=True,
        flag_value=False,
        help="If true, returns HH:MM:SS and Unix epoch timestamps. Defaults to true.",
    )
]
FormatOption = Annotated[
    Format,
    typer.Option(
        "--format",
        "-f",
        help="Format of the response",
    ),
]
TimeOption = Annotated[
    TimeUnit,
    typer.Option(
        "--time",
        "-t",
        help="Time unit to use in the response",
    ),
]
SortOption = Annotated[
    list[str],
    typer.Option(
        "--sort",
        "-s",
        autocompletion=complete_sort,
        help="How to sort the response",
    ),
]
HeaderOption = Annotated[
    list[str],
    typer.Option(
        "--header",
        "-h",
        autocompletion=complete_column,
        help="Headers to include in the response",
    ),
]
BytesOption = Annotated[
    ByteUnit,
    typer.Option(
        "--bytes",
        "-b",
        help="Unit used to display byte values",
    ),
]
LocalOnlyOption = Annotated[
    bool,
    typer.Option(
        help="If true, the request retrieves information from the local node only. Defaults to false, which means information is retrieved from the master node.",
    ),
]
FullIdOption = Annotated[
    bool,
    typer.Option(
        help="If true, the node ID is displayed in full. Defaults to false, which means the node ID is displayed in short form.",
    ),
]
DetailedOption = Annotated[
    bool,
    typer.Option(
        help="If true, the response includes detailed information about shard recovery. Defaults to false.",
    ),
]
IndexOption = Annotated[
    list[str],
    typer.Option(
        "--index",
        "-i",
        autocompletion=complete_index,
        help="The index to use",
    ),
]
ActiveOnlyOption = Annotated[
    bool,
    typer.Option(
        help="If true, the response includes only ongoing recoveries. Defaults to false.",
    ),
]
RerouteDryRunOption = Annotated[
    bool,
    typer.Option(
        help="If true, then the request simulates the operation only and returns the resulting state.",
    ),
]
RerouteExplainOption = Annotated[
    bool,
    typer.Option(
        help="If true, then the response contains an explanation of why the commands can or cannot be executed. ",
    ),
]
RerouteRetryFailedOption = Annotated[
    bool,
    typer.Option(
        help="If true, then retries allocation of shards that are blocked due to too many subsequent allocation failures. ",
    ),
]
ExplainIncludeDiskInfoOption = Annotated[
    bool,
    typer.Option(
        "--include-disk-info",
        "--disk-info",
        "-d",
        help="Returns information about disk usage and shard sizes.",
    ),
]
ExplainIncludeYesDecisionsOption = Annotated[
    bool,
    typer.Option(
        "--include-yes-decisions",
        "--yes-decisions",
        "-y",
        help="Returns YES decisions in explanation.",
    ),
]
ShardOption = Annotated[
    int,
    typer.Option(
        "--shard",
        "-s",
        autocompletion=complete_shard,
        help="The shard ID to use",
    ),
]
ExplainPrimaryShardOption = Annotated[
    bool,
    typer.Option(
        "--primary",
        "-p",
        help="Returns explanation for the primary shard for the given shard ID",
    ),
]
NodeOption = Annotated[
    str,
    typer.Option(
        "--node",
        "-n",
        autocompletion=complete_node,
        help="The node name to use.",
    ),
]
SettingsTransientOption = Annotated[
    bool,
    typer.Option(
        "--transient",
        help="If true, the request sets the transient settings. Defaults to false, which means the request sets the persistent settings.",
    ),
]

SettingsKeyArgument = Annotated[
    str,
    typer.Argument(
        help="The elasticsearch setting to update.",
        autocompletion=complete_settings_key,
    ),
]

SettingsValueArgument = Annotated[
    str,
    typer.Argument(
        help="The value to set the setting to.",
    ),
]
ContextOption = Annotated[
    str,
    typer.Option(
        "--context",
        "-c",
        autocompletion=complete_context,
        help="Elasticsearch cluster to use",
        envvar="ESCTL_CONTEXT",
    ),
]
VerboseOption = Annotated[
    int,
    typer.Option(
        "--verbose",
        "-v",
        count=True,
        min=0,
        max=4,
        help="Increase verbosity level",
    ),
]
JSONPathOption = Annotated[
    str,
    typer.Option(
        help="JSONPath expression to filter the response, implies --format=json",
    ),
]
JMESPathOption = Annotated[
    str,
    typer.Option(
        help="JMESPath expression to filter the response, implies --format=json",
    ),
]
YAMLPathOption = Annotated[
    str,
    typer.Option(
        help="YAMLPath expression to filter the response, implies --format=yaml",
    ),
]
PrettyOption = Annotated[
    bool,
    typer.Option(
        help="Pretty print the output",
    ),
]

IndexArgument = Annotated[
    str,
    typer.Argument(
        autocompletion=complete_index,
        help="The index to use",
    ),
]

ParentTaskIdOption = Annotated[
    str,
    typer.Option(
        "--parent-task-id",
        help="The parent task ID to filter tasks by",
        autocompletion=complete_parent_task_id,
    ),
]

TaskIdArgument = Annotated[
    str,
    typer.Argument(
        help="The task ID to use",
        autocompletion=complete_task_id,
    ),
]

SliceOption = Annotated[
    int,
    typer.Option(
        "--slices",
        "-s",
        help="The number of slices to use for the reindexing operation. Defaults to 'auto'.",
    ),
]

RestoreSnapshotRepositoryArgument = Annotated[
    str,
    typer.Argument(
        help="The name of the repository to restore the snapshot from",
        autocompletion=complete_repository,
    ),
]


RestoreSnapshotNameArgument = Annotated[
    str | None,
    typer.Argument(
        help="The name of the snapshot to restore",
        autocompletion=complete_snapshot_name,
    ),
]

RestoreSnapshotIndexOption = Annotated[
    Optional[list[str]],
    typer.Option(
        "--index",
        "-i",
        help="The index to restore from the snapshot",
        autocompletion=complete_snapshot_indices,
    ),
]
