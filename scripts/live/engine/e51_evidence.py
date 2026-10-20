"""E51: the number evidence rule (engine AD-45). Four small workflows run the shared
`render_and_grade` block on the fake provider, so no model is called and nothing is spent: a number
that only a model stated fails the grade, the same number stated by a fetched source passes, a year
that only a timestamp carries is no evidence while a year in the data is, and a number an agent's
code printed fails.

Run it from `qmx-agents/`: `uv run --no-sync python ../scripts/live/engine/e51_evidence.py`.
Each case is written to a scratch folder under the store's `homes/` and run as a draft; nothing is
committed but this script.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Final

from common import boot

from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.templates.catalog import PACK

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "tpl1"
ROOT: Final = STORE / "homes" / "tpl1-e51"
BLOCK: Final = PACK / "_shared" / "render-and-grade"
HEADLINE: Final = "The setup holds on the EURUSD open."


class Log:
    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"owner-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> bool:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= bool(ok)
        return bool(ok)

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        return 0 if self.passed else 1


def node(
    name: str,
    kind: str,
    position: list[int],
    *,
    role: str = "",
    retry: dict[str, Any] | None = None,
    **parameters: Any,
) -> Any:
    found: dict[str, Any] = {
        "id": name,
        "name": name.replace("_", " ").title(),
        "type": kind,
        "typeVersion": 1,
        "position": position,
        "effect": "none",
        "parameters": parameters,
    }
    if role:
        found["role"] = role
    if retry is not None:
        found["retry"] = retry
    return found


def graded(name: str, *, model: str, source: str | None, prose: str) -> dict[str, Any]:
    """One case: a payload node (`model` = the kind that writes it, `sheet` its answer), an optional
    script source, a report script that states `prose`, and the shared grade, deliver and stop."""
    nodes = [
        {
            "id": "start",
            "name": "Start",
            "type": "trigger",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {"kinds": ["manual"]},
        },
        node("payload", model, [220, 0], role="triage", **sheet_parameters(model)),
        node("report", "script", [440, 0], script="scripts/report.py"),
        node(
            "grade",
            "grader",
            [660, 0],
            mode="deterministic",
            script="scripts/render_and_grade.py",
            schema_ref="schemas/output.json",
        ),
        node("deliver", "script", [880, 0], script="scripts/deliver.py"),
        node("stop", "script", [880, 120], retry={"max_tries": 1}, script="scripts/stop.py"),
    ]
    connections: dict[str, Any] = {
        "Start": {"main": [[{"node": "Payload", "port": "in", "map": "one"}]]},
        "Payload": {"main": [[{"node": "Report", "port": "in", "map": "one"}]]},
    }
    if source is not None:
        nodes.insert(2, node("source", "script", [220, 160], script="scripts/source.py"))
        connections["Start"]["main"][0].append({"node": "Source", "port": "in", "map": "one"})
        connections["Source"] = {"main": [[{"node": "Report", "port": "in", "map": "one"}]]}
        connections["Report"] = {
            "main": [
                [
                    {"node": "Grade", "port": "in", "map": "one"},
                ]
            ]
        }
        connections["Source"]["main"][0].append({"node": "Grade", "port": "in", "map": "one"})
    else:
        connections["Report"] = {"main": [[{"node": "Grade", "port": "in", "map": "one"}]]}
    connections["Grade"] = {
        "pass": [[{"node": "Deliver", "port": "in", "map": "one"}]],
        "fail": [[{"node": "Stop", "port": "in", "map": "one"}]],
    }
    return {
        "schema": "qmx.workflow/1",
        "id": name,
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "meta": {},
    }


def sheet_parameters(model: str) -> dict[str, Any]:
    base: dict[str, Any] = {"prompt_ref": "prompts/note.md", "recording_ref": "fixtures/note.json"}
    if model == "llm":
        base["schema_ref"] = "schemas/note.json"
    else:
        base["output_schema_ref"] = "schemas/note.json"
    return base


OUTPUT_SCHEMA: Final = {
    "type": "object",
    "required": ["headline"],
    "properties": {"headline": {"type": "string"}},
    "x-prose": ["headline"],
}
NOTE_SCHEMA: Final = {
    "type": "object",
    "required": ["note"],
    "properties": {"note": {"type": "string"}},
}


def write(
    root: Path, case: dict[str, Any], *, note: dict[str, Any], prose: str, source: str
) -> Path:
    folder = root / case["id"]
    (folder / "scripts").mkdir(parents=True)
    (folder / "schemas").mkdir()
    (folder / "prompts").mkdir()
    (folder / "fixtures").mkdir()
    (folder / "definition.json").write_text(json.dumps(case, indent=2) + "\n", encoding="utf-8")
    (folder / "schemas" / "output.json").write_text(
        json.dumps(OUTPUT_SCHEMA, indent=2) + "\n", encoding="utf-8"
    )
    (folder / "schemas" / "note.json").write_text(
        json.dumps(NOTE_SCHEMA, indent=2) + "\n", encoding="utf-8"
    )
    (folder / "prompts" / "note.md").write_text("Write the note.\n", encoding="utf-8")
    (folder / "fixtures" / "note.json").write_text(json.dumps(note) + "\n", encoding="utf-8")
    (folder / "scripts" / "report.py").write_text(REPORT.format(prose=prose), encoding="utf-8")
    (folder / "scripts" / "source.py").write_text(SOURCE.format(source=source), encoding="utf-8")
    for name in ("render_and_grade.py", "deliver.py", "stop.py"):
        shutil.copyfile(BLOCK / "scripts" / name, folder / "scripts" / name)
    return folder


REPORT: Final = '''\
"""The report a case grades: it states one number, and copies nothing."""
import json
import sys

json.load(sys.stdin)
print(json.dumps({{"headline": {prose!r}}}))
'''

SOURCE: Final = '''\
"""A fetched source: the run's own record of what it read."""
import json
import sys

json.load(sys.stdin)
print(json.dumps({{"text": {source!r}}}))
'''


def run(folder: Path) -> tuple[Any, Any]:
    """The case as a draft, test-run on the fake provider: the report and what Deliver gave."""
    home = ROOT / "home"
    with EngineService.open(home) as svc:
        svc.drafts.put(folder.name, Bundle.read(folder), 0, caller=OPERATOR)
        report = asyncio.run(
            svc.tests.run(folder.name, caller=OPERATOR, inputs={"case": folder.name}, fake=True)
        )
    return report, report.reason


CASES: Final = {
    "model-intermediate": {
        "note": {"note": "The edge is 4321 pips per trade."},
        "prose": "The edge is 4321 pips per trade.",
        "source": "nothing to see",
        "model": "llm",
        "chained_source": False,
        "want": "failed",
        "why": "a number only a model's intermediate output states fails the grade",
    },
    "fetched-source": {
        "note": {"note": "Read the fetched sheet."},
        "prose": "The edge is 4321 pips per trade.",
        "source": "The fetched sheet reports an edge of 4321 pips per trade.",
        "model": "llm",
        "chained_source": True,
        "want": "passed",
        "why": "the same number stated by a fetched source passes",
    },
    "timestamp-year": {
        "note": {"note": "Read the fetched sheet."},
        "prose": "Written in 2029 for the desk.",
        "source": "The sheet was fetched at 2029-01-02T03:04:05Z.",
        "model": "llm",
        "chained_source": True,
        "want": "failed",
        "why": "a year that appears only in a timestamp is not evidence",
    },
    "year-in-data": {
        "note": {"note": "Read the fetched sheet."},
        "prose": "Written in 2029 for the desk.",
        "source": json.dumps({"year": 2029, "desk": "FX"}),
        "model": "llm",
        "chained_source": True,
        "want": "passed",
        "why": "a year the source data carries is evidence",
    },
    "agent-code": {
        "note": {"note": "The agent printed its own answer: 4321.", "printed": "4321"},
        "prose": "The agent's own code printed 4321.",
        "source": "nothing to see",
        "model": "agent",
        "chained_source": False,
        "want": "failed",
        "why": "a number an agent's own code printed fails the grade",
    },
}


def main() -> int:
    boot()
    log = Log("tpl1-e51")
    shutil.rmtree(ROOT, ignore_errors=True)
    (ROOT / "home").mkdir(parents=True)
    for name, case in CASES.items():
        definition = graded(
            name,
            model=case["model"],
            source="scripts/source.py" if case["chained_source"] else None,
            prose=case["prose"],
        )
        folder = write(
            ROOT,
            definition,
            note=case["note"],
            prose=case["prose"],
            source=case["source"],
        )
        report, reason = run(folder)
        log(f"{name}: {report.status} {reason or ''} (want {case['want']})")
        log.check(case["why"], report.status == case["want"], report.status)
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
