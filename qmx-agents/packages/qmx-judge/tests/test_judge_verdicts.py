"""The referee cannot be gamed: luck, many variants, zero trades and unopened runs never pass."""

from __future__ import annotations

import dataclasses
import math
import random
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmx_engine.ledger import redact
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_judge.judge import (
    JudgedResult,
    JudgeRefused,
    Trade,
    Verdict,
    judge,
    land_judgement,
    parse_spec,
)
from qmx_judge.landing import Stored
from qmx_judge.tries import Counted, effective_tries

DAY = 86_400 * 10**9
START = 1_735_689_600 * 10**9
"""2025-01-01 00:00 UTC."""
OPERATOR = Principal("operator")
SPEC = parse_spec(
    {
        "origin": "written",
        "claim": {"edge": "buys pullbacks in an uptrend", "horizon": "a day"},
        "markets": "admitted",
        "preset": "shipped",
    }
)
EVIDENCE: Mapping[str, Mapping[str, object]] = {
    "random_entries": {"edge_ratio": "1.4", "p": "0.01"},
    "cost_stress": {"multiplier": "1.5", "expectancy_r": "0.2"},
    "walk_forward": {"efficiency": "0.7"},
}
"""Every cheaper step passes, so only the try-corrected verdict can stop a lucky market."""


def run_id(n: int) -> str:
    return f"qmbr-pc-{n:026d}"


def result(
    n: int,
    trades: Mapping[str, list[Decimal]],
    *,
    evidence: Mapping[str, Mapping[str, object]] = EVIDENCE,
    zero: bool = False,
    result_id: str | None = None,
) -> JudgedResult:
    found = tuple(
        Trade(market, START + day * DAY, r)
        for market, rs in sorted(trades.items())
        for day, r in enumerate(rs)
    )
    return JudgedResult(
        result_id=result_id or f"result-{n}",
        run_id=run_id(n),
        status="finished",
        unit="unit-v1",
        tester="qmb@0.1.0",
        zero_trades=zero,
        trades=() if zero else found,
        markets=tuple(sorted(trades)),
        compiled_fp="fp1:sha256:unit",
        evidence=evidence,
    )


def opened(*results: JudgedResult) -> list[dict[str, object]]:
    return [
        {"kind": "run", "state": state, "run_id": r.run_id, "family": "unit-v1"}
        for r in results
        for state in ("opened", "landed")
    ]


def verdict_of(*results: JudgedResult, **kwargs: object) -> Verdict:
    return judge(
        SPEC,
        study="study-v1",
        results=results,
        tries=opened(*results),
        principal="agent:chat",
        versions={"checker": "qml 0.1.0"},
        **kwargs,  # pyright: ignore[reportArgumentType]
    )


def markets(seed: int, count: int, edge: float, trades: int = 100) -> dict[str, list[Decimal]]:
    draw = random.Random(seed)  # noqa: S311 - a seeded fixture, not a secret
    return {
        f"fx.m{i:02d}": [Decimal(f"{draw.gauss(edge, 1):.4f}") for _ in range(trades)]
        for i in range(count)
    }


def test_the_best_of_twenty_markets_does_not_pass_on_luck() -> None:
    """Research 24's trap: 20 markets of 100 trades with a true edge of +0.06R."""
    verdict = verdict_of(result(1, markets(24, 20, 0.06)))
    best = max(verdict.per_market, key=lambda m: m.raw_r)
    lucky = next(s for s in best.steps if s.rule.name == "try_corrected")

    assert (best.market, str(best.raw_r.quantize(Decimal("0.0001")))) == ("fx.m04", "0.2782")
    assert str(best.shrunk_r.quantize(Decimal("0.0001"))) == "0.1349"
    assert abs(best.shrunk_r - Decimal("0.06")) < Decimal("0.1"), "test bound: within 0.1R"
    assert (best.outcome, lucky.outcome) == ("fail", "failed")
    assert [m.outcome for m in verdict.per_market] == ["fail"] * 20
    assert (verdict.overall, verdict.raw_tries, verdict.effective_tries) == ("fail", 20, 20)


def test_a_real_edge_passes_and_says_so_with_its_tries() -> None:
    verdict = verdict_of(result(1, markets(3, 1, 0.5, trades=150)))

    assert verdict.overall == "pass"
    assert verdict.says() == (
        "Pass by the shipped preset. fx.m00 passes on 150 trades at 0.3226R shrunk. "
        "Behind it: 1 tries, 1 effective."
    )


def test_a_step_no_result_could_run_leaves_the_verdict_incomplete_never_a_pass() -> None:
    verdict = verdict_of(result(1, markets(3, 1, 0.5, trades=150), evidence={}))

    assert verdict.overall == "incomplete"
    assert verdict.says() == (
        "Not judged yet by the shipped preset. fx.m00 is not judged yet: signal against random "
        "entries, cost stress, walk-forward efficiency not run. Behind it: 1 tries, 1 effective."
    )


def test_a_zero_trade_result_never_passes() -> None:
    claimed = result(1, markets(3, 1, 0.5, trades=150), zero=True)
    empty = result(2, {"fx.m00": []})

    for verdict in (verdict_of(claimed), verdict_of(empty)):
        assert verdict.overall == "no_trades"
        assert verdict.says() == (
            "Placed no trades by the shipped preset. A result with no trades never passes. "
            "fx.m00 placed no trades. Behind it: 1 tries, 1 effective."
        )


def test_a_result_the_core_never_opened_is_refused() -> None:
    stray = result(1, markets(3, 1, 0.5, trades=150))
    with pytest.raises(JudgeRefused) as refused:
        judge(
            SPEC,
            study="study-v1",
            results=[stray],
            tries=[],
            principal="agent:chat",
            versions={},
        )
    assert refused.value.problems == (
        "result-1 has no core run id; the judge reads only runs the core opened",
    )


def variants(seed: int) -> list[dict[str, float]]:
    """Research 24's family: a base, 40 tweaks at 0.95 to it, 10 distinct units at 0.2."""
    draw = random.Random(seed)  # noqa: S311 - a seeded fixture, not a secret
    days = range(500)
    base = [draw.gauss(0, 1) for _ in days]
    common = [draw.gauss(0, 1) for _ in days]
    rows = [base]
    rows += [
        [0.95 * b + math.sqrt(1 - 0.95**2) * draw.gauss(0, 1) for b in base] for _ in range(40)
    ]
    rows += [
        [0.2 * c + math.sqrt(1 - 0.2**2) * draw.gauss(0, 1) for c in common] for _ in range(10)
    ]
    return [{f"d{d:03d}": value for d, value in zip(days, row, strict=True)} for row in rows]


def test_51_variants_cluster_to_11_effective_tries() -> None:
    streams = variants(11)

    assert effective_tries([Counted(f"v{i}", s) for i, s in enumerate(streams)], 0.5) == 11


def test_the_verdict_counts_51_variants_of_one_family_as_11_tries() -> None:
    family = [
        result(n, {"fx.eurusd": [Decimal(f"{v:.4f}") for v in stream.values()]})
        for n, stream in enumerate(variants(11))
    ]
    verdict = judge(
        SPEC,
        study="study-v1",
        results=family[:1],
        tries=opened(*family),
        family=family[1:],
        principal="agent:chat",
        versions={},
    )

    assert (verdict.raw_tries, verdict.effective_tries) == (51, 11)


class StoreLanding:
    """The judge's Library port over a real store, writing on main as the operator."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def find(self, item: str) -> str | None:
        head = self.store.head(item, "main")
        return None if head is None else head[0]

    def put(
        self,
        kind: str,
        fields: Mapping[str, object],
        blobs: Mapping[str, bytes],
        *,
        item: str | None,
        title: str,
        summary: str,
        principal: str,
    ) -> Stored:
        draft = Draft(kind, item, title, summary, fields=cast(JsonObject, dict(fields)))
        return Stored(self.store.put(OPERATOR, draft, on="main", expected_head=None).object_id)

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str:
        return self.store.relate(OPERATOR, from_id, relation, to_id)


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    wall = lambda: datetime(2026, 11, 2, tzinfo=UTC)  # noqa: E731
    with Store.open(tmp_path / "library", redactor=redact, wall=wall) as opened_store:
        yield opened_store


def note(store: Store, item: str) -> str:
    draft = Draft("note", item, item, fields={})
    return store.put(OPERATOR, draft, on="main", expected_head=None).object_id


def test_a_judge_version_bump_lands_a_second_verdict_beside_the_first(store: Store) -> None:
    unit, study, landed = note(store, "unit"), note(store, "study"), note(store, "result")
    library = StoreLanding(store)
    real = result(1, markets(3, 1, 0.5, trades=150), result_id=landed)

    def judged(version: str) -> Verdict:
        found = judge(
            SPEC,
            study=study,
            results=[real],
            tries=opened(real),
            principal="agent:chat",
            versions={},
            judge_version=version,
        )
        return dataclasses.replace(found, unit=unit)

    first = land_judgement(library, judged("1"), results=[real], spec=SPEC, writer="operator")
    again = land_judgement(library, judged("1"), results=[real], spec=SPEC, writer="operator")
    bumped = land_judgement(library, judged("2"), results=[real], spec=SPEC, writer="operator")
    verdicts = store.with_field("verdict", "unit", unit)

    assert again == first
    assert bumped.verdict != first.verdict
    assert verdicts == [first.verdict, bumped.verdict]
    assert [store.get(OPERATOR, v).fields["versions"] for v in verdicts] == [
        {"judge": "1", "tester": "qmb@0.1.0"},
        {"judge": "2", "tester": "qmb@0.1.0"},
    ]
    assert sorted(first.cards) == ["baseline-card", "proposal-card"]
    proposal = store.get(OPERATOR, first.cards["proposal-card"]).fields
    assert (proposal["ask"], proposal["tries"], proposal["made_by"]) == ("paper", 1, "agent:chat")


def test_a_weak_edge_that_fails_lands_a_death_certificate_with_its_cause(store: Store) -> None:
    unit, study, landed = note(store, "unit"), note(store, "study"), note(store, "result")
    lucky = result(1, markets(24, 20, 0.06), result_id=landed)
    found = judge(
        SPEC, study=study, results=[lucky], tries=opened(lucky), principal="agent:chat", versions={}
    )
    verdict = dataclasses.replace(found, unit=unit)

    landed_judgement = land_judgement(
        StoreLanding(store), verdict, results=[lucky], spec=SPEC, writer="operator"
    )
    death = store.get(OPERATOR, landed_judgement.cards["death-certificate"]).fields

    assert sorted(landed_judgement.cards) == ["death-certificate"]
    assert (death["cause"], death["unit"]) == ("no_signal", unit)
