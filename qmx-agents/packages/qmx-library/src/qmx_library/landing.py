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
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from qmx_library.port import MergeResult
from qmx_library.principal import MAIN, drafts_ref, runs_ref
from qmx_library.store import Store

type Mode = Literal["live", "test"]


@dataclass(frozen=True, slots=True)
class Landed:
    item: str
    into: str
    result: MergeResult


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
        result = store.merge(store.engine, item, from_ref=source, into=into, strategy="ff-only")
        landed.append(Landed(item, into, result))
    return landed
