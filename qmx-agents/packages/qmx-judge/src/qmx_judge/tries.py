"""The try ledger: one append-only `try` item per counted try (Level 0 AD-25, Part B AD-207).

A run writes two items, never one item edited: the `opened` try when the lander opens it and a
`landed` or `failed` try when it closes, linking back to the first. Each is written once by one
writer, so concurrent runs share no record, and family counts are a query over `try` items.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal

__all__ = ["TRY_KIND", "Try", "TryKind", "TryState", "try_item"]

TRY_KIND: Final = "try"

type TryKind = Literal["run", "check", "spec_edit", "shortlist", "paper_pick", "whatif_rerun"]
type TryState = Literal["opened", "landed", "failed", "recorded"]


def try_item(run_id: str, state: TryState) -> str:
    """The Library item of a run's opening or closing try, named by its run id so a retry
    finds it instead of writing a second one."""
    return f"try-{run_id}-{'opened' if state == 'opened' else 'closed'}"


@dataclass(frozen=True, slots=True)
class Try:
    kind: TryKind
    state: TryState
    run_id: str
    family: str
    unit: str
    principal: str
    at: str
    study: str | None = None
    market: str | None = None
    tester: Mapping[str, str] | None = None
    place: str | None = None
    links: tuple[str, ...] = ()

    def fields(self) -> dict[str, object]:
        """The item's fields, as the `try` kind file declares them."""
        found: dict[str, object] = {
            "kind": self.kind,
            "state": self.state,
            "run_id": self.run_id,
            "family": self.family,
            "unit": self.unit,
            "principal": self.principal,
            "at": self.at,
            "links": list(self.links),
        }
        optional = {
            "study": self.study,
            "market": self.market,
            "tester": None if self.tester is None else dict(self.tester),
            "place": self.place,
        }
        found.update({name: value for name, value in optional.items() if value is not None})
        return found
