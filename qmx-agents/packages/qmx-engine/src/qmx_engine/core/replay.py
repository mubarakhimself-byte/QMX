"""Node-level replay (AD-7): a ready node with a valid memo settles from it, and only a node without
one starts.

The memo key is `(run_id, node_id, iteration, partition_id, sha256(inputs),
sha256(node_definition))`, the same fingerprint `qmx_engine.ledger.memo.MemoKey` stores. A node
reruns only when its own inputs or its own definition changed, so an edited node invalidates its
memo and a downstream node reruns only if the edit changed what reached it. Each fan-out partition
and each loop iteration is its own slot with its own memo, so a failed chunk reruns alone.
"""

from __future__ import annotations

from pydantic import JsonValue
from qmx_ledger.journal import fingerprint

from qmx_engine.core.commands import StartNode, UseMemo
from qmx_engine.core.ladder import asks
from qmx_engine.core.state import JsonObject, Ready, Slot, State
from qmx_engine.definition.model import Node


def node_definition(node: Node) -> JsonObject:
    """The slice that keys a node's memo. `position` is left out, so moving a node reruns
    nothing, and so is an unset `limits`, so a node keeps the key it had before limits existed."""
    unset = {"limits"} if node.limits is None else set[str]()
    return node.model_dump(mode="json", by_alias=True, exclude={"position", *unset})


def memo_key(
    run_id: str,
    node_id: str,
    iteration: int,
    partition: int | None,
    inputs: JsonValue,
    definition: JsonObject,
) -> str:
    partition_id = "" if partition is None else str(partition)
    return fingerprint(
        [run_id, node_id, iteration, partition_id, fingerprint(inputs), fingerprint(definition)]
    )


def idempotency_key(run_id: str, slot: Slot, attempt: int) -> str:
    """`run:node:iteration:attempt` (SOLUTION-DESIGN 3.4), with the partition before the attempt
    when the node fanned out, so two chunks never share a key."""
    node_id, iteration, partition = slot
    where = f"{iteration}" if partition is None else f"{iteration}:{partition}"
    return f"{run_id}:{node_id}:{where}:{attempt}"


def dispatch(state: State, ready: list[Ready]) -> list[StartNode | UseMemo]:
    commands: list[StartNode | UseMemo] = []
    for item in ready:
        slot = Slot(item.node.id, item.iteration, item.partition)
        definition = node_definition(item.node)
        key = memo_key(state.run_id, *slot, item.inputs, definition)
        saved = state.memos.get(key)
        if saved is not None:
            commands.append(UseMemo(*slot, key, saved))
            continue
        attempt = state.attempts.get(slot, 0) + 1
        commands.append(
            StartNode(
                run_id=state.run_id,
                node_id=slot.node_id,
                iteration=slot.iteration,
                partition=slot.partition,
                attempt=attempt,
                memo_key=key,
                idempotency_key=idempotency_key(state.run_id, slot, attempt),
                node_definition=definition,
                inputs=item.inputs,
                now=state.now,
                plan=item.plan,
                ladder=asks(state, item.node, slot),
            )
        )
    return commands
