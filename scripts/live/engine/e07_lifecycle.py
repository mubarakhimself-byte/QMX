"""EP9's lifecycle lanes: the AD-11 states through the engine service, on real script runs of the
`script-chain` fixture and the fake Library in a throwaway home.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e07_lifecycle.py [lane]`
Lanes are `e07 stale subgraph publish-enable settings archive refs`; none named runs all. Each
writes `evidence/ep9/<ENGINE_LOG_PREFIX>ep9-<lane>.log`, and the script exits 1 if any lane failed.

- `e07` (lane 2): `runs.start` on a draft is refused, `tests.run` on it finishes on script nodes,
  and enabling a version with no passing run for its hash is refused.
- `stale` (lane 5), `subgraph` (lane 6), `publish-enable` (lane 7), `settings` (lane 8),
  `archive` (lane 9) and `refs` (lane 10) are the plan's menu lanes of the same names.

No model, no key, no ship home.
"""

from __future__ import annotations

import asyncio
import sqlite3
import sys
from collections.abc import Callable
from typing import Any, Final, cast

from common import Log, throwaway_home
from qmx_control.models import Document
from qmx_control.service import ControlService, SettingsSection
from qmx_engine.ports.library import Bundle, drafts_ref
from qmx_engine.ports.library_fake import library_path
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused
from x07_nodes import CHAIN, events

EDIT: Final = (
    b'import json, sys\nprint(json.dumps({"total": sum(json.load(sys.stdin)["in"]) + 1}))\n'
)


def refusal(log: Log, name: str, code: str, call: Callable[[], object]) -> None:
    try:
        call()
    except Refused as refused:
        log.check(name, refused.code == code, str(refused))
        return
    log.check(name, False, "not refused")


def e07(log: Log) -> None:
    home = throwaway_home("ep9", "e07")
    with EngineService.open(home) as svc:
        draft = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR)
        state = svc.drafts.state(draft.item)
        log(f"draft {draft.item} revision {draft.revision} on {draft.ref}: {state}")
        refusal(
            log,
            "runs.start on a draft is refused",
            "run_refused",
            lambda: asyncio.run(svc.runs.start(draft.object_id, caller=OPERATOR)),
        )
        untested = svc.ctx.library.publish(
            draft.item, drafts_ref(draft.item), "0.1.0", principal="operator"
        )
        log(f"version {untested} published straight through the Library port, never tested")
        refusal(
            log,
            "enable without a passing run for the version's hash is refused",
            "not_tested",
            lambda: svc.versions.enable(untested, caller=OPERATOR),
        )
        report = asyncio.run(svc.tests.run(draft.item, caller=OPERATOR))
        started = [
            e.data["node_id"] for e in events(home, report.run_id) if e.kind == "node_started"
        ]
        mode = events(home, report.run_id)[0].data.get("mode")
        log(f"tests.run: run {report.run_id} mode {mode} {report.status}, nodes started {started}")
        log.check(
            "tests.run on the draft finishes on script nodes, in test mode",
            report.status == "passed"
            and mode == "test"
            and started == ["start", "numbers", "double", "total"],
            (report.status, mode, started),
        )
        log.check(
            "the draft now reads tested",
            svc.drafts.state(draft.item) == "tested",
            svc.drafts.state(draft.item),
        )


def stale(log: Log) -> None:
    home = throwaway_home("ep9", "stale")
    with EngineService.open(home) as svc:
        chain = Bundle.read(CHAIN)
        item = svc.drafts.put(None, chain, 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        edited = Bundle(chain.definition, {**chain.files, "scripts/total.py": EDIT})
        svc.drafts.put(item, edited, 1, caller=OPERATOR)
        report = svc.tests.report(item)
        log.check(
            "after the edit the report reads stale", report is not None and report.stale, report
        )
        refusal(
            log,
            "publish is refused until a new test",
            "publish_refused",
            lambda: svc.versions.publish(item, "1.0.0", caller=OPERATOR),
        )
        fresh = asyncio.run(svc.tests.run(item, caller=OPERATOR))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        log.check(
            "after a new test publish succeeds", fresh.status == "passed" and bool(version), version
        )


def subgraph(log: Log) -> None:
    home = throwaway_home("ep9", "subgraph")
    with EngineService.open(home) as svc:
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        report = asyncio.run(
            svc.tests.run(item, caller=OPERATOR, inputs=[1, 2, 3], subgraph=["double", "total"])
        )
        found = events(home, report.run_id)
        started = [e.data["node_id"] for e in found if e.kind == "node_started"]
        drafted = [n for n in started if n != "subgraph-input"]
        outputs = [
            e.data.get("outputs")
            for e in found
            if e.kind == "node_finished" and e.data.get("node_id") == "total"
        ]
        log(f"nodes started: {started}; total's outputs {outputs}")
        log.check("only the two selected draft nodes run", drafted == ["double", "total"], drafted)
        log.check("they ran on the test inputs", outputs == [{"main": {"total": 12}}], outputs)
        log.check(
            "a subgraph test marks nothing tested",
            svc.drafts.state(item) == "validated",
            svc.drafts.state(item),
        )


def publish_enable(log: Log) -> None:
    home = throwaway_home("ep9", "publish-enable")
    with EngineService.open(home) as svc:
        library = svc.ctx.library
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        report = asyncio.run(svc.tests.run(item, caller=OPERATOR))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        copied = [
            library.get(e.to_id).fields.get("run_id") for e in library.edges(version, "tested-by")
        ]
        log.check(
            "the published object carries the copied tested-by edge",
            copied == [report.run_id],
            copied,
        )
        runs_before = len(library.objects(item, "test-report"))
        enabled = svc.versions.enable(version, caller=OPERATOR)
        log.check(
            "enable succeeds with no new test",
            enabled.state == "enabled" and len(library.objects(item, "test-report")) == runs_before,
            enabled,
        )
        objects = len(library.objects(item, "workflow"))
        again = svc.versions.publish(item, "1.0.1", caller=OPERATOR)
        log.check(
            "a second publish with the same hash creates nothing",
            again == version and len(library.objects(item, "workflow")) == objects,
            (again, objects),
        )


class Watched(ControlService):
    puts: list[str]

    def settings_put(self, section: SettingsSection, values: Document) -> Document:
        self.puts.append(section)
        return super().settings_put(section, values)


def settings(log: Log) -> None:
    home = throwaway_home("ep9", "settings")
    (home / "settings.toml").write_text(
        '[roles]\nwriter = ["claude/opus"]\nscout = ["claude/haiku"]\n\n'
        "[engine.retry]\nbackoff = [5, 10]\n",
        encoding="utf-8",
    )
    control = Watched(home)
    control.puts = []
    port = ControlSettings(control)
    values = port.values()
    log(
        f"roles.writer {values['roles.writer']}, roles.scout {values['roles.scout']}, "
        f"retry.backoff {values['retry.backoff']}"
    )
    log.check(
        "[roles] and [engine] override the defaults",
        values["roles.writer"] == ("claude/opus",) and values["retry.backoff"] == (5, 10),
        (values["roles.writer"], values["retry.backoff"]),
    )
    chain = Bundle.read(CHAIN)
    scan = {"id": "scan", "name": "Scan", "type": "llm", "typeVersion": 1, "role": "scout"}
    nodes = [*cast(list[Any], chain.definition["nodes"]), scan | {"parameters": {}}]
    scouted = Bundle({**chain.definition, "nodes": nodes}, chain.files)
    with EngineService.open(home, settings=port) as svc:
        item = svc.drafts.put(None, scouted, 0, caller=OPERATOR).item
        codes = [p.code for p in svc.drafts.validate(item)]
    with EngineService.open(home) as svc:
        defaults = [p.code for p in svc.drafts.validate(item)]
    log.check("with the defaults alone the role is unknown", "role_unknown" in defaults, defaults)
    log.check("a role named only in [roles] validates", "role_unknown" not in codes, codes)
    log.check("settings_put was never called", control.puts == [], control.puts)


def archive(log: Log) -> None:
    home = throwaway_home("ep9", "archive")
    with EngineService.open(home) as svc:
        library = svc.ctx.library
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        run = asyncio.run(svc.runs.start(version, caller=OPERATOR))
        archived = svc.versions.archive(version, caller=OPERATOR)
        runs = svc.runs.list(item, version)
        lineage = [e.edge for e in library.edges(version, reverse=True)]
        bundle = library.get_object(version)
        log.check("the version is archived", archived.state == "archived", archived)
        log.check("its runs stay readable", [r.run_id for r in runs] == [run.run_id], runs)
        log.check("its lineage stays readable", "run-of" in lineage, lineage)
        log.check(
            "its content stays readable",
            bundle.definition["id"] == "script-chain",
            bundle.definition["id"],
        )
        refusal(
            log,
            "an archived version no longer runs",
            "run_refused",
            lambda: asyncio.run(svc.runs.start(version, caller=OPERATOR)),
        )


def refs(log: Log) -> None:
    home = throwaway_home("ep9", "refs")
    with EngineService.open(home) as svc:
        library = svc.ctx.library
        draft = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR)
        report = asyncio.run(svc.tests.run(draft.item, caller=OPERATOR))
        version = svc.versions.publish(draft.item, "1.0.0", caller=OPERATOR)
        with sqlite3.connect(library_path(home)) as db:
            rows = db.execute(
                "SELECT ref, item, object_id, revision FROM refs ORDER BY ref"
            ).fetchall()
        for row in rows:
            log(f"ref {row}")
        heads = {(str(r[0]), str(r[1])): str(r[2]) for r in rows}
        summary = library.objects(report.run_id, "workflow-run")[-1]
        log.check(
            "the draft sits on refs/drafts/<item>",
            heads.get((drafts_ref(draft.item), draft.item)) == draft.object_id,
            heads,
        )
        log.check("the version sits on main", heads.get(("main", draft.item)) == version, heads)
        log.check(
            "the test run carries mode test and status passed",
            (summary.fields["mode"], summary.fields["status"], summary.ref)
            == ("test", "passed", f"refs/runs/{report.run_id}"),
            summary.fields,
        )
        log.check(
            "the version reads as tested",
            svc.versions.get(version).tested,
            svc.versions.get(version),
        )


LANES: Final[dict[str, Callable[[Log], None]]] = {
    "e07": e07,
    "stale": stale,
    "subgraph": subgraph,
    "publish-enable": publish_enable,
    "settings": settings,
    "archive": archive,
    "refs": refs,
}


def main() -> int:
    names = sys.argv[1:] or list(LANES)
    failed = 0
    for name in names:
        log = Log("ep9", f"ep9-{name}")
        LANES[name](log)
        failed |= log.verdict()
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
