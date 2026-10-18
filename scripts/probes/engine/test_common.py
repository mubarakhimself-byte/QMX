# ruff: noqa: S101
from __future__ import annotations

import json
from pathlib import Path

from common import cache_read, model_calls


def row(seq: int, event: str, cache: int) -> str:
    return json.dumps(
        {
            "seq": seq,
            "run_id": "chat-1",
            "event": event,
            "payload": {
                "profile": "claude",
                "model": "claude-haiku",
                "input_tokens": 10,
                "output_tokens": 2,
                "cache_read_tokens": cache,
                "cache_write_tokens": 7,
            },
        }
    )


def test_the_reader_sums_cache_reads_and_skips_a_malformed_line(tmp_path: Path) -> None:
    journal = tmp_path / "journal.jsonl"
    journal.write_text(
        "\n".join(
            [
                row(1, "model_call", 1200),
                '{"seq": 2, "run_id": "chat-1", "event": "model_ca',
                row(3, "token_count", 999),
                row(4, "model_call", 3400),
            ]
        ),
        encoding="utf-8",
    )

    calls = model_calls(journal)

    assert [call.seq for call in calls] == [1, 4]
    assert cache_read(calls) == 4600


def test_a_missing_journal_reads_as_no_rows(tmp_path: Path) -> None:
    assert model_calls(tmp_path / "absent.jsonl") == []
