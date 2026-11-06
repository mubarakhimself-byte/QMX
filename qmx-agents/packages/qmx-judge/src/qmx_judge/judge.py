"""The judge: pure functions over a study spec, landed results and try rows (Part B AD-207,
Level 0 AD-25). Scripts decide; agents explain; he promotes.

Every market a result traded, or the spec names, is judged by one rule: its mean trade R is shrunk
toward the unit's whole result (`shrink`), and the chain runs cheapest first, each step saying
what it can and cannot fail on (MIS-11). The last step deflates the market's Sharpe by the
family's effective tries, so the best of many markets or variants does not pass on luck. A market
with no trades never passes (QB-15). A step whose evidence no result carries for that market, over
the window its trades ran, is `not_run`, and a verdict with a step not run is `incomplete`, never a
pass: the judge passes only what it checked.

A study version made after the results' first try was written knowing them. The door counts it as
a try, and it judges with the `spread` estimator and `FALLBACK_K`, whatever k it names
(`late_spec`).

A verdict records the judge, checker and tester versions (WF-12), and its item is named by its
inputs, so judging the same results again finds the same verdict and a new judge version lands a
second verdict beside the first.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from statistics import NormalDist
from typing import Final, Literal, cast

from qmf.core import fingerprint, is_refusal

from qmx_judge.landing import LanderPort
from qmx_judge.presets import DEFAULT_PRESET, PRESETS, Preset, preset
from qmx_judge.shrink import FALLBACK_K, Shrunk, estimate_k, shrink
from qmx_judge.tries import Counted, Try, daily_r, effective_tries

__all__ = [
    "BASELINE_KIND",
    "CHAIN",
    "CLUSTER_CORRELATION",
    "DEATH_KIND",
    "FORECAST_KIND",
    "JUDGE_VERSION",
    "PROPOSAL_KIND",
    "STUDY_KIND",
    "VERDICT_KIND",
    "Claim",
    "JudgeRefused",
    "JudgedResult",
    "Judgement",
    "MarketVerdict",
    "Overall",
    "Step",
    "StudySpec",
    "Trade",
    "Verdict",
    "baseline_card",
    "death_certificate",
    "deflated_sharpe",
    "judge",
    "land_judgement",
    "late_spec",
    "parse_spec",
    "proposal_card",
    "quick_spec",
    "score_forecast",
    "spec_edit",
    "spec_problems",
    "trade_r",
]

JUDGE_VERSION: Final = "2"
STUDY_KIND: Final = "study-spec"
VERDICT_KIND: Final = "verdict"
BASELINE_KIND: Final = "baseline-card"
PROPOSAL_KIND: Final = "proposal-card"
DEATH_KIND: Final = "death-certificate"
FORECAST_KIND: Final = "forecast"
CLASSIFIER_VERSION: Final = "1"
SCORER_VERSION: Final = "1"

CLUSTER_CORRELATION: Final = Decimal("0.5")
"""`[judge] cluster_correlation`, the starting default: daily R streams correlated above this
are one try. A spec may raise it, never lower it, because a lower one would count fewer tries."""
MONTE_CARLO_RESAMPLES: Final = 1000
"""The starting default number of bootstrapped trade orders behind the Monte Carlo floor."""
EULER: Final = 0.5772156649
FOUR_PLACES: Final = Decimal("0.0001")

type Overall = Literal["pass", "fail", "too_thin", "no_trades", "incomplete"]
type StepOutcome = Literal["passed", "failed", "not_run"]
type Origin = Literal["written", "quick"]
type Estimator = Literal["spread", "fixed"]
type Window = tuple[str, str]
"""A run's start and end dates."""


class JudgeRefused(ValueError):
    """What the judge will not judge. The first problem is the message; `problems` holds all."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__(problems[0])
        self.problems = tuple(problems)


@dataclass(frozen=True, slots=True)
class Claim:
    edge: str
    horizon: str = ""
    sessions: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StudySpec:
    """A `study-spec` as the judge reads it; `fields` keeps everything else he wrote."""

    origin: Origin
    claim: Claim | None
    markets: tuple[str, ...] | None
    """None is `admitted`. A list adds markets to the ones the results traded and drops none."""
    preset: Preset
    estimator: Estimator
    k: Decimal
    correlated_threshold: Decimal
    min_trades: int
    seed: int
    fields: Mapping[str, object] = field(default_factory=dict[str, object])
    written_late: bool = False
    """Made after the results' first try, so its own k is not used (`late_spec`)."""


def _decimal(value: object) -> Decimal | None:
    if not isinstance(value, str):
        return None
    try:
        found = Decimal(value)
    except InvalidOperation:
        return None
    return found if found.is_finite() else None


def _object(fields: Mapping[str, object], name: str) -> Mapping[str, object]:
    found = fields.get(name)
    return cast(Mapping[str, object], found) if isinstance(found, Mapping) else {}


def _texts(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in cast(list[object], value) if isinstance(item, str))


def _window(fields: Mapping[str, object]) -> Window | None:
    """The dates of `fields`' window, the part of its text a run is cut from."""
    found = _object(fields, "window")
    start, end = found.get("start"), found.get("end")
    return (start[:10], end[:10]) if isinstance(start, str) and isinstance(end, str) else None


def spec_problems(fields: Mapping[str, object]) -> list[str]:
    """What is wrong with a study spec beyond its kind's shape: the registered checker's rule."""
    problems: list[str] = []
    named = fields.get("preset", DEFAULT_PRESET)
    if named not in PRESETS:
        problems.append(f"preset is one of {', '.join(sorted(PRESETS))}, not {named!r}")
    shrinkage = _object(fields, "shrinkage")
    estimator = shrinkage.get("estimator", "spread")
    if estimator not in ("spread", "fixed"):
        problems.append("shrinkage estimator is spread or fixed")
    if "k" in shrinkage:
        k = _decimal(shrinkage["k"])
        if k is None or k <= 0:
            problems.append("shrinkage k is a positive decimal written as text")
    elif estimator == "fixed":
        problems.append("a fixed shrinkage names its k")
    if "correlated_threshold" in fields:
        threshold = _decimal(fields["correlated_threshold"])
        if threshold is None or not Decimal(0) < threshold < Decimal(1):
            problems.append("correlated_threshold is a decimal between 0 and 1, written as text")
    markets = fields.get("markets", "admitted")
    if markets != "admitted" and not _texts(markets):
        problems.append("markets is admitted or a list of market ids")
    return problems


def parse_spec(fields: Mapping[str, object]) -> StudySpec:
    """The spec's fields as the judge reads them, refusing with every problem at once."""
    problems = spec_problems(fields)
    if problems:
        raise JudgeRefused(problems)
    chosen = preset(str(fields.get("preset", DEFAULT_PRESET)))
    claimed = _object(fields, "claim")
    edge = claimed.get("edge")
    claim = (
        Claim(
            edge,
            str(claimed.get("horizon", "")),
            _texts(claimed.get("sessions")),
            _texts(claimed.get("conditions")),
        )
        if isinstance(edge, str)
        else None
    )
    markets = fields.get("markets", "admitted")
    shrinkage = _object(fields, "shrinkage")
    threshold = _decimal(fields.get("correlated_threshold")) or CLUSTER_CORRELATION
    needed = _object(fields, "record_needed").get("trades")
    seeds = fields.get("seeds")
    first_seed = cast(list[object], seeds)[0] if isinstance(seeds, list) and seeds else 0
    return StudySpec(
        origin="quick" if fields.get("origin") == "quick" else "written",
        claim=claim,
        markets=None if markets == "admitted" else _texts(markets),
        preset=chosen,
        estimator="fixed" if shrinkage.get("estimator") == "fixed" else "spread",
        k=_decimal(shrinkage.get("k")) or FALLBACK_K,
        correlated_threshold=max(threshold, CLUSTER_CORRELATION),
        min_trades=max(chosen.min_trades, needed if isinstance(needed, int) else 0),
        seed=first_seed if isinstance(first_seed, int) else 0,
        fields=dict(fields),
    )


def late_spec(spec: StudySpec) -> StudySpec:
    """The spec a study version made after the results' first try judges under. A tiny k leaves
    every weight near 1, which switches the luckiest-market pull off, so its k is not used."""
    return replace(spec, estimator="spread", k=FALLBACK_K, written_late=True)


def quick_spec(idea: str | None) -> dict[str, object]:
    """The implicit spec of a run asked without one, marked `quick`: the shipped preset over
    every admitted market, its claim the unit's own claim card idea."""
    return {
        "origin": "quick",
        "claim": {"edge": idea or "", "horizon": "", "sessions": [], "conditions": []},
        "markets": "admitted",
        "preset": DEFAULT_PRESET,
        "shrinkage": {"estimator": "spread", "k": str(FALLBACK_K)},
        "correlated_threshold": str(CLUSTER_CORRELATION),
        "holdout": "off",
    }


def trade_r(trade: Mapping[str, object]) -> Decimal:
    """The R the judge reads for a trade: `r`, price money over risk, with no costs in it. Whether
    R includes costs is the risk session's call, and `net_r` beside it is this one line away."""
    return Decimal(str(trade["r"]))


@dataclass(frozen=True, slots=True)
class Trade:
    market: str
    closed_at: int
    """Epoch nanoseconds."""
    r: Decimal


@dataclass(frozen=True, slots=True)
class JudgedResult:
    """A landed `backtest-result` as the judge reads it: its fields and its report's trades."""

    result_id: str
    run_id: str
    status: str
    unit: str
    tester: str
    """`<app>@<version>`; results are pooled within one tester version only (QB-13)."""
    zero_trades: bool
    trades: tuple[Trade, ...]
    markets: tuple[str, ...] = ()
    compiled_fp: str | None = None
    evidence: Mapping[str, Mapping[str, object]] = field(
        default_factory=dict[str, Mapping[str, object]]
    )
    """The chain's evidence from the result's measures. `random_entries`, `cost_stress` and
    `walk_forward` are tables keyed by market, each row with its window. `pbo` answers for the
    family, so it is one entry."""
    costs_uncalibrated: bool = False
    placeholders: tuple[str, ...] = ()
    window: Window | None = None

    @classmethod
    def read(
        cls, result_id: str, fields: Mapping[str, object], trades: Sequence[Mapping[str, object]]
    ) -> JudgedResult:
        tester = _object(fields, "tester")
        labels = _object(fields, "labels")
        measures = _object(fields, "measures")
        found = tuple(
            Trade(str(t["market_id"]), int(cast(int, t["closed_at"])), trade_r(t)) for t in trades
        )
        evidence = {
            name: cast(Mapping[str, object], measures[name])
            for name in ("random_entries", "cost_stress", "walk_forward", "pbo")
            if isinstance(measures.get(name), Mapping)
        }
        compiled = fields.get("compiled_fp")
        return cls(
            result_id=result_id,
            run_id=str(fields.get("run_id", "")),
            status=str(fields.get("status", "")),
            unit=str(fields.get("unit", "")),
            tester=f"{tester.get('app', '')}@{tester.get('version', '')}",
            zero_trades=labels.get("zero_trades") is True or not found,
            trades=() if labels.get("zero_trades") is True else found,
            markets=_texts(fields.get("markets")),
            compiled_fp=compiled if isinstance(compiled, str) else None,
            evidence=evidence,
            costs_uncalibrated=labels.get("costs_uncalibrated") is True,
            placeholders=_texts(labels.get("placeholders")),
            window=_window(fields),
        )


@dataclass(frozen=True, slots=True)
class StepRule:
    name: str
    title: str
    can_fail_on: str
    cannot_fail_on: str


CHAIN: Final[tuple[StepRule, ...]] = (
    StepRule("claim", "claim card present", "a missing or empty claim", "anything about results"),
    StepRule(
        "random_entries",
        "signal against random entries",
        "a signal no better than random entries",
        "an edge that only shows after costs",
    ),
    StepRule("cost_stress", "cost stress", "an edge that costs erase", "luck in the sample"),
    StepRule(
        "walk_forward",
        "walk-forward efficiency",
        "settings that only fit the in-sample",
        "an edge that decays after the last window",
    ),
    StepRule(
        "monte_carlo",
        "Monte Carlo floor",
        "a record whose unlucky trade orders lose",
        "luck from many tries",
    ),
    StepRule(
        "pbo",
        "probability of backtest overfitting",
        "a family whose best in-sample pick fails out of sample",
        "one run's luck",
    ),
    StepRule(
        "try_corrected",
        "try-corrected verdict",
        "luck from many tries",
        "a real edge with too few trades yet (it reads too thin to judge)",
    ),
)
"""The default chain, cheapest first (`judge.md` §3). `pbo` runs only in a preset that names it."""


@dataclass(frozen=True, slots=True)
class Step:
    rule: StepRule
    outcome: StepOutcome
    detail: str

    def fields(self) -> dict[str, object]:
        return {
            "name": self.rule.name,
            "passed": self.outcome == "passed",
            "outcome": self.outcome,
            "can_fail_on": self.rule.can_fail_on,
            "cannot_fail_on": self.rule.cannot_fail_on,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class MarketVerdict:
    market: str
    trades: int
    raw_r: Decimal
    shrunk_r: Decimal
    weight: Decimal
    outcome: Overall
    steps: tuple[Step, ...]

    def fields(self) -> dict[str, object]:
        return {
            "market": self.market,
            "trades": self.trades,
            "raw_r": _text(self.raw_r),
            "shrunk_r": _text(self.shrunk_r),
            "weight": _text(self.weight),
            "outcome": self.outcome,
            "steps": [step.fields() for step in self.steps],
        }

    def says(self, needed: int) -> str:
        if self.outcome == "no_trades":
            return f"{self.market} placed no trades"
        trades = _count(self.trades, "trade")
        if self.outcome == "too_thin":
            return f"{self.market} is too thin to judge, {trades} of the {needed} needed"
        if self.outcome == "pass":
            return f"{self.market} passes on {trades} at {_text(self.shrunk_r)}R shrunk"
        failed = next((s for s in self.steps if s.outcome == "failed"), None)
        if failed is not None:
            return f"{self.market} fails the {failed.rule.title}: {failed.detail}"
        waiting = ", ".join(s.rule.title for s in self.steps if s.outcome == "not_run")
        return f"{self.market} is not judged yet: {waiting} not run"


_WORDS: Final[Mapping[str, str]] = {
    "pass": "Pass",
    "fail": "Fail",
    "too_thin": "Too thin to judge",
    "no_trades": "Placed no trades",
    "incomplete": "Not judged yet",
}


@dataclass(frozen=True, slots=True)
class Verdict:
    study: str
    results: tuple[str, ...]
    unit: str
    compiled_fp: str | None
    principal: str
    per_market: tuple[MarketVerdict, ...]
    overall: Overall
    effective_tries: int
    raw_tries: int
    preset: str
    min_trades: int
    versions: Mapping[str, str]
    counted: tuple[str, ...]
    """The labels of every counted try, so the verdict's item names what it was judged on."""
    costs_uncalibrated: bool = False
    """A result behind it paid no costs measured from enough real fills."""
    written_late: bool = False
    """Its study version was made after the results' first try."""

    def says(self) -> str:
        """The verdict in plain words, with the tries behind it."""
        head = f"{_WORDS[self.overall]} by the {self.preset} preset."
        if self.overall == "no_trades":
            head += " A result with no trades never passes."
        markets = "; ".join(m.says(self.min_trades) for m in self.per_market)
        raw = _count(self.raw_tries, "try", "tries")
        tries = f"Behind it: {raw}, {self.effective_tries} effective."
        costs = (
            "These results are costs uncalibrated: their money paid no costs measured from real "
            "fills."
            if self.costs_uncalibrated
            else ""
        )
        late = (
            "This study was written after these results' first try, so it counted as a try and "
            "its own k was not used."
            if self.written_late
            else ""
        )
        parts = (head, f"{markets}." if markets else "", costs, late, tries)
        return " ".join(part for part in parts if part)

    def fields(self) -> dict[str, object]:
        found: dict[str, object] = {
            "study": self.study,
            "results": list(self.results),
            "unit": self.unit,
            "principal": self.principal,
            "per_market": [m.fields() for m in self.per_market],
            "overall": self.overall,
            "effective_tries": self.effective_tries,
            "raw_tries": self.raw_tries,
            "preset": self.preset,
            "versions": dict(self.versions),
            "says": self.says(),
        }
        if self.compiled_fp is not None:
            found["compiled_fp"] = self.compiled_fp
        if self.costs_uncalibrated:
            found["costs_uncalibrated"] = True
        if self.written_late:
            found["written_late"] = True
        return found

    @property
    def item(self) -> str:
        """Named by what it judged and who judged it, never by when."""
        named = fingerprint(
            {
                "study": self.study,
                "results": sorted(self.results),
                "counted": sorted(self.counted),
                "versions": dict(self.versions),
                "preset": self.preset,
            }
        )
        if is_refusal(named):
            raise JudgeRefused([f"the verdict's inputs do not fingerprint: {named}"])
        return f"verdict-{named.value.digest[:24]}"


def _count(n: int, one: str, many: str = "") -> str:
    return f"{n} {one if n == 1 else many or one + 's'}"


def _text(value: Decimal) -> str:
    return str(value.quantize(FOUR_PLACES))


def _decimal_text(value: float) -> str:
    return f"{value:.4f}"


def deflated_sharpe(
    sharpe: float, observations: int, skew: float, kurtosis: float, tries: int
) -> tuple[float, float]:
    """The bar the best of `tries` reaches by luck alone, and the probability that `sharpe`
    beats it net of skew and fat tails (Bailey and Lopez de Prado, 2014). Under no edge a
    Sharpe estimate over `observations` trades has variance about 1/(observations - 1)."""
    normal = NormalDist()
    bar = 0.0
    if tries >= 2 and observations > 1:
        spread = math.sqrt(1 / (observations - 1))
        bar = spread * (
            (1 - EULER) * normal.inv_cdf(1 - 1 / tries)
            + EULER * normal.inv_cdf(1 - 1 / (tries * math.e))
        )
    tails = 1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe**2
    if observations <= 1 or tails <= 0:
        return bar, 0.0
    return bar, normal.cdf((sharpe - bar) * math.sqrt(observations - 1) / math.sqrt(tails))


def _moments(rs: Sequence[float]) -> tuple[float, float, float]:
    """Standard deviation, skew and (non-excess) kurtosis of `rs`."""
    n = len(rs)
    mean = sum(rs) / n
    var = sum((r - mean) ** 2 for r in rs) / n
    if var == 0:
        return 0.0, 0.0, 3.0
    sd = math.sqrt(var)
    skew = sum(((r - mean) / sd) ** 3 for r in rs) / n
    kurt = sum(((r - mean) / sd) ** 4 for r in rs) / n
    return sd, skew, kurt


def _claim(rule: StepRule, spec: StudySpec) -> Step:
    if spec.claim is not None and spec.claim.edge.strip():
        return Step(rule, "passed", f"claims {spec.claim.edge.strip()}")
    return Step(rule, "failed", "the study names no claim")


def _random_entries(rule: StepRule, spec: StudySpec, found: Mapping[str, object]) -> Step:
    ratio, p = _decimal(found.get("edge_ratio")), _decimal(found.get("p"))
    if ratio is None or p is None:
        return Step(rule, "failed", "random_entries carries no edge_ratio and p as text")
    good = ratio > spec.preset.entry_edge_ratio_min and p <= spec.preset.signal_p
    detail = f"entry edge ratio {ratio} at p {p}"
    return Step(rule, "passed" if good else "failed", detail)


def _cost_stress(rule: StepRule, spec: StudySpec, found: Mapping[str, object]) -> Step:
    multiplier, expectancy = _decimal(found.get("multiplier")), _decimal(found.get("expectancy_r"))
    if multiplier is None or expectancy is None:
        return Step(rule, "failed", "cost_stress carries no multiplier and expectancy_r as text")
    if multiplier < spec.preset.cost_stress:
        need = spec.preset.cost_stress
        return Step(rule, "not_run", f"costs stressed {multiplier}x, the preset needs {need}x")
    detail = f"expectancy {expectancy}R at {multiplier}x costs"
    return Step(rule, "passed" if expectancy > 0 else "failed", detail)


def _walk_forward(rule: StepRule, spec: StudySpec, found: Mapping[str, object]) -> Step:
    efficiency = _decimal(found.get("efficiency"))
    if efficiency is None:
        return Step(rule, "failed", "walk_forward carries no efficiency as text")
    need = spec.preset.walk_forward_efficiency
    good = efficiency >= need
    return Step(rule, "passed" if good else "failed", f"efficiency {efficiency} of {need} needed")


_MARKET_EVIDENCE: Final[
    Mapping[str, tuple[Callable[[StepRule, StudySpec, Mapping[str, object]], Step], str]]
] = {
    "random_entries": (_random_entries, "no result in the study ran random entries"),
    "cost_stress": (_cost_stress, "no result in the study stressed its costs"),
    "walk_forward": (_walk_forward, "no result in the study walked forward"),
}
"""The steps a market answers on its own evidence: each one's reader, and its words for no row."""
_WORST_FIRST: Final[tuple[StepOutcome, ...]] = ("failed", "not_run", "passed")


def _spans(windows: set[Window | None]) -> str:
    return ", ".join(
        "no stated window" if window is None else f"{window[0]} to {window[1]}"
        for window in sorted(windows, key=str)
    )


def _covers(rule: StepRule, ran: Window | None, traded: Window | None) -> bool:
    """Whether evidence over `ran` answers for trades over `traded`. Only walk-forward may run
    wider, as template `b`'s does over in-sample and its folds. A wider cost stress or random
    entries would read mostly other trades, so it answers for nothing but its own window. A window
    not stated covers only another not stated, because there is nothing to compare."""
    if ran is None or traded is None or rule.name != "walk_forward":
        return ran == traded
    return ran[0] <= traded[0] and traded[1] <= ran[1]


def _market_step(
    rule: StepRule, spec: StudySpec, results: Sequence[JudgedResult], market: str
) -> Step:
    """`market`'s step on its own rows, which must cover every window its trades ran. A row that
    covers none answers nothing, and of several rows the worst decides, so a second friendly run
    cannot hide a failing one."""
    read, absent = _MARKET_EVIDENCE[rule.name]
    rows = [row for r in results if (row := _object(r.evidence.get(rule.name, {}), market))]
    if not rows:
        return Step(rule, "not_run", f"{absent} on {market}")
    traded = {r.window for r in results if any(t.market == market for t in r.trades)}
    ran = {_window(row) for row in rows}
    uncovered = {w for w in traded if not any(_covers(rule, found, w) for found in ran)}
    if uncovered:
        return Step(
            rule,
            "not_run",
            f"{market}'s evidence ran over {_spans(ran)}, its trades over {_spans(uncovered)}",
        )
    steps = [
        read(rule, spec, row) for row in rows if any(_covers(rule, _window(row), w) for w in traded)
    ]
    return min(steps, key=lambda step: _WORST_FIRST.index(step.outcome))


def _monte_carlo(rule: StepRule, spec: StudySpec, rs: Sequence[float]) -> Step:
    draw = random.Random(spec.seed)  # noqa: S311 - a seeded resample, not a secret
    totals = sorted(sum(draw.choice(rs) for _ in rs) for _ in range(MONTE_CARLO_RESAMPLES))
    p5 = totals[int(0.05 * MONTE_CARLO_RESAMPLES)]
    floor = spec.preset.monte_carlo_p5_above
    good = Decimal(_decimal_text(p5)) > floor
    return Step(rule, "passed" if good else "failed", f"5th percentile {_decimal_text(p5)}R")


def _pbo(rule: StepRule, spec: StudySpec, results: Sequence[JudgedResult]) -> Step:
    found = next((r.evidence["pbo"] for r in results if "pbo" in r.evidence), None)
    if found is None:
        return Step(rule, "not_run", "no result in the study measured the family's PBO")
    value = _decimal(found.get("value"))
    if value is None:
        return Step(rule, "failed", "pbo carries no value as text")
    good = spec.preset.pbo_pass is not None and value < spec.preset.pbo_pass
    return Step(rule, "passed" if good else "failed", f"PBO {value}")


def _try_corrected(
    rule: StepRule, spec: StudySpec, shrunk: Shrunk, rs: Sequence[float], tries: int
) -> Step:
    sd, skew, kurt = _moments(rs)
    if sd == 0:
        return Step(rule, "failed", "every trade made the same R")
    sharpe = float(shrunk.shrunk_r) / sd
    bar, probability = deflated_sharpe(sharpe, len(rs), skew, kurt, tries)
    floor = spec.preset.min_expectancy_r
    good = (
        Decimal(_decimal_text(probability)) >= spec.preset.deflated_sharpe
        and shrunk.shrunk_r > floor
    )
    detail = (
        f"deflated Sharpe {_decimal_text(probability)} over {tries} effective tries "
        f"(luck alone reaches {_decimal_text(bar)} per trade, this market {_decimal_text(sharpe)})"
    )
    return Step(rule, "passed" if good else "failed", detail)


def _outcome(trades: int, needed: int, steps: Sequence[Step]) -> Overall:
    if trades == 0:
        return "no_trades"
    if trades < needed:
        return "too_thin"
    if any(step.outcome == "failed" for step in steps):
        return "fail"
    if any(step.outcome == "not_run" for step in steps):
        return "incomplete"
    return "pass"


def _overall(markets: Sequence[MarketVerdict]) -> Overall:
    found = {m.outcome for m in markets}
    for outcome in ("pass", "fail", "incomplete", "too_thin"):
        if outcome in found:
            return cast(Overall, outcome)
    return "no_trades"


def _counted(
    tries: Sequence[Mapping[str, object]], streams: Mapping[str, Sequence[Counted]]
) -> list[Counted]:
    """One counted try per run (its two items are one try), one per market it traded, and one
    per other kind of try. A behaviour check is not a try at the result."""
    counted: list[Counted] = []
    runs: set[str] = set()
    for row in tries:
        kind, run_id = row.get("kind"), str(row.get("run_id", ""))
        if kind == "check":
            continue
        if kind in ("run", "whatif_rerun"):
            if run_id in runs:
                continue
            runs.add(run_id)
            counted += streams.get(run_id) or [Counted(f"run:{run_id}", None)]
            continue
        counted.append(Counted(f"{kind}:{run_id}", None))
    return counted


def _streams(results: Sequence[JudgedResult]) -> dict[str, list[Counted]]:
    found: dict[str, list[Counted]] = {}
    for result in results:
        by_market: dict[str, list[tuple[int, Decimal]]] = {}
        for trade in result.trades:
            by_market.setdefault(trade.market, []).append((trade.closed_at, trade.r))
        found[result.run_id] = [
            Counted(f"run:{result.run_id}:{market}", daily_r(pairs))
            for market, pairs in sorted(by_market.items())
        ]
    return found


def _pooled_twice(results: Sequence[JudgedResult]) -> list[str]:
    """Why some trades would pool more than once: a result given twice, or two results whose
    trades in one market span overlapping times, as reruns of one window do."""
    given = Counter(r.result_id for r in results)
    problems = [
        f"{result_id} is given {times} times; each result is judged once"
        for result_id, times in given.items()
        if times > 1
    ]
    spans: dict[str, dict[str, tuple[int, int]]] = {}
    for result in results:
        mine = spans.setdefault(result.result_id, {})
        for trade in result.trades:
            low, high = mine.get(trade.market, (trade.closed_at, trade.closed_at))
            mine[trade.market] = (min(low, trade.closed_at), max(high, trade.closed_at))
    ids = list(spans)
    for i, first in enumerate(ids):
        for second in ids[i + 1 :]:
            for market in sorted(spans[first].keys() & spans[second].keys()):
                (a_low, a_high), (b_low, b_high) = spans[first][market], spans[second][market]
                if a_low <= b_high and b_low <= a_high:
                    problems.append(
                        f"{first} and {second} trade {market} over the same time; a market's "
                        "trades pool only across separate windows"
                    )
    return problems


def _pull_table(
    trades: Mapping[str, list[Decimal]],
    results: Sequence[JudgedResult],
    family: Sequence[JudgedResult],
    enough: int,
) -> dict[str, list[Decimal]]:
    """The trades the shrink reads, so that what an agent chooses to judge cannot weaken the pull.
    A market reads the longest record the same code has of it in `family`. Its judged trades stand
    only when they are `enough` to judge it on and overlap no longer record from this tester.
    Same code means an equal `compiled_fp`, else an equal `unit`, or a record holding every judged
    trade. Reruns of one market are never added together."""
    table = {market: rs for market, rs in trades.items() if rs}
    code = {r.compiled_fp or r.unit for r in results}
    testers = {r.tester for r in results}
    judged = [t for r in results for t in r.trades]
    for other in family:
        if (other.compiled_fp or other.unit) not in code and not (
            judged and set(judged) <= set(other.trades)
        ):
            continue
        held: dict[str, list[Trade]] = {}
        for trade in other.trades:
            held.setdefault(trade.market, []).append(trade)
        for market, rows in held.items():
            low, high = min(t.closed_at for t in rows), max(t.closed_at for t in rows)
            overlaps = other.tester in testers and any(
                low <= t.closed_at <= high for t in judged if t.market == market
            )
            thin = len(trades.get(market, ())) < enough
            if (thin or overlaps) and len(rows) > len(table.get(market, ())):
                table[market] = [t.r for t in rows]
    return table


def judge(
    spec: StudySpec,
    *,
    study: str,
    results: Sequence[JudgedResult],
    tries: Sequence[Mapping[str, object]],
    family: Sequence[JudgedResult] = (),
    principal: str,
    versions: Mapping[str, str],
    judge_version: str = JUDGE_VERSION,
) -> Verdict:
    """The verdict on `results` under `spec`. `tries` are the fields of every `try` item of the
    results' families; `family` are other landed results of those families, whose daily R lets
    the clustering find how many of their tries were really different, and whose other markets
    stay in the shrink (`_pull_table`). `versions` names the checker version; the verdict adds the
    judge's and the tester's."""
    opened = {str(t.get("run_id")) for t in tries if t.get("state") == "opened"}
    problems = [] if results else ["the judge needs one landed result at least"]
    problems += [
        f"{r.result_id} has no core run id; the judge reads only runs the core opened"
        for r in results
        if not r.run_id.startswith("qmbr-") or r.run_id not in opened
    ]
    problems += [
        f"{r.result_id} is {r.status}, not finished" for r in results if r.status != "finished"
    ]
    units = sorted({r.unit for r in results})
    if len(units) > 1:
        problems.append(f"one verdict judges one unit, not {', '.join(units)}")
    testers = sorted({r.tester for r in results})
    if len(testers) > 1:
        problems.append(f"results pool within one tester version, not {', '.join(testers)}")
    problems += _pooled_twice(results)
    if problems:
        raise JudgeRefused(problems)
    streams = _streams([*family, *results])
    counted = _counted(tries, streams)
    known = {c.label for c in counted}
    counted += [c for r in results for c in streams[r.run_id] if c.label not in known]
    threshold = float(spec.correlated_threshold)
    tried = max(effective_tries(counted, threshold), 1)
    named = spec.markets if spec.markets is not None else ()
    traded = {t.market for r in results for t in r.trades}
    markets = sorted(set(named) | traded | {m for r in results for m in r.markets})
    trades = {m: [t.r for r in results for t in r.trades if t.market == m] for m in markets}
    table = _pull_table(trades, results, family, spec.min_trades)
    k = spec.k if spec.estimator == "fixed" else estimate_k(table, spec.k)
    shrunk = {s.market: s for s in shrink(table, k)}
    per_market: list[MarketVerdict] = []
    for market in markets:
        rs = [float(r) for r in trades[market]]
        found = shrunk.get(market) if rs else None
        if found is None:
            zero = Decimal(0)
            per_market.append(MarketVerdict(market, 0, zero, zero, zero, "no_trades", ()))
            continue
        steps = _chain(spec, results, found, rs, tried)
        outcome = _outcome(len(rs), spec.min_trades, steps)
        per_market.append(
            MarketVerdict(
                market, len(rs), found.raw_r, found.shrunk_r, found.weight, outcome, steps
            )
        )
    compiled = sorted({r.compiled_fp for r in results if r.compiled_fp})
    return Verdict(
        study=study,
        results=tuple(r.result_id for r in results),
        unit=units[0],
        compiled_fp=compiled[0] if len(compiled) == 1 else None,
        principal=principal,
        per_market=tuple(per_market),
        overall=_overall(per_market),
        effective_tries=tried,
        raw_tries=len(counted),
        preset=spec.preset.name,
        min_trades=spec.min_trades,
        versions={**versions, "judge": judge_version, "tester": testers[0]},
        counted=tuple(c.label for c in counted),
        costs_uncalibrated=any(r.costs_uncalibrated for r in results),
        written_late=spec.written_late,
    )


def _chain(
    spec: StudySpec,
    results: Sequence[JudgedResult],
    shrunk: Shrunk,
    rs: Sequence[float],
    tries: int,
) -> tuple[Step, ...]:
    steps: list[Step] = []
    for rule in CHAIN:
        match rule.name:
            case "claim":
                steps.append(_claim(rule, spec))
            case "random_entries" | "cost_stress" | "walk_forward":
                steps.append(_market_step(rule, spec, results, shrunk.market))
            case "monte_carlo":
                steps.append(_monte_carlo(rule, spec, rs))
            case "pbo":
                if spec.preset.pbo_pass is not None:
                    steps.append(_pbo(rule, spec, results))
            case _:
                steps.append(_try_corrected(rule, spec, shrunk, rs, tries))
    return tuple(steps)


def spec_edit(
    spec_object: str,
    *,
    unit: str,
    family: str,
    principal: str,
    at: str,
) -> Try:
    """The `spec_edit` try a new study spec version lands when a result exists against an
    earlier one: editing the rules after reading a result is a counted try (Level 0 AD-25)."""
    return Try(
        kind="spec_edit",
        state="recorded",
        run_id=spec_object,
        family=family,
        unit=unit,
        principal=principal,
        at=at,
        study=spec_object,
    )


CAUSES: Final[Mapping[str, str]] = {
    "claim": "behaviour",
    "random_entries": "no_signal",
    "cost_stress": "costs",
    "walk_forward": "overfit",
    "monte_carlo": "no_signal",
    "pbo": "overfit",
    "try_corrected": "overfit",
}
"""The death certificate's cause, by the first step a failed market failed; appendable."""


def death_certificate(verdict_id: str, verdict: Verdict) -> dict[str, object] | None:
    """A typed cause of death for a failed verdict, classified by script; agents explain it."""
    if verdict.overall not in ("fail", "no_trades"):
        return None
    cause = "no_trades"
    if verdict.overall == "fail":
        failed = [
            step.rule.name
            for market in verdict.per_market
            if market.outcome == "fail"
            for step in market.steps
            if step.outcome == "failed"
        ]
        cause = CAUSES[failed[0]] if failed else "behaviour"
    return {
        "unit": verdict.unit,
        "verdict": verdict_id,
        "cause": cause,
        "classifier_version": CLASSIFIER_VERSION,
    }


def baseline_card(
    verdict_id: str,
    verdict: Verdict,
    results: Sequence[JudgedResult],
    spec: StudySpec,
) -> dict[str, object] | None:
    """The record a passing unit froze, which the decay check compares live against."""
    if verdict.overall != "pass":
        return None
    passed = {m.market for m in verdict.per_market if m.outcome == "pass"}
    trades = sorted(
        (t for r in results for t in r.trades if t.market in passed), key=lambda t: t.closed_at
    )
    rs = [t.r for t in trades]
    total = sum(rs, Decimal(0))
    draw = random.Random(spec.seed)  # noqa: S311 - a seeded resample, not a secret
    floats = [float(r) for r in rs]
    cone: list[dict[str, object]] = []
    for count in sorted({c for c in (25, 50, 100, len(floats)) if c <= len(floats)}):
        paths = sorted(
            sum(draw.choice(floats) for _ in range(count)) for _ in range(MONTE_CARLO_RESAMPLES)
        )
        cone.append(
            {
                "trades": count,
                "p5": _decimal_text(paths[int(0.05 * MONTE_CARLO_RESAMPLES)]),
                "p50": _decimal_text(paths[MONTE_CARLO_RESAMPLES // 2]),
                "p95": _decimal_text(paths[int(0.95 * MONTE_CARLO_RESAMPLES)]),
            }
        )
    span_days = max((trades[-1].closed_at - trades[0].closed_at) / 86_400e9, 1.0)
    return {
        "unit": verdict.unit,
        "verdict": verdict_id,
        "record_r": {
            "trades": len(rs),
            "total_r": _text(total),
            "mean_r": _text(total / len(rs)),
            "markets": sorted(passed),
        },
        "cone": cone,
        "cost_assumptions": {"rule": str(spec.fields.get("cost_rule", "the tester's profile"))},
        "fill_assumptions": {"model": str(spec.fields.get("fill_model", "the tester's model"))},
        "trade_rate": {"per_week": _decimal_text(len(rs) / span_days * 7)},
        "readings_range": {},
    }


def proposal_card(
    verdict_id: str,
    verdict: Verdict,
    *,
    ask: str = "paper",
    placeholders: Sequence[str] = (),
) -> dict[str, object] | None:
    """What waits for his click after a pass. It never moves a unit; his click does."""
    if verdict.overall != "pass":
        return None
    return {
        "subject": verdict.unit,
        "ask": ask,
        "evidence": [verdict_id, *verdict.results],
        "verdict": verdict_id,
        "tries": verdict.effective_tries,
        "preset": verdict.preset,
        "placeholders": list(placeholders),
        "made_by": verdict.principal,
    }


def score_forecast(forecast: Mapping[str, object], happened: bool, at: str) -> dict[str, object]:
    """A dated call scored after its horizon by a script, never by its forecaster: the Brier
    score of its confidence against what the market's recorded data shows happened."""
    confidence = _decimal(forecast.get("confidence")) or Decimal("0.5")
    outcome = Decimal(1) if happened else Decimal(0)
    return {
        **forecast,
        "scored_at": at,
        "score": str(((confidence - outcome) ** 2).quantize(FOUR_PLACES)),
        "scorer_version": SCORER_VERSION,
    }


@dataclass(frozen=True, slots=True)
class Judgement:
    """What landed: the verdict and the cards it froze."""

    verdict: str
    cards: Mapping[str, str]


def land_judgement(
    library: LanderPort,
    verdict: Verdict,
    *,
    results: Sequence[JudgedResult],
    spec: StudySpec,
    writer: str,
    placeholders: Sequence[str] = (),
) -> Judgement:
    """Land the verdict and the cards it calls for, each once: a pass freezes its baseline card
    and leaves a proposal for his click, a failure lands its death certificate. Landing it again
    finds every item and writes nothing."""

    def once(kind: str, item: str, fields: Mapping[str, object], title: str) -> str:
        found = library.find(item)
        if found is not None:
            return found
        stored = library.put(
            kind, fields, {}, item=item, title=title, summary=title, principal=writer
        )
        return stored.object_id

    verdict_id = once(VERDICT_KIND, verdict.item, verdict.fields(), verdict.says()[:200])
    library.link(verdict_id, "tests", verdict.unit, principal=writer)
    library.link(verdict_id, "uses", verdict.study, principal=writer)
    for result in verdict.results:
        library.link(verdict_id, "consumed", result, principal=writer)
    cards: dict[str, str] = {}
    made: tuple[tuple[str, Callable[[], dict[str, object] | None]], ...] = (
        (BASELINE_KIND, lambda: baseline_card(verdict_id, verdict, results, spec)),
        (PROPOSAL_KIND, lambda: proposal_card(verdict_id, verdict, placeholders=placeholders)),
        (DEATH_KIND, lambda: death_certificate(verdict_id, verdict)),
    )
    for kind, build in made:
        fields = build()
        if fields is None:
            continue
        card = once(kind, f"{kind}-{verdict.item}", fields, f"{kind} of {verdict.unit}")
        library.link(card, "derived-from", verdict_id, principal=writer)
        cards[kind] = card
    return Judgement(verdict_id, cards)
