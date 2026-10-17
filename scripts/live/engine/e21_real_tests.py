"""EP10 lane 2 (E21): a draft's test run uses a real cheap model; the fake switch spends nothing.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e21_real_tests.py`
Writes `evidence/ep10/<ENGINE_LOG_PREFIX>ep10-e21.log`. On a throwaway home whose only provider row
is OpenRouter's, the `one-llm` fixture is saved as a draft and test-run through the engine service.
The `triage` role resolves to its test-only OpenRouter row, the chat runs through the relay on the
key by reference, and the run lands on `refs/runs/<id>` with mode test. The draft is then test-run
again with the fake switch, and every relay journal must be byte-identical afterwards. No plan turn.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3

from common import Log
from llm_lanes import KIMI, ONE_LLM, PR, describe, harnessed, journals, openrouter_home, relay_usd
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.library_fake import library_path
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR


async def main() -> int:
    log = Log(PR, "ep10-e21")
    home = openrouter_home("e21")
    async with harnessed(home) as found:
        with EngineService.open(home, harness=HarnessAdapter(found.harness)) as svc:
            item = svc.drafts.put(None, Bundle.read(ONE_LLM), 0, caller=OPERATOR).item
            real = await svc.tests.run(item, caller=OPERATOR, inputs={"country": "Japan"})
            log(f"real test run {real.run_id}: {real.status} {real.reason or ''}")
            tested = svc.drafts.state(item)
            before = journals(home)
            fake = await svc.tests.run(item, caller=OPERATOR, fake=True)
            log(f"fake test run {fake.run_id}: {fake.status} {fake.reason or ''}")
            after = journals(home)
    with Reader.open(home) as reader:
        real_spans = [s for s in reader.spans(real.run_id) if s.profile is not None]
        fake_spans = [s for s in reader.spans(fake.run_id) if s.profile is not None]
        outputs = [
            e.data.get("outputs")
            for e in reader.events(real.run_id)
            if e.kind == "node_finished" and e.data.get("node_id") == "capital"
        ]
    for span in (*real_spans, *fake_spans):
        log(f"span {describe(span)}")
    log(f"real run outputs: {outputs}")
    with sqlite3.connect(library_path(home)) as db:
        rows = db.execute(
            "SELECT kind, ref, fields FROM objects WHERE ref = ?", (f"refs/runs/{real.run_id}",)
        ).fetchall()
    summaries = [json.loads(fields) for kind, _, fields in rows if kind == "workflow-run"]
    log(f"objects on refs/runs/{real.run_id}: {[(k, r) for k, r, _ in rows]}")
    summary = summaries[-1] if summaries else {}
    log.check(
        "the draft test run resolved the cheap OpenRouter row and passed",
        real.status == "passed"
        and [(s.profile, s.model, s.status) for s in real_spans] == [("openrouter", KIMI, "ok")],
        [(s.profile, s.model, s.status, s.tokens) for s in real_spans],
    )
    log.check(
        "the run wrote its summary on refs/runs/<id> with mode test",
        (summary.get("mode"), summary.get("status")) == ("test", "passed"),
        {k: summary.get(k) for k in ("mode", "status", "object_id")},
    )
    log.check(
        "the passed real test run made the draft tested",
        tested == "tested",
        tested,
    )
    log.check(
        "the fake rerun passed on the fake provider and left every relay journal unchanged",
        fake.status == "passed" and [s.profile for s in fake_spans] == ["fake"] and before == after,
        {"journals": len(before), "changed": sorted(set(before.items()) ^ set(after.items()))},
    )
    log(f"OpenRouter spend estimate (upper bound): ${relay_usd(home):.4f}")
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
