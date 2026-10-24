"""The template pack's catalogue: the 31 templates ENGINE-PLAN Appendix I lists, with their needs,
and the copilot eval battery (engine AD-66).

Each row names its plain title and id (ruling 35, SOLUTION-DESIGN 26.9), the cards in research
files 15, 16, 17 or 44 it was built from, what it waits for, and its folder. Since TP4 every row
has one. A row with `needs` gets a definition naming the same `meta.needs` and installs as a
validated draft; any other row is tested on real models and published disabled. `test_cost` is what
the row's test run cost when it was measured on the cheapest test candidates.

The id is a plain phrase and the code prefix is gone. `ALIASES` keeps every id the pack used before
TPL1, so an old id still finds its template and installs it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal

from pydantic import JsonValue

from qmx_engine.definition.model import Need
from qmx_engine.triggers.cron import Cron

type CardFile = Literal["15", "16", "17", "44", "46"]

PACK: Final = Path(__file__).resolve().parent
SHARED: Final = PACK / "_shared"


@dataclass(frozen=True, slots=True)
class Card:
    file: CardFile
    """`15-templates-researcher.md`, `16-templates-trader-risk.md`, `17-templates-dev-pm-lab.md` or
    `44-agentic-engineering-foundations.md` under `tracker/qma-v2/research/methodology/`."""
    card: str
    """The card's id in that file's headings, such as `R1` (file 16 reuses `R1` for a risk card)."""


@dataclass(frozen=True, slots=True)
class Template:
    id: str
    """The plain id the copilot and the CLI look a template up by; the shelf shows `name`."""
    name: str
    cards: tuple[Card, ...]
    pr: str
    needs: tuple[Need, ...] = ()
    folder: str = field(kw_only=True)
    """The workflow folder under the pack, which is also the workflow's id. B-91: every row has one,
    so it is required rather than a `None` the install path has to refuse."""
    triggers: tuple[Cron, ...] = ()
    """The card's schedule. Install adds each one disabled once the template is published; the
    manual kind is in the definition."""
    test_inputs: JsonValue = None
    test_cost: str | None = None


def card(file: CardFile, *ids: str) -> tuple[Card, ...]:
    return tuple(Card(file, found) for found in ids)


NODE: Final[tuple[Need, ...]] = ("trading-node",)
QMB: Final[tuple[Need, ...]] = ("qmb-door",)
SANDBOX: Final[tuple[Need, ...]] = ("sandbox",)
"""A placed attempt runs under the sandbox tool server (AD-25, H8); the template is a draft until
that placement exists, which is what `meta.needs` records."""

CATALOG: Final[tuple[Template, ...]] = (
    Template(
        "paper-scout-to-research-note",
        "Paper scout to research note",
        card("15", "R1"),
        "TP1",
        folder="rs1-paper-scout",
        triggers=(Cron("0 */6 * * *", "UTC"),),
        test_inputs={"fixture": True},
        test_cost="TPL1 lane 2: 5 haiku turns, tokens in 10, out 20, cache read 21615; 63 s",
    ),
    Template(
        "news-and-macro-calendar-watch",
        "News and macro calendar watch",
        card("16", "T3"),
        "TP1",
        folder="t3-news-calendar-watch",
        triggers=(Cron("5 0 * * *", "UTC"),),
        test_inputs={"fixture": "surprise"},
        test_cost="TPL1 lane 2: 1 haiku turn, tokens in 2, out 5, cache read 4207; 13 s",
    ),
    Template(
        "rough-idea-to-test-plan",
        "Question a rough idea until it is a clear test plan",
        card("15", "R0"),
        "TP2",
        folder="rs0-idea-grill",
        test_inputs={"fixture": True},
        test_cost="TPL1 lane 2: 2 haiku turns, tokens in 4, out 9, cache read 5696; 54 s",
    ),
    Template(
        "source-to-component-card",
        "Source to component card",
        card("15", "R2", "R5", "R7"),
        "TP2",
        folder="rs2-source-to-component-card",
        test_inputs={"fixture": True},
        test_cost="TPL1 lane 2: 5 haiku turns, tokens in 10, out 16, cache read 15564; 42 s",
    ),
    Template(
        "literature-review-on-a-topic",
        "Literature review on a topic",
        card("15", "R4", "R7"),
        "TP2",
        folder="rs4-literature-review",
        test_inputs={"fixture": True},
        test_cost="TPL1 lane 2: 9 haiku turns, tokens in 18, out 34, cache read 27515; 150 s",
    ),
    Template(
        "video-to-strategy-ideas",
        "Turn a video, a playlist or saved posts into strategy ideas",
        card("15", "R5", "R7"),
        "TP2",
        folder="a-fill-the-library",
        test_inputs={"fixture": "one-video"},
        test_cost="TPL1 lane 2: 8 haiku turns, tokens in 16, out 24, cache read 22218; 76 s",
    ),
    Template(
        "weekly-review",
        "Weekly review",
        card("15", "R9") + card("17", "D10"),
        "TP2",
        folder="rv-weekly-review",
        triggers=(Cron("0 6 * * 1", "UTC"),),
        test_inputs={"fixture": True},
        test_cost="TPL1 lane 2: 2 haiku turns, tokens in 4, out 6, cache read 4590; 26 s",
    ),
    Template(
        "morning-market-brief",
        "Morning market brief before each session",
        card("16", "T1", "T2", "T10"),
        "TP3",
        folder="db-desk-brief",
        triggers=(
            Cron("0 6 * * 1-5", "Europe/London"),
            Cron("30 7 * * 1-5", "America/New_York"),
            Cron("5 17 * * 1-5", "America/New_York"),
        ),
        test_inputs={"fixture": "busy"},
        test_cost="TPL1 lane 2: 1 haiku turn, tokens in 2, out 4, cache read 2295; 23 s",
    ),
    Template(
        "research-desk-overnight",
        "Research desk overnight",
        card("16", "T4"),
        "TP3",
        folder="t4-research-desk-overnight",
        triggers=(Cron("0 3 * * 0-4", "Europe/London"),),
        test_inputs={"fixture": True},
        test_cost="TPL1 lane 2: 4 haiku turns, tokens in 8, out 17, cache read 9180; 40 s",
    ),
    Template(
        "copilot-eval-battery",
        "Copilot eval battery",
        card("44", "DC-10"),
        "EVAL",
        folder="ev-copilot-eval-battery",
        test_inputs={"fixture": True},
        test_cost="TPL1 lane 2: 4 haiku turns, tokens in 8, out 13, cache read 9180; 41 s",
    ),
    Template(
        "demo-trades-fill-quality",
        "Watch demo trades and check fill quality",
        card("16", "T5", "T9"),
        "TP3",
        NODE,
        folder="dm-demo-monitor",
    ),
    Template(
        "trade-journal-in-risk-units",
        "Review my trade journal in risk units",
        card("16", "T7"),
        "TP3",
        NODE,
        folder="t7-trade-journal-review",
    ),
    Template(
        "trading-guards-alive",
        "Check that the trading guards are alive",
        card("16", "R1", "R6"),
        "TP3",
        NODE,
        folder="gw-guard-watchdogs",
    ),
    Template(
        "correlation-and-exposure-drift",
        "Correlation and exposure drift",
        card("16", "R2"),
        "TP3",
        NODE,
        folder="rk2-correlation-drift",
    ),
    Template(
        "decay-and-limit-report",
        "Decay and limit report",
        card("16", "R3") + card("17", "P3"),
        "TP3",
        NODE,
        folder="dc-decay-and-limit-report",
    ),
    Template(
        "stress-tests", "Stress tests", card("16", "R5"), "TP3", NODE, folder="rk5-stress-tests"
    ),
    Template(
        "incident-post-mortem",
        "Incident post-mortem",
        card("16", "R8"),
        "TP3",
        NODE,
        folder="rk8-incident-post-mortem",
    ),
    Template(
        "portfolio-combination-study",
        "Portfolio combination study",
        card("17", "P1"),
        "TP3",
        ("trading-node", "risk-session"),
        folder="p1-portfolio-combination",
    ),
    Template(
        "daily-book-report",
        "Daily book report",
        card("17", "P2"),
        "TP3",
        ("broker-read-token",),
        folder="p2-daily-book-report",
    ),
    Template(
        "change-bundle-for-approval",
        "Bundle a change for me to approve",
        card("16", "T6") + card("17", "P4"),
        "TP3",
        ("trading-node", "risk-session"),
        folder="pp-proposal-pack",
    ),
    Template(
        "strategy-idea-to-paper-tested",
        "Turn a strategy idea into a tested strategy, ending on paper",
        card("17", "D2", "D3"),
        "TP4",
        QMB,
        folder="b-build-and-prove",
    ),
    Template(
        "source-to-a-lab-test",
        "Source to a Lab test",
        card("15", "R3") + card("16", "T8"),
        "TP4",
        QMB,
        folder="rs3-source-to-lab-test",
    ),
    Template(
        "hypotheses-from-dead-ends",
        "Hypotheses from dead ends",
        card("15", "R6"),
        "TP4",
        ("real-library",),
        folder="rs6-hypotheses-from-dead-ends",
        triggers=(Cron("0 5 * * 1", "UTC"),),
    ),
    Template(
        "question-over-a-large-table",
        "Answer a question over a large table",
        card("15", "R8"),
        "TP4",
        ("rlm",),
        folder="rs8-big-data-question",
    ),
    Template(
        "first-backtest-from-an-idea",
        "Get a first backtest result from an idea",
        card("17", "L1"),
        "TP4",
        QMB,
        folder="l1-idea-to-first-result",
    ),
    Template(
        "overnight-lab-loop",
        "Overnight Lab loop",
        card("17", "L4"),
        "TP4",
        QMB,
        folder="l4-overnight-lab-loop",
        triggers=(Cron("0 23 * * *", "Europe/London"),),
    ),
    Template(
        "build-a-component-or-indicator",
        "Build a component or indicator",
        card("17", "D1", "D5"),
        "TP4",
        ("sandbox",),
        folder="bc-build-a-component",
    ),
    Template(
        "iterate-against-qmb-with-overfit-guards",
        "Iterate against QMB with overfit guards",
        card("17", "D3"),
        "TP4",
        QMB,
        folder="d3-iterate-against-qmb",
    ),
    Template(
        "variant-generation-and-comparison",
        "Variant generation and comparison",
        card("17", "D4"),
        "TP4",
        QMB,
        folder="d4-variant-comparison",
    ),
    Template(
        "ml-training-run-with-a-holdout",
        "ML training run with a holdout",
        card("17", "D6"),
        "TP4",
        ("qmb-door", "sandbox"),
        folder="d6-ml-training-run",
    ),
    Template(
        "mini-app-lifecycle",
        "Mini app lifecycle",
        card("17", "D7", "D8"),
        "TP4",
        ("sandbox", "app-op"),
        folder="ma-mini-app-lifecycle",
    ),
    Template(
        "connect-mini-apps",
        "Connect one mini app's output to another",
        card("17", "D9"),
        "TP4",
        ("app-op",),
        folder="d9-mini-app-pipeline",
    ),
    Template(
        "revolution-loop",
        "Loop a subworkflow until the idea plateaus",
        card("44", "DC-11"),
        "TPL3",
        folder="revolution-loop",
        test_inputs={"fixture": "first-pass"},
        test_cost="TPL3 lane 2: 3 haiku turns, tokens in 6, out 15, cache read 8852; 38 s",
    ),
    Template(
        "ask-the-panel",
        "Ask several model families and show the spread",
        card("46", "K-11"),
        "TPL3",
        folder="ask-the-panel",
        test_inputs={"fixture": "recorded"},
        test_cost="TPL3 lane 2: 4 haiku turns, tokens in 8, out 20, cache read 13633; 41 s",
    ),
    Template(
        "clippings-into-research",
        "Turn new clippings into linked research",
        card("46", "K-31"),
        "TPL3",
        folder="clippings-into-research",
        test_inputs={"fixture": True},
        test_cost="TPL3 lane 2: 1 haiku turn, tokens in 2, out 1, cache read 3888; 27 s",
    ),
    Template(
        "morning-digest",
        "Morning digest of everything since you last looked",
        card("46", "K-32"),
        "TPL3",
        folder="morning-digest",
        triggers=(Cron("0 7 * * *", "Europe/London"),),
        test_inputs={"fixture": True},
        test_cost="TPL3 lane 2: 1 haiku turn, tokens in 2, out 4, cache read 2531; 34 s",
    ),
    Template(
        "crystallise-a-workflow",
        "Replace a settled agent step with a script",
        card("46", "K-19"),
        "TPL3",
        folder="crystallise-a-workflow",
        test_inputs={"fixture": True},
        test_cost="TPL3 lane 2: 1 haiku turn, tokens in 2, out 5, cache read 5122; 13 s",
    ),
    Template(
        "run-one-job-on-his-server",
        "Run one job on his server",
        card("46", "5.0"),
        "REM",
        needs=SANDBOX,
        folder="run-on-a-machine",
        test_inputs={"command": ["python", "-c", "print(42)"]},
    ),
    Template(
        "backup-weekly",
        "Weekly backup",
        card("46", "G13"),
        "RUN1C",
        folder="backup-weekly",
        triggers=(Cron("0 6 * * 1", "UTC"),),
        test_inputs={"dry_run": True},
    ),
)

ALIASES: Final[dict[str, str]] = {
    "rs1": "paper-scout-to-research-note",
    "t3": "news-and-macro-calendar-watch",
    "rs0": "rough-idea-to-test-plan",
    "rs2": "source-to-component-card",
    "rs4": "literature-review-on-a-topic",
    "a": "video-to-strategy-ideas",
    "rv": "weekly-review",
    "db": "morning-market-brief",
    "t4": "research-desk-overnight",
    "ev": "copilot-eval-battery",
    "dm": "demo-trades-fill-quality",
    "t7": "trade-journal-in-risk-units",
    "gw": "trading-guards-alive",
    "rk2": "correlation-and-exposure-drift",
    "dc": "decay-and-limit-report",
    "rk5": "stress-tests",
    "rk8": "incident-post-mortem",
    "p1": "portfolio-combination-study",
    "p2": "daily-book-report",
    "pp": "change-bundle-for-approval",
    "b": "strategy-idea-to-paper-tested",
    "rs3": "source-to-a-lab-test",
    "rs6": "hypotheses-from-dead-ends",
    "rs8": "question-over-a-large-table",
    "l1": "first-backtest-from-an-idea",
    "l4": "overnight-lab-loop",
    "bc": "build-a-component-or-indicator",
    "d3": "iterate-against-qmb-with-overfit-guards",
    "d4": "variant-generation-and-comparison",
    "d6": "ml-training-run-with-a-holdout",
    "ma": "mini-app-lifecycle",
    "d9": "connect-mini-apps",
    "rs1-paper-scout": "paper-scout-to-research-note",
    ("t3-news-calendar-watch"): "news-and-macro-calendar-watch",
    ("rs0-idea-grill"): "rough-idea-to-test-plan",
    ("rs2-source-to-component-card"): "source-to-component-card",
    ("rs4-literature-review"): "literature-review-on-a-topic",
    ("a-fill-the-library"): "video-to-strategy-ideas",
    ("rv-weekly-review"): "weekly-review",
    ("db-desk-brief"): "morning-market-brief",
    ("t4-research-desk-overnight"): "research-desk-overnight",
    ("ev-copilot-eval-battery"): "copilot-eval-battery",
    ("dm-demo-monitor"): "demo-trades-fill-quality",
    ("t7-trade-journal-review"): "trade-journal-in-risk-units",
    ("gw-guard-watchdogs"): "trading-guards-alive",
    ("rk2-correlation-drift"): "correlation-and-exposure-drift",
    ("dc-decay-and-limit-report"): "decay-and-limit-report",
    ("rk5-stress-tests"): "stress-tests",
    ("rk8-incident-post-mortem"): "incident-post-mortem",
    ("p1-portfolio-combination"): "portfolio-combination-study",
    ("p2-daily-book-report"): "daily-book-report",
    ("pp-proposal-pack"): "change-bundle-for-approval",
    ("b-build-and-prove"): "strategy-idea-to-paper-tested",
    ("rs3-source-to-lab-test"): "source-to-a-lab-test",
    ("rs6-hypotheses-from-dead-ends"): "hypotheses-from-dead-ends",
    ("rs8-big-data-question"): "question-over-a-large-table",
    ("l1-idea-to-first-result"): "first-backtest-from-an-idea",
    ("l4-overnight-lab-loop"): "overnight-lab-loop",
    ("bc-build-a-component"): "build-a-component-or-indicator",
    ("d3-iterate-against-qmb"): "iterate-against-qmb-with-overfit-guards",
    ("d4-variant-comparison"): "variant-generation-and-comparison",
    ("d6-ml-training-run"): "ml-training-run-with-a-holdout",
    ("ma-mini-app-lifecycle"): "mini-app-lifecycle",
    ("d9-mini-app-pipeline"): "connect-mini-apps",
}
"""Every id the pack answered to before TPL1, to the plain id it answers to now. The key is
casefolded, so `RS1` and `rs1` both find it."""

BY_ID: Final[dict[str, Template]] = {
    name: template for template in CATALOG for name in (template.id, template.folder) if name
}

ALL_BUILT: Final = tuple(str(t.folder) for t in CATALOG)


def find(template_id: str) -> Template:
    """The template that id names, by its plain id, its folder, or any id it had before TPL1."""
    wanted = template_id.strip().casefold()
    found = BY_ID.get(wanted)
    if found is not None:
        return found
    renamed = ALIASES.get(wanted)
    if renamed is None:
        raise KeyError(template_id)
    return BY_ID[renamed]
