"""Saved node results under the AD-7 key.

A memo is keyed by `(run_id, node_id, iteration, partition, sha256(inputs),
sha256(node_definition))`, hashed with `qmx_ledger.journal.fingerprint` so two processes agree on
it. Writes go through the ledger's writer; `has` and `outputs` read through a `Reader`. Outputs
are stored redacted (AD-37), the same text the node's committed event holds.

The ledger events decide whether a memo is valid (AD-7, B-19): a `node_finished` with its input and
definition hashes stands until a later recorded event voids it, and the core reads only those. This
table is an index derived from them, so it keeps no validity of its own that anything reads.
"""

from __future__ import annotations

import json
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
    partition: str
    inputs_hash: str
    definition_hash: str

    @classmethod
    def of(
        cls,
        run_id: str,
        node_id: str,
        iteration: int,
        partition: str,
        inputs: JsonValue,
        node_definition: JsonValue,
    ) -> MemoKey:
        return cls(
            run_id,
            node_id,
            iteration,
            partition,
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
                self.partition,
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
                key.partition,
                key.inputs_hash,
                key.definition_hash,
                text,
            ),
        )

    ledger.write(operation)


def has(reader: Reader, key: MemoKey) -> bool:
    row = reader.connection.execute(
        "SELECT 1 FROM memos WHERE fingerprint = ?", (key.fingerprint,)
    ).fetchone()
    return row is not None


def outputs(reader: Reader, key: MemoKey) -> JsonValue:
    """The saved outputs under the key; `LookupError` when there are none."""
    row = reader.connection.execute(
        "SELECT outputs FROM memos WHERE fingerprint = ?", (key.fingerprint,)
    ).fetchone()
    if row is None:
        raise LookupError("no memo for this key")
    return json.loads(row[0])
