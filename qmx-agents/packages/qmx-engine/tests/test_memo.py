from __future__ import annotations

from pathlib import Path

from qmx_engine.ledger import memo
from qmx_engine.ledger.events import JsonObject
from qmx_engine.ledger.memo import MemoKey
from qmx_engine.ledger.store import Ledger, Reader

TRIAGE: JsonObject = {"type": "llm", "parameters": {"prompt_ref": "prompts/triage.md"}}
TRIAGE_EDITED: JsonObject = {"type": "llm", "parameters": {"prompt_ref": "prompts/triage-v2.md"}}
FETCH: JsonObject = {"type": "script", "parameters": {"script_ref": "scripts/feed_ids.py"}}


def test_a_changed_definition_invalidates_exactly_its_memos(tmp_path: Path) -> None:
    triage = [MemoKey.of("run", "triage", 0, str(p), {"chunk": p}, TRIAGE) for p in range(2)]
    fetch = MemoKey.of("run", "fetch", 0, "", {"feed": "arxiv"}, FETCH)
    other_run = MemoKey.of("run-2", "triage", 0, "0", {"chunk": 0}, TRIAGE)
    with Ledger.open(tmp_path) as ledger:
        for key in [*triage, fetch, other_run]:
            memo.record(ledger, key, {"main": [key.partition_id]})
        changed = memo.invalidate_by_definition(
            ledger, "run", {"triage": TRIAGE_EDITED, "fetch": FETCH}
        )

    assert changed == 2
    with Reader.open(tmp_path) as reader:
        assert [(memo.has(reader, k), memo.valid(reader, k)) for k in triage] == [
            (True, False),
            (True, False),
        ]
        assert memo.valid(reader, fetch)
        assert memo.outputs(reader, fetch) == {"main": [""]}
        assert memo.valid(reader, other_run)
        edited = MemoKey.of("run", "triage", 0, "0", {"chunk": 0}, TRIAGE_EDITED)
        assert not memo.has(reader, edited)


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
