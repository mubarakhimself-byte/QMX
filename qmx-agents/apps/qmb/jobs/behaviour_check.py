"""The `behaviour_check` run kind: QML's layer G in QMB's sandbox child (Part B slice B5b, B6).

The check runs in a fresh child, ``python -m qmb.host.behaviour``, because only a process that
loaded the unit's blocks itself may state isolation, which layer G's safety half requires. The
child reads the run folder's ``in/`` and writes nothing; its ``qmx.behaviour/1`` report is this
job's one bundle file, which the core lands as the unit's `test-report` for its fingerprint.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping

import qmb_tester as tester


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    job = {
        "run_folder": str((folder / "in").resolve()),
        "request": tester.unit_body(asked, run_id),
        "margin": asked.get("g_slice_margin", "0.20"),
    }
    child = subprocess.run(  # noqa: S603 - this interpreter, QMB's own module, no shell
        [sys.executable, "-m", "qmb.host.behaviour"],
        input=json.dumps(job),
        capture_output=True,
        text=True,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    try:
        answer = json.loads(child.stdout)
    except json.JSONDecodeError:
        tail = child.stderr.strip().splitlines()[-1:] or [f"exit {child.returncode}"]
        return tester.failed(run_id, f"the behaviour check's child gave no report: {tail[0]}")
    if answer.get("ok") is not True:
        refusal = answer.get("refusal") or {}
        return tester.failed(run_id, f"{refusal.get('field')}: {refusal.get('reason')}")
    report = answer["report"]
    return tester.leave(
        run_id,
        "finished",
        labels={"safety": report["safety"]["verdict"]},
        files=[tester.write(folder, "behaviour.json", report)],
        versions={"qmb": tester.TESTER["version"]},
    )
