"""The copilot eval battery (engine AD-66): the `ev-copilot-eval-battery` template run on the model
a change concerns, beside the current one, with pass^3 per task for both.

A change of the copilot's default model runs the new model as the candidate and the current one
as the baseline, both on the current slot text. A persona, methodology or skill draft runs the
draft's slot text as the candidate and the published text as the baseline, both on the current
default model. Each side is one run of the template with its roles pinned (B-60): the tries'
`writer` role to the side's model, and `judge` to the first judge candidate of a family no graded
model is from, else labelled `same_family` (AD-13). A live battery runs the published
template; a test battery runs the pack's draft, which is how lanes and the template's own tests
run it. Nothing waits on a battery: the caller lands the result where the change card reads it.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, cast

from pydantic import JsonValue

from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.roles import Mode
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Caller, Refused
from qmx_engine.service.runs import run_bundle
from qmx_engine.templates.catalog import PACK
from qmx_engine.templates.install import current_draft

type JsonObject = dict[str, JsonValue]

ITEM: Final = "ev-copilot-eval-battery"
FOLDER: Final = PACK / ITEM
SUBJECT_ROLE: Final = "writer"
JUDGE_ROLE: Final = "judge"
FAMILIES: Final = (
    ("claude", "anthropic"),
    ("anthropic", "anthropic"),
    ("gpt", "openai"),
    ("openai", "openai"),
    ("kimi", "moonshot"),
    ("moonshot", "moonshot"),
    ("deepseek", "deepseek"),
    ("glm", "zhipu"),
    ("z-ai", "zhipu"),
    ("zhipu", "zhipu"),
    ("qwen", "qwen"),
    ("minimax", "minimax"),
    ("gemini", "google"),
    ("google", "google"),
)
"""Name prefixes to the vendor whose model it is. A gateway profile such as `openrouter` names no
family, so the model path is read first."""


def family(row: str) -> str:
    """The vendor family of a Settings row `profile/model[@effort]`, whichever profile serves it:
    `openrouter/deepseek/deepseek-chat` is `deepseek`, `claude/haiku` is `anthropic`."""
    parts = row.partition("@")[0].lower().split("/")
    for part in [*parts[1:], parts[0]]:
        for prefix, name in FAMILIES:
            if part.startswith(prefix):
                return name
    return parts[1] if len(parts) > 1 else parts[0]


@dataclass(frozen=True, slots=True)
class Judge:
    row: str
    same_family: bool


def judge_for(graded: Sequence[str], candidates: Sequence[str]) -> Judge:
    """The first judge candidate whose family no graded model shares; with none, the first
    candidate, labelled `same_family`."""
    if not candidates:
        raise Refused("no_judge", "the judge role has no candidate")
    taken = {family(row) for row in graded}
    other = next((row for row in candidates if family(row) not in taken), None)
    return Judge(other, False) if other is not None else Judge(candidates[0], True)


@dataclass(frozen=True, slots=True)
class Side:
    model: str
    """The Settings row the side's tries run on."""
    surface: str = ""
    """The persona, methodology and skills index text the tries work under."""

    @property
    def surface_digest(self) -> str:
        """sha256 over the slot text this side passed. The harness's AD-62 digest also covers the
        tool list, which a battery try does not have."""
        return hashlib.sha256(self.surface.encode()).hexdigest()


def _bundle(svc: EngineService, mode: Mode, caller: Caller) -> tuple[Bundle, str]:
    if mode == "live":
        versions = svc.versions.list(ITEM)
        if not versions:
            raise Refused("not_published", f"{ITEM} has no published version to run live")
        object_id = versions[-1].object_id
        return svc.ctx.library.get_object(object_id), object_id
    bundle = Bundle.read(FOLDER)
    draft = current_draft(svc, ITEM)
    if draft is None or draft.bundle != bundle:
        draft = svc.drafts.put(ITEM, bundle, 0 if draft is None else draft.revision, caller=caller)
    return bundle, draft.object_id


def _side(svc: EngineService, run_id: str, side: Side) -> JsonObject:
    with Reader.open(svc.ctx.home) as reader:
        events = reader.events(run_id)
        spans = reader.spans(run_id)
    delivered = [
        cast(JsonObject, e.data["outputs"])["main"]
        for e in events
        if e.kind == "node_finished" and e.data.get("node_id") == "deliver"
    ]
    report = cast(JsonObject, delivered[-1]) if delivered else {}

    def ran(role: str) -> list[JsonValue]:
        return [*sorted({f"{s.profile}/{s.model}" for s in spans if s.role == role and s.model})]

    return {
        "model": side.model,
        "family": family(side.model),
        "surface_digest": side.surface_digest,
        "run_id": run_id,
        "status": "passed" if delivered else "failed",
        "ran_on": ran(SUBJECT_ROLE),
        "judged_on": ran(JUDGE_ROLE),
        "passed": report.get("passed"),
        "total": report.get("total"),
        "tasks": report.get("tasks", []),
    }


async def run(
    svc: EngineService,
    tasks: Sequence[JsonValue],
    candidate: Side,
    baseline: Side,
    *,
    judges: Sequence[str],
    subject: str,
    mode: Mode = "live",
    caller: Caller = OPERATOR,
) -> JsonObject:
    """Both sides run at once; the result names, per task, pass^3 on each side."""
    judge = judge_for([candidate.model, baseline.model], judges)
    bundle, object_id = _bundle(svc, mode, caller)
    started = time.monotonic()

    async def one(side: Side) -> str:
        pins: JsonObject = {"roles": {SUBJECT_ROLE: side.model, JUDGE_ROLE: judge.row}}
        inputs: JsonObject = {"tasks": list(tasks), "surface": side.surface}
        outcome, _ = await run_bundle(
            svc.ctx,
            bundle,
            object_id=object_id,
            item=ITEM,
            mode=mode,
            inputs=inputs,
            subgraph=None,
            caller=caller,
            pins=pins,
        )
        return outcome.run_id

    ran = await asyncio.gather(one(candidate), one(baseline))
    pairs = zip(ran, (candidate, baseline), strict=True)
    sides = [_side(svc, run_id, side) for run_id, side in pairs]
    by_side = [
        {str(t["id"]): t["pass3"] for t in cast(list[JsonObject], s["tasks"])} for s in sides
    ]
    ids = [str(cast(JsonObject, t)["id"]) for t in tasks]
    return {
        "battery": ITEM,
        "subject": subject,
        "mode": mode,
        "judge": {"row": judge.row, "family": family(judge.row), "same_family": judge.same_family},
        "candidate": sides[0],
        "baseline": sides[1],
        "per_task": [
            {"id": i, "candidate": by_side[0].get(i), "baseline": by_side[1].get(i)} for i in ids
        ],
        "wall_s": round(time.monotonic() - started, 1),
    }
