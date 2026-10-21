"""P-NEST (engine AD-5, SOLUTION-DESIGN 28.8): the built validator accepts a loop whose body calls
a subworkflow that holds its own loop, the one sanctioned nesting (the revolution-loop shape).

The probe writes the parent and its child block folder `blocks/inner/` into a throwaway home and
runs the engine's own `validate` and `checked` on both: the parent because that is what a save
runs, the child because the `subworkflow` node runs `checked` on it at dispatch. It also records,
as a control, what the validator says about a loop directly inside a loop body, which AD-5 says
v1 refuses with `nesting_unsupported`.

    uv run --no-sync --project qmx-agents python scripts/probes/library/p_nest.py
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from common import HOMES, Log, Verdict

FALLBACK: Final = "TPL3 adds exactly this exception to the validator."


def node(name: str, type_: str, **parameters: Any) -> dict[str, Any]:
    return {"id": name, "name": name, "type": type_, "typeVersion": 1, "parameters": parameters}


def to(target: str, port: str = "in") -> list[dict[str, Any]]:
    return [{"node": target, "port": port, "map": "one"}]


def write(root: Path, nodes: list[dict[str, Any]], connections: dict[str, Any]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    document = {
        "schema": "qmx.workflow/1",
        "id": root.name,
        "name": root.name,
        "nodes": nodes,
        "connections": {s: {p: [t] for p, t in ports.items()} for s, ports in connections.items()},
    }
    (root / "definition.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    (root / "scripts").mkdir(exist_ok=True)
    (root / "scripts" / "step.py").write_text("def main(value):\n    return value\n", "utf-8")
    return root


def looped(root: Path, body: dict[str, Any]) -> Path:
    """trigger -> loop; the loop's body is `body`, which feeds `next`; `done` ends the run."""
    return write(
        root,
        [
            node("start", "trigger"),
            node("again", "loop", max_iterations=3),
            body,
            node("after", "script", script="scripts/step.py"),
        ],
        {
            "start": {"main": to("again")},
            "again": {"body": to(body["name"]), "done": to("after")},
            body["name"]: {"main": to("again", "next")},
        },
    )


def shapes(home: Path) -> tuple[Path, Path, Path]:
    """The parent, its child block, and the control (a loop inside a loop body, no subworkflow)."""
    shutil.rmtree(home, ignore_errors=True)
    parent = looped(home / "revolution", node("child", "subworkflow", workflow="blocks/inner"))
    inner = looped(parent / "blocks" / "inner", node("step", "script", script="scripts/step.py"))
    control = write(
        home / "loop-in-loop",
        [
            node("start", "trigger"),
            node("outer", "loop", max_iterations=3),
            node("inner", "loop", max_iterations=3),
            node("step", "script", script="scripts/step.py"),
        ],
        {
            "start": {"main": to("outer")},
            "outer": {"body": to("inner")},
            "inner": {"body": to("step"), "done": to("outer", "next")},
            "step": {"main": to("inner", "next")},
        },
    )
    return parent, inner, control


def verdict(parent: Sequence[str], inner: Sequence[str]) -> Verdict:
    """PASS when the validator and the dispatch check find no problem in the parent or child."""
    numbers = {"parent_problems": len(parent), "child_problems": len(inner)}
    if not parent and not inner:
        return Verdict("P-NEST", "PASS", numbers, "the validator accepts the revolution-loop shape")
    codes = " ".join(sorted({*parent, *inner}))
    return Verdict("P-NEST", "FAIL", numbers, f"the validator refuses it: {codes}", FALLBACK)


def main() -> None:
    from qmx_engine.definition.folder import load  # noqa: PLC0415
    from qmx_engine.definition.validate import checked, validate  # noqa: PLC0415

    log = Log("prb-l-taint-nest")
    parent, inner, control = shapes(HOMES / "p_nest")
    found: dict[str, list[str]] = {}
    for name, root in (("parent", parent), ("child", inner), ("control", control)):
        problems = validate(load(root))
        ran = checked(root)
        refused = [p.code for p in ran] if isinstance(ran, list) else []
        found[name] = sorted({p.code for p in problems} | set(refused))
        log.say(f"  {name} {root.relative_to(HOMES)}: validate={problems} checked={refused}")
    if not found["control"]:
        log.say(
            "  note: the control (a loop directly inside a loop body) also validates; AD-5 says "
            "v1 refuses it with nesting_unsupported, and no such check exists yet"
        )
    log.verdict(verdict(found["parent"], found["child"]))


if __name__ == "__main__":
    main()
