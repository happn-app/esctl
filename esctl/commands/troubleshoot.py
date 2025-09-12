from typing import Any
from rich import print
from rich.prompt import Confirm
from rich.table import Table
import typer

from esctl.config import get_client_from_ctx


app = typer.Typer(rich_markup_mode="rich")

@app.callback(
    help="Troubleshoot common issues with elasticsearch.",
    invoke_without_command=True,
)
def troubleshoot(
    ctx: typer.Context,
):
    client = get_client_from_ctx(ctx)
    health = client.cluster.health().raw
    health_emoji = {"green": "✅", "yellow": "⚠️", "red": "❌"}.get(health["status"], "❓")
    print(f"{health_emoji} -- Cluster health: [b {health['status']}]{health['status']}[/]")
    if health["status"] == "green":
        typer.Exit(code=0)

    # Which shards on which indices are unassigned?
    shards = client.cat.shards(
        format="json",
        h=["index","shard","prirep","state","unassigned.reason"]
    ).raw
    unassigned_shards: list[dict[str, Any]] = [s for s in shards if s["state"] == "UNASSIGNED"] # type: ignore
    initializing_shards = [s for s in shards if s["state"] == "INITIALIZING"] # type: ignore
    relocating_shards = [s for s in shards if s["state"] == "RELOCATING"] # type: ignore
    if initializing_shards:
        print(f"⚠️ -- {len(initializing_shards)} initializing shards:")
        table = Table("index", "shard", "prirep", "state")
        for shard in initializing_shards:
            table.add_row(shard["index"], shard["shard"], shard["prirep"], shard["state"]) # type: ignore
        print(table)
    if relocating_shards:
        print(f"⚠️ -- {len(relocating_shards)} relocating shards:")
        table = Table("index", "shard", "prirep", "state")
        for shard in relocating_shards:
            table.add_row(shard["index"], shard["shard"], shard["prirep"], shard["state"]) # type: ignore
        print(table)
    if not unassigned_shards:
        print("✅ -- No unassigned shards, cluster is going to recover eventually.")
        typer.Exit(code=0)
    if unassigned_shards:
        print(f"❌ -- {len(unassigned_shards)} unassigned shards:")
        table = Table("index", "shard", "prirep", "unassigned.reason")
        for shard in unassigned_shards:
            table.add_row(
                shard["index"],
                shard["shard"],
                shard["prirep"],
                shard.get("unassigned.reason", "N/A"),
            )
        print(table)
    # Check that the shard's index still exists, and that it's not a "system" index, denoted by a leading dot
    indices = client.cat.indices(format="json", h=["index"]).raw
    existing_indices = {idx["index"] for idx in indices} # type: ignore
    unassigned_absent_indices = {shard["index"] for shard in unassigned_shards if shard["index"] not in existing_indices} # type: ignore
    if unassigned_absent_indices:
        print(f"❌ -- The following indices with unassigned shards do not exist: {', '.join(unassigned_absent_indices)}")
        print("    If these indices were recently deleted, the unassigned shards will eventually be cleaned up by Elasticsearch.")
        print("    If these indices were not recently deleted, you may need to restore them from a snapshot or backup.")
        typer.Exit(code=1)
    system_indices = {shard["index"] for shard in unassigned_shards if shard["index"].startswith(".")} # type: ignore
    if system_indices:
        print(f"❌ -- The following system indices with unassigned shards exist: {', '.join(system_indices)}")
        print("    System indices are managed by Elasticsearch and should not be deleted or modified manually.")

        should_reroute = Confirm.ask(
            "Do you want to attempt to reroute the unassigned shards for these system indices? This may resolve the issue if the shards can be allocated to other nodes.", default=True
        )
        if should_reroute:
            client.cluster.reroute(explain=True, retry_failed=True)

    # There are unassigned shards, need to use the cluster allocation explain API to understand why
    for shard in unassigned_shards:
        index = shard["index"]
        print(f"❌ -- Explanation for unallocated shard {shard["shard"]} ([b]{shard["prirep"]}[/]) detected on index: {index}")
        explanation = client.cluster.allocation_explain(index=index, shard=shard["shard"], primary=shard["prirep"] == "p").raw
        print(f"    {explanation["allocate_explanation"]}")
        all_deciders = set()
        for decision in explanation.get("node_allocation_decisions", []):
            print(f"    [b]Node:[/b] {decision['node_name']}")
            for dec in decision.get("deciders", []):
                decision_emoji = {"YES": "✅", "NO": "❌", "THROTTLE": "⚠️"}.get(dec["decision"], "❓")
                print(f"      - {decision_emoji} {dec['decider']}: {dec['explanation']}")
                all_deciders.add(dec["decider"])
        print()
        # If all shards are unassigned because of the decider "same_shard" it means that number of nodes < number of shards
        if all_deciders == {"same_shard"}:
            print("❌ -- All unassigned shards are due to the 'same_shard' decider.")
            print("    This usually means that the number of nodes in the cluster is less than the number of shards for the affected indices.")
            print("    Consider adding more nodes to the cluster or reducing the number of primary shards on the affected indices.")
            typer.Exit(code=1)
