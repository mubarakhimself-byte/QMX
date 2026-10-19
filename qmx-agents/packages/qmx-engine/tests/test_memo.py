from __future__ import annotations

from pathlib import Path

from qmx_engine.ledger import memo
from qmx_engine.ledger.events import JsonObject
from qmx_engine.ledger.memo import MemoKey
from qmx_engine.ledger.store import Ledger, Reader

TRIAGE: JsonObject = {"type": "llm", "parameters": {"prompt_ref": "prompts/triage.md"}}


def test_b19_the_memo_table_is_an_index_and_keeps_no_validity_flag(tmp_path: Path) -> None:
    key = MemoKey.of("run", "triage", 0, "1", {"chunk": 1}, TRIAGE)
    other = MemoKey.of("run", "triage", 0, "2", {"chunk": 2}, TRIAGE)
    with Ledger.open(tmp_path) as ledger:
        memo.record(ledger, key, {"main": ["card"]})

    with Reader.open(tmp_path) as reader:
        assert (memo.has(reader, key), memo.has(reader, other)) == (True, False)
        assert memo.outputs(reader, key) == {"main": ["card"]}
    assert not hasattr(memo, "valid")
    assert not hasattr(memo, "invalidate_by_definition")


def test_the_key_ignores_key_order_and_names_every_part() -> None:
    one = MemoKey.of("run", "n1", 2, "3", {"a": 1, "b": [1, 2]}, {"type": "script"})
    same = MemoKey.of("run", "n1", 2, "3", {"b": [1, 2], "a": 1}, {"type": "script"})
    assert one.fingerprint == same.fingerprint
    assert (
        len(
            {
                MemoKey.of(
                    "run", "n1", 2, "4", {"a": 1, "b": [1, 2]}, {"type": "script"}
                ).fingerprint,
                MemoKey.of(
                    "run", "n1", 3, "3", {"a": 1, "b": [1, 2]}, {"type": "script"}
                ).fingerprint,
                MemoKey.of(
                    "run", "n1", 2, "3", {"a": 2, "b": [1, 2]}, {"type": "script"}
                ).fingerprint,
                MemoKey.of("run", "n1", 2, "3", {"a": 1, "b": [1, 2]}, {"type": "llm"}).fingerprint,
                one.fingerprint,
            }
        )
        == 5
    )
