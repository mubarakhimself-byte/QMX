"""The template pack's catalogue: the 31 templates and their needs, as ENGINE-PLAN Appendix I
lists them.

Each row names its plain name (ruling 35), the cards in research files 15, 16 or 17 it was built
from, what it waits for, and its folder. Since TP4 every row has one. A row with `needs` gets a
definition naming the same `meta.needs` and installs as a validated draft; any other row is tested
on real models and published disabled.
`test_cost` is what the row's test run cost when its PR measured it on the cheapest test
candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from pydantic import JsonValue

from qmx_engine.definition.model import Need
from qmx_engine.triggers.cron import Cron

type CardFile = Literal["15", "16", "17"]

PACK: Final = Path(__file__).resolve().parent
SHARED: Final = PACK / "_shared"


@dataclass(frozen=True, slots=True)
class Card:
    file: CardFile
    """`15-templates-researcher.md`, `16-templates-trader-risk.md` or `17-templates-dev-pm-lab.md`
    under `tracker/qma-v2/research/methodology/`."""
    card: str
    """The card's id in that file's headings, such as `R1` (file 16 reuses `R1` for a risk card)."""


@dataclass(frozen=True, slots=True)
class Template:
    id: str
    name: str
    cards: tuple[Card, ...]
    pr: str
    needs: tuple[Need, ...] = ()
    folder: str | None = None
    """The workflow folder under the pack, which is also the workflow's id."""
    triggers: tuple[Cron, ...] = ()
    """The card's schedule. Install adds each one disabled once the template is published; the
    manual kind is in the definition."""
    test_inputs: JsonValue = None
    test_cost: str | None = None


def card(file: CardFile, *ids: str) -> tuple[Card, ...]:
    return tuple(Card(file, found) for found in ids)


NODE: Final[tuple[Need, ...]] = ("trading-node",)
QMB: Final[tuple[Need, ...]] = ("qmb-door",)

CATALOG: Final[tuple[Template, ...]] = (
    Template(
        "RS1",
        "Paper scout to research note",
        card("15", "R1"),
        "TP1",
        folder="rs1-paper-scout",
        triggers=(Cron("0 */6 * * *", "UTC"),),
        test_inputs={"fixture": True},
        test_cost="TP1 lane 2: 5 Kimi spans; 47k in, 8k out, 86k cache read; 233 s",
    ),
    Template(
        "T3",
        "News and macro calendar watch",
        card("16", "T3"),
        "TP1",
        folder="t3-news-calendar-watch",
        triggers=(Cron("5 0 * * *", "UTC"),),
        test_inputs={"fixture": "surprise"},
        test_cost="TP1 lane 3: quiet day 0 tokens, 1 s; surprise day 1 Kimi span, 6k in, 1k out",
    ),
    Template(
        "RS0",
        "Idea grill to term sheet",
        card("15", "R0"),
        "TP2",
        folder="rs0-idea-grill",
        test_inputs={"fixture": True},
    ),
    Template(
        "RS2",
        "Source to component card",
        card("15", "R2", "R5", "R7"),
        "TP2",
        folder="rs2-source-to-component-card",
        test_inputs={"fixture": True},
    ),
    Template(
        "RS4",
        "Literature review on a topic",
        card("15", "R4", "R7"),
        "TP2",
        folder="rs4-literature-review",
        test_inputs={"fixture": True},
    ),
    Template(
        "A",
        "Fill the Library, funnel stages 1 to 7",
        card("15", "R5", "R7"),
        "TP2",
        folder="a-fill-the-library",
        test_inputs={"fixture": "one-video"},
    ),
    Template(
        "RV",
        "Weekly review",
        card("15", "R9") + card("17", "D10"),
        "TP2",
        folder="rv-weekly-review",
        triggers=(Cron("0 6 * * 1", "UTC"),),
        test_inputs={"fixture": True},
    ),
    Template(
        "DB",
        "Desk brief",
        card("16", "T1", "T2", "T10"),
        "TP3",
        folder="db-desk-brief",
        triggers=(
            Cron("0 6 * * 1-5", "Europe/London"),
            Cron("30 7 * * 1-5", "America/New_York"),
            Cron("5 17 * * 1-5", "America/New_York"),
        ),
        test_inputs={"fixture": "busy"},
    ),
    Template(
        "T4",
        "Research desk overnight",
        card("16", "T4"),
        "TP3",
        folder="t4-research-desk-overnight",
        triggers=(Cron("0 3 * * 0-4", "Europe/London"),),
        test_inputs={"fixture": True},
    ),
    Template(
        "DM",
        "Demo monitor and execution quality",
        card("16", "T5", "T9"),
        "TP3",
        NODE,
        folder="dm-demo-monitor",
    ),
    Template(
        "T7",
        "Trade journal review in R",
        card("16", "T7"),
        "TP3",
        NODE,
        folder="t7-trade-journal-review",
    ),
    Template(
        "GW", "Guard watchdogs", card("16", "R1", "R6"), "TP3", NODE, folder="gw-guard-watchdogs"
    ),
    Template(
        "RK2",
        "Correlation and exposure drift",
        card("16", "R2"),
        "TP3",
        NODE,
        folder="rk2-correlation-drift",
    ),
    Template(
        "DC",
        "Decay and limit report",
        card("16", "R3") + card("17", "P3"),
        "TP3",
        NODE,
        folder="dc-decay-and-limit-report",
    ),
    Template("RK5", "Stress tests", card("16", "R5"), "TP3", NODE, folder="rk5-stress-tests"),
    Template(
        "RK8",
        "Incident post-mortem",
        card("16", "R8"),
        "TP3",
        NODE,
        folder="rk8-incident-post-mortem",
    ),
    Template(
        "P1",
        "Portfolio combination study",
        card("17", "P1"),
        "TP3",
        ("trading-node", "risk-session"),
        folder="p1-portfolio-combination",
    ),
    Template(
        "P2",
        "Daily book report",
        card("17", "P2"),
        "TP3",
        ("broker-read-token",),
        folder="p2-daily-book-report",
    ),
    Template(
        "PP",
        "Proposal pack he signs",
        card("16", "T6") + card("17", "P4"),
        "TP3",
        ("trading-node", "risk-session"),
        folder="pp-proposal-pack",
    ),
    Template(
        "B",
        "Build and prove, funnel stages 8 to 12",
        card("17", "D2", "D3"),
        "TP4",
        QMB,
        folder="b-build-and-prove",
    ),
    Template(
        "RS3",
        "Source to a Lab test",
        card("15", "R3") + card("16", "T8"),
        "TP4",
        QMB,
        folder="rs3-source-to-lab-test",
    ),
    Template(
        "RS6",
        "Hypotheses from dead ends",
        card("15", "R6"),
        "TP4",
        ("real-library",),
        folder="rs6-hypotheses-from-dead-ends",
        triggers=(Cron("0 5 * * 1", "UTC"),),
    ),
    Template(
        "RS8",
        "Big-data question",
        card("15", "R8"),
        "TP4",
        ("rlm",),
        folder="rs8-big-data-question",
    ),
    Template(
        "L1", "Idea to first result", card("17", "L1"), "TP4", QMB, folder="l1-idea-to-first-result"
    ),
    Template(
        "L4",
        "Overnight Lab loop",
        card("17", "L4"),
        "TP4",
        QMB,
        folder="l4-overnight-lab-loop",
        triggers=(Cron("0 23 * * *", "Europe/London"),),
    ),
    Template(
        "BC",
        "Build a component or indicator",
        card("17", "D1", "D5"),
        "TP4",
        ("sandbox",),
        folder="bc-build-a-component",
    ),
    Template(
        "D3",
        "Iterate against QMB with overfit guards",
        card("17", "D3"),
        "TP4",
        QMB,
        folder="d3-iterate-against-qmb",
    ),
    Template(
        "D4",
        "Variant generation and comparison",
        card("17", "D4"),
        "TP4",
        QMB,
        folder="d4-variant-comparison",
    ),
    Template(
        "D6",
        "ML training run with a holdout",
        card("17", "D6"),
        "TP4",
        ("qmb-door", "sandbox"),
        folder="d6-ml-training-run",
    ),
    Template(
        "MA",
        "Mini app lifecycle",
        card("17", "D7", "D8"),
        "TP4",
        ("sandbox", "app-op"),
        folder="ma-mini-app-lifecycle",
    ),
    Template(
        "D9",
        "Mini-app-to-mini-app pipeline",
        card("17", "D9"),
        "TP4",
        ("app-op",),
        folder="d9-mini-app-pipeline",
    ),
)

ALL_BUILT: Final = tuple(str(t.folder) for t in CATALOG)
CALIBRATED: Final = ("rs2-source-to-component-card", "rs4-literature-review", "a-fill-the-library")

SHARED_COPIES: Final[dict[str, tuple[str, ...]]] = {
    "preflight/scripts/new_ids.py": ("rs1-paper-scout/scripts/new_ids.py",),
    "paper-read/prompts/read.md": ("rs1-paper-scout/prompts/read.md",),
    "paper-read/schemas/cards.json": ("rs1-paper-scout/schemas/cards.json",),
    "research-harness/scripts/citation_check.py": (
        "rs1-paper-scout/scripts/citation_check.py",
        "rs4-literature-review/scripts/citation_check.py",
        "_shared/understand-extract/scripts/citation_check.py",
        "rs2-source-to-component-card/scripts/citation_check.py",
        "a-fill-the-library/scripts/citation_check.py",
        "t4-research-desk-overnight/scripts/citation_check.py",
        "rk8-incident-post-mortem/scripts/citation_check.py",
        "rs3-source-to-lab-test/scripts/citation_check.py",
    ),
    "render-and-grade/scripts/render_and_grade.py": tuple(
        f"{t}/scripts/render_and_grade.py" for t in ALL_BUILT
    ),
    "render-and-grade/scripts/stop.py": tuple(f"{t}/scripts/stop.py" for t in ALL_BUILT),
    "render-and-grade/scripts/deliver.py": tuple(
        f"{t}/scripts/deliver.py" for t in ALL_BUILT if t != "a-fill-the-library"
    ),
    "overfit-gates/scripts/deflated_sharpe.py": tuple(
        f"{t}/scripts/deflated_sharpe.py"
        for t in (
            "b-build-and-prove",
            "l4-overnight-lab-loop",
            "d3-iterate-against-qmb",
            "d4-variant-comparison",
        )
    ),
    "understand-extract/scripts/sections.py": (
        "rs2-source-to-component-card/scripts/sections.py",
        "a-fill-the-library/scripts/sections.py",
    ),
    "understand-extract/prompts/sections.md": (
        "rs2-source-to-component-card/prompts/sections.md",
        "a-fill-the-library/prompts/sections.md",
    ),
    "understand-extract/schemas/claims.json": (
        "rs2-source-to-component-card/schemas/claims.json",
        "a-fill-the-library/schemas/claims.json",
    ),
    "understand-extract/scripts/card_holes.py": ("a-fill-the-library/scripts/card_holes.py",),
    "understand-extract/prompts/extract.md": ("a-fill-the-library/prompts/extract.md",),
    "understand-extract/schemas/cards.json": ("a-fill-the-library/schemas/cards.json",),
    **{
        f"calibrate/{name}": tuple(f"{t}/{name}" for t in CALIBRATED)
        for name in (
            "scripts/basis.py",
            "scripts/agreement.py",
            "prompts/sample.md",
            "schemas/votes.json",
        )
    },
}
"""Each shared block file, under `_shared/`, to its copies in the templates. A run holds only its
own folder's files, so a template carries a byte-identical copy of each block file it uses."""


def find(template_id: str) -> Template:
    for template in CATALOG:
        if template.id == template_id:
            return template
    raise KeyError(template_id)
