"""SEC1A lanes (E37): nothing the engine stores or serves carries a secret (AD-37), a node names
only a `qmx/tool/<name>` key, and only a version on `main` runs live.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e37_redaction.py [lane ...]`
Lanes are `e37 refs published grep script spans`; none named runs all, in that order (`grep` and
`spans` read the home `e37` leaves). Each writes
`D:/QMX-worktrees/qma-ship/build/evidence/sec1a/<ENGINE_LOG_PREFIX>sec1a-<lane>.log`.

Every key here is a planted fake built at run time; no lane reads a real secret, a keyring entry,
a model or the ship home.

- `e37` (lane 2): a provider failure echoing `key_sk-or-v1-...` is answered by an in-process
  stub (no provider call, as in E12), so the executor redacts nothing and the seams must. Pass when
  the ledger, the inbox title and cause, `explain`, REST (explain, inbox, run list) and the run
  summary in the Library all show `[redacted...]` and never the key.
- `refs` (lane 3): `python -m qmx_engine validate` on a folder whose node names `qmx/ctrader`.
- `published` (lane 4): `runs.start` on a draft and on a workflow object on a run's ref.
- `grep` (lane 5): the planted key is in no file under the `e37` home.
- `script` (lane 6): a real script prints a key on stdout, another on stderr before it fails.
- `spans` (lane 7): the `e37` run's spans count their redactions.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final

from common import Log
from fastapi.testclient import TestClient
from qmx_control import ControlService, create_app
from qmx_engine.control_door import EngineDoor
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult
from qmx_engine.ports.library import Bundle, runs_ref
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.runner import Engine, Outcome
from qmx_engine.service.api import EngineService, explain_run
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.service.rest import engine_router
from qmx_engine.settings import DEFAULTS
from qmx_engine.trace_export import export
from x07_nodes import cli, edge, events, node, run_id_of, runnable, write_folder

PR: Final = "sec1a"
BUILD: Final = Path("D:/QMX-worktrees/qma-ship/build")
BEARER: Final = {"Authorization": "Bearer e37-check"}
PLANTED: Final = "sk-or-" + "v1-" + "e37f" * 16
"""A fake OpenRouter-shaped key, glued to a word where it appears (`key_<planted>`)."""
MASK: Final = "[redacted"


class BuildLog(Log):
    def __init__(self, slug: str) -> None:
        folder = BUILD / "evidence" / PR
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}{PR}-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def home_of(slug: str, *, fresh: bool) -> Path:
    root = BUILD / "homes" / f"{PR}-{slug}"
    if fresh:
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True)
    return root


def clean(text: str) -> bool:
    return PLANTED not in text and MASK in text


class Unauthorized:
    """A provider that answers 401 and echoes the key it was sent, as a careless upstream does."""

    def run(self, job: NodeJob) -> NodeResult:
        message = f"upstream 401 Unauthorized for key_{PLANTED}"
        return Failed("auth", message, signature("auth", message), retryable=False)


@contextmanager
def served(home: Path) -> Iterator[TestClient]:
    control = ControlService(home)
    opened: list[EngineDoor] = []
    ready, stop = threading.Event(), threading.Event()

    async def main() -> None:
        async with EngineDoor.open(control) as door:
            opened.append(door)
            ready.set()
            while not stop.is_set():
                await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(main(),))
    thread.start()
    if not ready.wait(30):
        raise SystemExit("BLOCKED: the engine door did not open")
    try:
        bearer = BEARER["Authorization"].split()[1]
        app = create_app(control, bearer, extra_routers=[engine_router(opened[0])])
        with TestClient(app) as rest:
            yield rest
    finally:
        stop.set()
        thread.join(30)


def e37(log: Log) -> None:
    home = home_of("e37", fresh=True)
    root = write_folder(
        home / "wf-e37",
        [node("start", "trigger"), node("call", "script", script="scripts/call.py")],
        {"start": {"main": [edge("call")]}},
        {"call": "print(1)\n"},
    )
    definition = runnable(root)

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS, executors={"script": Unauthorized()})
            return await engine.start(root, definition, mode="test", inputs=None)

    outcome = asyncio.run(go())
    log(f"run {outcome.run_id} {outcome.status}: {outcome.reason}")
    with LibraryFake.open(home) as library:
        draft = library.put_draft("wf-e37", Bundle.read(root), 0, principal="operator")
        summary = export(
            home,
            outcome.run_id,
            library,
            workflow_item=draft.item,
            object_id=draft.object_id,
            mode="test",
            status=outcome.status,
            reason=outcome.reason,
            started_by="operator",
        )
        trace = library.get_artifact(str(summary.fields["trace_artifact_hash"]))
    failed = [e.data for e in events(home, outcome.run_id) if e.kind == "node_failed"]
    with InboxTable.open(home) as inbox:
        items = inbox.list_items(open_only=False)
    explained = json.dumps(explain_run(home, outcome.run_id))
    with served(home) as rest:
        over_rest = {
            "explain": rest.get(f"/api/workflow-runs/{outcome.run_id}/explain", headers=BEARER),
            "inbox": rest.get("/api/inbox", headers=BEARER),
            "runs": rest.get(
                "/api/workflow-runs", params={"workflow_id": draft.item}, headers=BEARER
            ),
        }

    log.check("the run parked on the provider failure", outcome.status == "failed", outcome.status)
    log.check(
        "ledger: the failure message is redacted",
        len(failed) == 1 and clean(str(failed[0].get("message"))),
        failed[0].get("message") if failed else None,
    )
    log.check(
        "inbox: one item, title and cause redacted",
        len(items) == 1
        and clean(items[0].title + " " + items[0].cause)
        and PLANTED not in items[0].title,
        [(i.title, i.cause) for i in items],
    )
    log.check("explain: redacted", clean(explained), f"{len(explained)} chars, key absent")
    for name, answer in over_rest.items():
        log.check(
            f"REST {name}: 200 and redacted",
            answer.status_code == 200 and clean(answer.text),
            f"{answer.status_code}, {len(answer.text)} chars",
        )
    log.check(
        "run summary in the Library: reason redacted",
        clean(str(summary.fields.get("reason"))),
        summary.fields.get("reason"),
    )
    log.check(
        "trace artifact: the key is absent",
        PLANTED.encode() not in trace,
        f"{len(trace)} bytes",
    )


def refs(log: Log) -> None:
    home = home_of("refs", fresh=True)
    call = node("call", "script", script="scripts/call.py") | {
        "credentials": {"broker": "qmx/ctrader", "search": "qmx/tool/serp"}
    }
    root = write_folder(
        home / "wf-refs",
        [node("start", "trigger"), call],
        {"start": {"main": [edge("call")]}},
        {"call": "print(1)\n"},
    )
    code, lines = cli(log, "validate", str(root))
    for line in lines:
        log(f"  {line}")
    log(f"file: {root / 'definition.json'}")
    log.check("validate exits 1", code == 1, code)
    log.check(
        "the broker ref is refused at its path, the tool key passes",
        lines
        == [
            "credential_not_tool_key nodes[1].credentials.broker a node names only a "
            "qmx/tool/<name> key; provider and broker keys never reach it"
        ],
        lines,
    )


def published(log: Log) -> None:
    home = home_of("published", fresh=True)
    root = write_folder(
        home / "wf-published",
        [node("start", "trigger"), node("one", "script", script="scripts/one.py")],
        {"start": {"main": [edge("one")]}},
        {"one": "import json\nprint(json.dumps(1))\n"},
    )
    with EngineService.open(home) as svc:
        draft = svc.drafts.put(None, Bundle.read(root), 0, caller=OPERATOR)
        library: Any = svc.ctx.library
        stored = library.get(draft.object_id)
        on_a_run = library._put(
            "workflow", draft.item, runs_ref("run-elsewhere"), dict(stored.fields),
            "run:run-elsewhere", stored.blob,
        )  # fmt: skip
        for label, object_id in (("draft", draft.object_id), ("run ref", on_a_run.object_id)):
            try:
                view = asyncio.run(svc.runs.start(object_id, caller=OPERATOR))
                log.check(f"a {label} version is refused", False, f"ran: {view.status}")
            except Refused as refused:
                log.check(
                    f"a {label} version is refused as not published",
                    refused.code == "run_refused" and " is draft;" in str(refused),
                    f"{refused.code}: {refused}",
                )
        asyncio.run(svc.tests.run(draft.item, caller=OPERATOR))
        version = svc.versions.publish(draft.item, "1.0.0", caller=OPERATOR)
        ran = asyncio.run(svc.runs.start(version, caller=OPERATOR))
    log.check("the version on main runs live", (ran.mode, ran.status) == ("live", "passed"), ran)


def grep(log: Log) -> None:
    home = home_of("e37", fresh=False)
    files = [p for p in home.rglob("*") if p.is_file()]
    if not files:
        raise SystemExit("BLOCKED: run the e37 lane first")
    hits = [str(p.relative_to(home)) for p in files if PLANTED.encode() in p.read_bytes()]
    log(f"{len(files)} files under {home}: {sorted(p.name for p in files)}")
    log.check("the planted key is in no file", hits == [], hits)


def script(log: Log) -> None:
    home = home_of("script", fresh=True)
    root = write_folder(
        home / "wf-script",
        [
            node("start", "trigger"),
            node("speak", "script", script="scripts/speak.py"),
            node("fail", "script", script="scripts/fail.py") | {"retry": {"max_tries": 1}},
        ],
        {"start": {"main": [edge("speak")]}, "speak": {"main": [edge("fail")]}},
        {
            "speak": f"import json\nprint(json.dumps({{'echo': 'token={PLANTED}'}}))\n",
            "fail": (
                "import sys\n"
                f"print('x' * 400 + ' key_{PLANTED} ' + 'y' * 250, file=sys.stderr)\n"
                "sys.exit(3)\n"
            ),
        },
    )
    code, lines = cli(log, "run", str(root), "--home", str(home))
    run_id = run_id_of(lines)
    found = events(home, run_id)
    outputs = [e.data for e in found if e.kind == "node_finished" and e.data["node_id"] == "speak"]
    failed = [e.data for e in found if e.kind == "node_failed" and e.data["node_id"] == "fail"]
    log(f"exit {code}: {lines[:2]}")
    log.check(
        "stdout: the output is stored redacted",
        len(outputs) == 1 and clean(json.dumps(outputs[0])),
        outputs[0].get("outputs") if outputs else None,
    )
    log.check(
        "stderr: the failure tail is redacted, not cut through the key",
        len(failed) >= 1
        and all(clean(m := str(f.get("message"))) and PLANTED[-12:] not in m for f in failed),
        [str(f.get("message"))[:60] for f in failed],
    )


def spans(log: Log) -> None:
    home = home_of("e37", fresh=False)
    with Reader.open(home) as reader:
        (run_id,) = {row[0] for row in reader.connection.execute("SELECT run_id FROM events")}
        found = reader.spans(run_id)
    counted = [(s.node_id, s.attempt, s.redactions) for s in found]
    log(f"spans of {run_id}: {counted}")
    log.check(
        "the failed attempt's span counts its redactions", any(n > 0 for *_, n in counted), counted
    )


LANES: Final[dict[str, Callable[[Log], None]]] = {
    "e37": e37,
    "refs": refs,
    "published": published,
    "grep": grep,
    "script": script,
    "spans": spans,
}


def main() -> int:
    chosen = sys.argv[1:] or list(LANES)
    code = 0
    for name in chosen:
        log = BuildLog(name)
        LANES[name](log)
        code |= log.verdict()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
