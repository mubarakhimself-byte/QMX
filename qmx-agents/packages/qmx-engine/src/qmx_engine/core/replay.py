"""Node-level replay (AD-7): a ready node with a valid memo settles from it, and only a node without
one starts.

The memo key is `(run_id, node_id, iteration, partition_id, sha256(inputs),
sha256(node_definition))`, the same fingerprint `qmx_engine.ledger.memo.MemoKey` stores. A node
reruns only when its own inputs or its own definition changed, so an edited node invalidates its
memo and a downstream node reruns only if the edit changed what reached it.
"""

from __future__ import annotations

from pydantic import JsonValue
from qmx_ledger.journal import fingerprint

from qmx_engine.core.commands import StartNode, UseMemo
from qmx_engine.core.state import JsonObject, Ready, State
from qmx_engine.definition.model import Node

ITERATION = 0
PARTITION: int | None = None
"""Every node runs once per pass on a `one` edge; loops and fan-out arrive in EP6."""


def node_definition(node: Node) -> JsonObject:
    """The slice that keys a node's memo. `position` is left out, so moving a node reruns
    nothing."""
    return node.model_dump(mode="json", by_alias=True, exclude={"position"})


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


def dispatch(state: State, ready: list[Ready]) -> list[StartNode | UseMemo]:
    commands: list[StartNode | UseMemo] = []
    for item in ready:
        node_id = item.node.id
        definition = node_definition(item.node)
        key = memo_key(state.run_id, node_id, ITERATION, PARTITION, item.inputs, definition)
        saved = state.memos.get(key)
        if saved is not None:
            commands.append(UseMemo(node_id, ITERATION, PARTITION, key, saved))
            continue
        attempt = state.attempts.get(node_id, 0) + 1
        commands.append(
            StartNode(
                run_id=state.run_id,
                node_id=node_id,
                iteration=ITERATION,
                partition=PARTITION,
                attempt=attempt,
                memo_key=key,
                idempotency_key=f"{state.run_id}:{node_id}:{ITERATION}:{attempt}",
                node_definition=definition,
                inputs=item.inputs,
                now=state.now,
            )
        )
    return commands
