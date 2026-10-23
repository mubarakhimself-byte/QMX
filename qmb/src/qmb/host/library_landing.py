"""One result shape: every finished backtest lands as one `backtest-result` (Library AD-29).

QMB writes result files; this is the one step that puts a finished result into the Library, so
no caller invents a second shape, and no caller links its own edges. It runs after QMB finishes
and carries QMB's ledger line and CT-32 artifact verbatim, with three edges:

- ``consumed`` to the dataset card version the backtest read;
- ``uses`` to the bot version it ran;
- ``tests`` to a hypothesis, when one is named.

The trade and equity tables travel inside the result's report blob, so a backtest of millions of
rows stays one object instead of a row per item. Everything else about the object's fields is the
kind's own schema: this step validates nothing twice, so a field the kind does not allow is
refused where kinds are enforced.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Protocol

__all__ = [
    "BASE_PRINCIPAL",
    "REPORT_SLOT",
    "BacktestLanding",
    "BacktestResult",
    "LandingPort",
    "Stored",
    "land",
]

BASE_PRINCIPAL: Final[str] = "qmb:backtest"
"""Who puts a backtest result: QMB's own run, not the agent that asked for it."""

REPORT_SLOT: Final[str] = "report"
"""The one blob slot a `backtest-result` kind declares today."""


@dataclass(frozen=True, slots=True)
class Stored:
    """What the Library answered when the object landed."""

    object_id: str


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """One finished QMB backtest, as the landing step receives it.

    ``report`` is the ledger line and the CT-32 artifact verbatim, with the trade and equity
    tables inside it. ``outcome`` is the kind's own word (``supports | refutes | inconclusive``)
    when the run had one to claim.
    """

    run_id: str
    title: str
    summary: str
    world: str
    claim_class: str
    role: str
    fidelity: str
    provenance: Mapping[str, object]
    report: bytes
    outcome: str | None = None
    memo_key: str | None = None


class LandingPort(Protocol):
    """The Library, as this step needs it: one put, then one link per edge."""

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
    ) -> Stored: ...

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str: ...


@dataclass(frozen=True, slots=True)
class BacktestLanding:
    """The object that landed and the edges written from it, in order."""

    object_id: str
    edges: tuple[tuple[str, str], ...]


def land(
    result: BacktestResult,
    library: LandingPort,
    *,
    consumed: str,
    uses: str,
    tests: str | None = None,
    principal: str = BASE_PRINCIPAL,
) -> BacktestLanding:
    """Store one `backtest-result` and link it to its data, its bot and its hypothesis.

    ``consumed`` is the dataset card version the backtest read, ``uses`` the bot version it ran,
    and ``tests`` the hypothesis it was built to test. The result is stored under its QMB run id,
    so a rerun of the same run replaces nothing: QMB names a run by its own fingerprint.
    """
    fields: dict[str, object] = {
        "claim_class": result.claim_class,
        "fidelity": result.fidelity,
        "provenance": dict(result.provenance),
        "role": result.role,
        "world": result.world,
    }
    if result.outcome is not None:
        fields["outcome"] = result.outcome
    if result.memo_key is not None:
        fields["memo_key"] = result.memo_key
    stored = library.put(
        "backtest-result",
        fields,
        {REPORT_SLOT: result.report},
        item=result.run_id,
        title=result.title,
        summary=result.summary,
        principal=principal,
    )
    written: list[tuple[str, str]] = []
    for relation, target in (("consumed", consumed), ("uses", uses), ("tests", tests)):
        if target is None:
            continue
        library.link(stored.object_id, relation, target, principal=principal)
        written.append((relation, target))
    return BacktestLanding(stored.object_id, tuple(written))
