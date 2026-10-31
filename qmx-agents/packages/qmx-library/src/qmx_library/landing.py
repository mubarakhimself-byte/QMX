"""The standing landing rule (Library AD-18, rulings 57 and 80): nothing a run made waits for him
unless it must.

When a run ends `passed`, the engine (`engine:<store>`) moves what the run put on
`refs/runs/<run_id>`, one item at a time, by its kind's class:

- `record` (results, artifacts, notes, memory rows, the run itself) fast-forwards onto `main`,
  only for a `live` run of a workflow whose standing rule is `publish = auto`;
- `definition` and `governed` (workflows, agents, books and the rest) land on
  `refs/drafts/<item>` and wait for his one yes; `main` never moves for them here.

A run that did not pass lands nothing. A non-fast-forward never picks a side: it becomes a
`merge-conflict` object and the run's other objects still land.

A store that is not primary refuses `main` with `not_primary` (the server before the flip,
WU9). That record is not lost and nothing raises: it stays on `refs/runs/<run_id>` and its row
says `deferred` with the refusal as its reason, so the run still ends and its links are
still written.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from qmx_library.port import LibraryRefused, MergeResult, ObjectId
from qmx_library.principal import MAIN, drafts_ref, runs_ref
from qmx_library.store import Store

type Mode = Literal["live", "test", "unknown"]
"""`unknown` is an imported run whose record never said live or test; like a test run, its records
never land on `main`."""

NOT_PRIMARY: Final = "not_primary"
"""The refusal of a store that may not move `main` because another store is primary."""


@dataclass(frozen=True, slots=True)
class Deferred:
    """An item this store may not land because another store is primary: it stays on its run
    ref, at `object_id`."""

    object_id: ObjectId
    reason: str
    outcome: Literal["deferred"] = "deferred"


@dataclass(frozen=True, slots=True)
class Landed:
    item: str
    into: str
    result: MergeResult | Deferred


def land(
    store: Store, run_id: str, *, mode: Mode, status: str, publish: str = "auto"
) -> list[Landed]:
    if status != "passed":
        return []
    landed: list[Landed] = []
    source = runs_ref(run_id)
    for item, head in store.heads_on(source):
        klass = store.get(store.engine, head).klass
        if klass == "record":
            if mode != "live" or publish != "auto":
                continue
            into = MAIN
        else:
            into = drafts_ref(item)
        try:
            result = store.merge(store.engine, item, from_ref=source, into=into, strategy="ff-only")
        except LibraryRefused as refused:
            if refused.code != NOT_PRIMARY:
                raise
            landed.append(Landed(item, into, Deferred(head, str(refused))))
            continue
        landed.append(Landed(item, into, result))
    return landed
