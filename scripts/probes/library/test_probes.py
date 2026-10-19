"""Each probe's verdict on a passing and a failing recorded fixture, plus the two pieces of probe
logic a verdict rests on: the `marks()` walk and the grounder's score.

uv run --no-sync python -m pytest scripts/probes/library -q
"""

# ruff: noqa: S101

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common
import p_mem
import p_nest
import p_ops
import p_srch
import p_taint


def test_taint_passes_at_a_p95_within_50_ms_on_the_full_ancestry() -> None:
    result = p_taint.verdict([12.0] * 19 + [49.0], ancestry=500, levels=20)
    assert (result.outcome, result.numbers["p95_ms"], result.fallback) == ("PASS", 12.0, "")


def test_taint_fails_over_50_ms_and_names_the_closure_index() -> None:
    result = p_taint.verdict([12.0] * 10 + [80.0] * 10, ancestry=500, levels=20)
    assert (result.outcome, result.numbers["p95_ms"]) == ("FAIL", 80.0)
    assert result.fallback == p_taint.FALLBACK


def test_taint_fails_a_graph_smaller_than_the_pass_line() -> None:
    assert p_taint.verdict([1.0], ancestry=441, levels=20).outcome == "FAIL"


def test_marks_returns_the_worst_mark_and_the_path_to_it(tmp_path: Path) -> None:
    db = sqlite3.connect(tmp_path / "m.db")
    db.executescript(p_taint.SCHEMA)
    db.executemany(
        "INSERT INTO items VALUES (?, 'dataset', ?)",
        [("ia", "a"), ("ib", "b"), ("ic", "c2"), ("id", "d")],
    )
    db.executemany(
        "INSERT INTO objects VALUES (?, ?)",
        [("a", "ia"), ("b", "ib"), ("c", "ic"), ("c2", "ic"), ("d", "id")],
    )
    db.executemany(
        "INSERT INTO edges VALUES (?, ?, ?)",
        [
            ("a", "b", "consumed"),
            ("b", "c", "uses"),
            ("c", "d", "derived-from"),
            ("a", "x", "cites"),
        ],
    )
    db.execute("INSERT INTO marks VALUES ('id', 'quarantined', 'bad feed')")
    found = p_taint.marks(db, "a")
    assert (found.worst, found.path) == ("quarantined", ("a", "b", "c", "d"))
    db.execute("DELETE FROM marks")
    found = p_taint.marks(db, "a")
    assert (found.worst, found.path, p_taint.depth(found, "a")) == (
        "superseded",
        ("a", "b", "c"),
        3,
    )


def test_nest_passes_when_neither_folder_has_a_problem() -> None:
    assert p_nest.verdict([], []).outcome == "PASS"


def test_nest_fails_with_the_codes_and_the_validator_exception() -> None:
    result = p_nest.verdict(["nesting_unsupported"], [])
    assert (result.outcome, result.fallback) == ("FAIL", p_nest.FALLBACK)
    assert result.reason == "the validator refuses it: nesting_unsupported"


def scores(hindsight: float, fts5: float) -> dict[str, dict[str, float]]:
    return {
        "hindsight": dict.fromkeys(p_mem.TYPES, hindsight),
        "fts5": dict.fromkeys(p_mem.TYPES, fts5),
    }


def test_mem_passes_when_hindsight_matches_fts5_within_ram_and_time() -> None:
    assert p_mem.judge(scores(2.0, 2.0), memory_mb=1500, retain_s=12.0).outcome == "PASS"


def test_mem_fails_on_ram_first_with_the_server_fallback() -> None:
    result = p_mem.judge(scores(3.0, 1.0), memory_mb=2100, retain_s=12.0)
    assert (result.outcome, result.reason, result.fallback) == (
        "FAIL",
        "FAIL on RAM",
        p_mem.FALLBACK_RAM,
    )


def test_mem_fails_on_quality_naming_the_types_behind() -> None:
    behind = scores(2.0, 2.0)
    behind["hindsight"]["dead-end"] = 1.0
    result = p_mem.judge(behind, memory_mb=1500, retain_s=12.0)
    assert result.reason == "FAIL on quality: Hindsight is behind FTS5 on dead-end"
    assert result.fallback == p_mem.FALLBACK_QUALITY


def test_mem_reports_every_failed_line_with_its_fallback() -> None:
    behind = scores(2.0, 2.0)
    behind["hindsight"]["lab-to-hub"] = 1.0
    result = p_mem.judge(behind, memory_mb=2223, retain_s=42.0)
    assert result.reason == (
        "FAIL on RAM; FAIL on quality: Hindsight is behind FTS5 on lab-to-hub; "
        "FAIL on retain time: the digest retain did not finish within 30 s"
    )
    assert result.fallback == " ".join(
        (p_mem.FALLBACK_RAM, p_mem.FALLBACK_QUALITY, p_mem.FALLBACK_RETAIN)
    )


def test_mem_relevance_needs_every_joined_phrase() -> None:
    question = p_mem.Question("decided", "q", ("hindsight & ruling 119",))
    hits = ["Hindsight, ruling 119", "Hindsight only", "ruling 119 only"]
    assert p_mem.relevant(hits, question) == 1


def test_ops_passes_a_small_row_and_a_small_share() -> None:
    assert p_ops.verdict(809, 0.03, ticks=60, seconds=1800).outcome == "PASS"


def test_ops_fails_a_row_over_4_kb() -> None:
    result = p_ops.verdict(5000, 0.03, ticks=60, seconds=1800)
    assert (result.outcome, result.reason) == ("FAIL", "the row is over its line")


def item(item_id: str, title: str, producer: str = "operator") -> p_srch.Item:
    return p_srch.Item(item_id, "backtest-result", title, (), "2026-10-01", title, producer)


def test_grounder_answers_by_alias_and_abstains_on_no_match() -> None:
    items = [item("a", "london breakout"), item("b", "gold scalping")]
    table = p_srch.aliases(items)
    assert p_srch.ground("the london breakout", items, table) == p_srch.Answer(("a",), 1.0)
    assert p_srch.ground("eurusd news", items, table) == p_srch.Answer((), 0.0)


def test_trusted_items_rank_above_newer_test_runs() -> None:
    items = [item("his", "london breakout"), item("noise", "london breakout", "test-run")]
    noisy = [*items[1:], items[0]]
    assert p_srch.ground("london breakout", noisy, p_srch.aliases(noisy)).ids == ("his", "noise")


def test_srch_passes_at_the_line_on_a_real_store() -> None:
    answers = [p_srch.Answer(("a",), 1.0)] * 9 + [p_srch.Answer((), 0.0)]
    found = p_srch.score(answers, [["a"]] * 10)
    assert (found.precision, found.coverage) == (1.0, 0.9)
    assert p_srch.verdict(found, kept_top5=True, noise_ok=True, distinct_items=40).outcome == "PASS"


def test_srch_fails_below_the_line_and_on_a_one_item_store() -> None:
    answers = [p_srch.Answer(("b",), 1.0)] * 5 + [p_srch.Answer(("a",), 1.0)] * 5
    found = p_srch.score(answers, [["a"]] * 10)
    assert found.precision == 0.5
    assert p_srch.verdict(found, True, True, distinct_items=40).outcome == "FAIL"
    perfect = p_srch.score([p_srch.Answer(("a",), 1.0)], [["a"]])
    single = p_srch.verdict(perfect, True, True, distinct_items=1)
    assert (single.outcome, single.fallback) == ("FAIL", p_srch.FALLBACK)


def test_redact_hides_a_key_but_keeps_a_word_that_holds_sk() -> None:
    fake = "sk-" + "a1" * 12
    text = f"key {fake} in plan/risk-sizing-session-outcome"
    assert common.redact(text) == "key [redacted] in plan/risk-sizing-session-outcome"
