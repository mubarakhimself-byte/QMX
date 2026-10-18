"""Saved node results under the AD-7 key.

A memo is keyed by `(run_id, node_id, iteration, partition_id, sha256(inputs),
sha256(node_definition))`, hashed with `qmx_ledger.journal.fingerprint` so two processes agree on
it. Writes go through the ledger's writer; `has`, `valid` and `outputs` read through a `Reader`. A
memo stays stored after it is invalidated, so `has` still finds it and `valid` does not. Outputs
are stored redacted (AD-37), the same text the node's committed event holds.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from pydantic import JsonValue
from qmx_ledger.journal import encoded, fingerprint

from qmx_engine.ledger.redact import redact_json
from qmx_engine.ledger.store import Ledger, Reader, Transaction


@dataclass(frozen=True, slots=True)
class MemoKey:
    run_id: str
    node_id: str
    iteration: int
    partition_id: str
    inputs_hash: str
    definition_hash: str

    @classmethod
    def of(
        cls,
        run_id: str,
        node_id: str,
        iteration: int,
        partition_id: str,
        inputs: JsonValue,
        node_definition: JsonValue,
    ) -> MemoKey:
        return cls(
            run_id,
            node_id,
            iteration,
            partition_id,
            fingerprint(inputs),
            fingerprint(node_definition),
        )

    @property
    def fingerprint(self) -> str:
        return fingerprint(
            [
                self.run_id,
                self.node_id,
                self.iteration,
                self.partition_id,
                self.inputs_hash,
                self.definition_hash,
            ]
        )


def record(ledger: Ledger, key: MemoKey, outputs: JsonValue) -> None:
    text = encoded(redact_json(outputs)[0]).decode()

    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            "INSERT OR REPLACE INTO memos (fingerprint, run_id, node_id, iteration, partition_id,"
            " inputs_hash, definition_hash, outputs, valid) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (
                key.fingerprint,
                key.run_id,
                key.node_id,
                key.iteration,
                key.partition_id,
                key.inputs_hash,
                key.definition_hash,
                text,
            ),
        )

    ledger.write(operation)


def _valid_flag(reader: Reader, key: MemoKey) -> int | None:
    row = reader.connection.execute(
        "SELECT valid FROM memos WHERE fingerprint = ?", (key.fingerprint,)
    ).fetchone()
    return None if row is None else int(row[0])


def has(reader: Reader, key: MemoKey) -> bool:
    return _valid_flag(reader, key) is not None


def valid(reader: Reader, key: MemoKey) -> bool:
    return _valid_flag(reader, key) == 1


def outputs(reader: Reader, key: MemoKey) -> JsonValue:
    """The saved outputs of a valid memo; `LookupError` when there is none."""
    row = reader.connection.execute(
        "SELECT outputs FROM memos WHERE fingerprint = ? AND valid = 1", (key.fingerprint,)
    ).fetchone()
    if row is None:
        raise LookupError("no valid memo for this key")
    return json.loads(row[0])


def invalidate_by_definition(
    ledger: Ledger, run_id: str, definitions: Mapping[str, JsonValue]
) -> int:
    """Invalidate every memo of `run_id` whose node is in `definitions` (node id to its current
    definition) under another definition hash, and return how many changed. Nodes not named are
    left alone."""
    hashes = {node_id: fingerprint(definition) for node_id, definition in definitions.items()}

    def operation(txn: Transaction) -> int:
        changed = 0
        for node_id, definition_hash in hashes.items():
            changed += txn.connection.execute(
                "UPDATE memos SET valid = 0 WHERE run_id = ? AND node_id = ?"
                " AND definition_hash != ? AND valid = 1",
                (run_id, node_id, definition_hash),
            ).rowcount
        return changed

    return ledger.write(operation)
