"""EP8 lane 2 (E11): the failure ladder on the real runner and ledger.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e11_ladder.py`
Writes `evidence/ep8/<ENGINE_LOG_PREFIX>ep8-e11.log`. One `llm` node on the `writer` role (two
candidates, `claude/sonnet` then `gpt`) always fails retryably, each time with a different message;
the doctor is a stub that answers `logic`. The `llm` executor is a planted in-process stub, since
the real one lands in EP10, and the run starts from the parsed definition for the same reason. No
model, no key, no ship home.
"""

from __future__ import annotations

import asyncio
from typing import Final

from common import Log, throwaway_home
from qmx_engine.definition.folder import load
from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Ledger
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult
from qmx_engine.runner import Consult, Engine, Outcome, Verdict
from qmx_engine.settings import DEFAULTS
from x07_nodes import edge, events, node, write_folder

MESSAGES: Final = ("timeout talking upstream", "connection reset", "bad gateway", "rate limited")
EXPECTED: Final = ["retry", "retry", "account", "model", "doctor", "park"]


class AlwaysFails:
    def __init__(self) -> None:
        self.jobs: list[NodeJob] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.jobs.append(job)
        message = MESSAGES[min(job.attempt, len(MESSAGES)) - 1]
        return Failed("upstream", message, signature("upstream", message), retryable=True)


class LogicDoctor:
    def __init__(self) -> None:
        self.asked = 0

    async def classify(self, consult: Consult) -> Verdict:
        self.asked += 1
        return Verdict("logic")


def main() -> int:
    log = Log("ep8", "ep8-e11")
    home = throwaway_home("ep8", "e11")
    write = node("write", "llm")
    write |= {"role": "writer", "retry": {"max_tries": 3, "backoff_seconds": [0, 0]}}
    root = write_folder(
        home / "wf-ladder",
        [node("start", "trigger"), write],
        {"start": {"main": [edge("write")]}},
        {},
    )
    definition = Workflow.model_validate(load(root).document)
    llm, doctor = AlwaysFails(), LogicDoctor()

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS, executors={"llm": llm}, doctor=doctor)
            return await engine.start(root, definition, mode="test", inputs=None)

    outcome = asyncio.run(go())
    ladder = [e.data for e in events(home, outcome.run_id) if e.kind == "ladder_step"]
    for step in ladder:
        extra = step.get("candidate") or step.get("resume_at") or ""
        log(f"ladder_step attempt {step.get('attempt')} {step['step']}: {step['reason']} {extra}")
    names = [str(s["step"]) for s in ladder]
    shown = [f"{n} skipped" if s.get("skipped") else n for n, s in zip(names, ladder, strict=True)]
    log(f"ladder_step events: {' '.join(shown)}")
    log(
        f"ladder: {' '.join(n for n, s in zip(names, ladder, strict=True) if not s.get('skipped'))}"
    )
    log(
        f"attempts {[(j.attempt, j.resolved_model) for j in llm.jobs]}; doctor asked {doctor.asked}"
    )
    log(f"run {outcome.status}: {outcome.reason}")
    log.check("ladder steps read retry retry account model doctor park", names == EXPECTED, names)
    log.check(
        "the account step is skipped: no pool",
        ladder[2].get("reason") == "skipped: no pool",
        ladder[2],
    )
    log.check(
        "the model step takes the role's next candidate",
        ladder[3].get("candidate") == "gpt",
        ladder[3],
    )
    log.check(
        "the attempt after the model step asks for gpt",
        [j.resolved_model for j in llm.jobs][-1] == {"candidate": "gpt"},
        llm.jobs[-1].resolved_model,
    )
    log.check("the doctor was asked once", doctor.asked == 1, doctor.asked)
    log.check("the run ends failed (parked)", outcome.status == "failed", outcome.status)
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
