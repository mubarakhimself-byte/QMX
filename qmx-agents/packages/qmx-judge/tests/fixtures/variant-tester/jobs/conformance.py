"""The variant's `conformance` run kind: each of the core's cases laid out and replayed."""

from __future__ import annotations

import json
import runpy
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

VARIANT = cast("dict[str, Any]", runpy.run_path(str(Path(__file__).parents[1] / "variant.py")))
replay = cast("Callable[[Path, str], dict[str, object] | str]", VARIANT["replay"])
leave = cast("Callable[..., object]", VARIANT["leave"])


def run(inputs: Mapping[str, object]) -> object:
    run_id, folder = str(inputs["run_id"]), Path(str(inputs["run_folder"]))
    pack = cast("dict[str, Any]", inputs["pack"])
    cases: dict[str, object] = {}
    for case in cast("list[dict[str, Any]]", pack["cases"]):
        root = folder / "cases" / str(case["case"])
        for path, text in cast("dict[str, str]", pack["files"]).items():
            (root / "in" / path).parent.mkdir(parents=True, exist_ok=True)
            (root / "in" / path).write_text(text, "utf-8", newline="")
        (root / "in" / "request.json").write_text(json.dumps(case["request"]), "utf-8")
        found = replay(root, f"{run_id}/{case['case']}")
        cases[str(case["case"])] = (
            {"status": "failed", "reason": found}
            if isinstance(found, str)
            else {"status": "finished", **found}
        )
    report = {"schema_version": "qmx.conformance.output/1", "pack": pack["id"], "cases": cases}
    return leave(folder, run_id, report)
