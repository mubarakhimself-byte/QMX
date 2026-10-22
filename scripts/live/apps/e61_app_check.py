"""E61: `qmx app check` refuses a pack it cannot carry (AD-61, AD-19; review 48 M10).

Two refusals, each on a real pack view built for it:

- a tool whose wire name `mcp__qmx__<toolset>_<op>` passes 64 characters;
- a pack whose server serves a tool its `[operations]` rows never declared.

The third case is the clean pack: the same view, declared and served equal, must pass.

    python e61_app_check.py --evidence D:/QMX-worktrees/qma-ship/build/evidence/app2a

Writes `owner-app2a-e61.log` beside the other APP2a logs and exits 0 only when every case reads
PASS.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path("D:/QMX-worktrees/qma-ship/build/evidence/app2a")
LOG = "owner-app2a-e61.log"


@dataclass(frozen=True, slots=True)
class Case:
    name: str
    declared: tuple[str, ...]
    served: tuple[str, ...]
    toolset: str
    expected: str


CASES = (
    Case(
        "a wire name past 64",
        ("b" * 40,),
        ("b" * 40,),
        "app:" + "a" * 30,
        "wire_name: mcp__qmx__",
    ),
    Case(
        "a served tool it never declared",
        ("alpha_ping",),
        ("alpha_ping", "alpha_send"),
        "app:pack-alpha",
        "tools_differ: the server's tools differ from the declared rows",
    ),
    Case("a clean pack", ("alpha_ping",), ("alpha_ping",), "app:pack-alpha", "ok"),
)


def view(root: Path) -> Path:
    """One pack view on disk: the plugin manifest and one skill, as PACK materialises it."""
    files = {
        ".claude-plugin/plugin.json": json.dumps({"name": "pack-alpha", "version": "0.1.0"}),
        "skills/alpha-skill/SKILL.md": "---\nname: alpha-skill\n---\n\nAsk alpha for a reading.\n",
    }
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    args = parser.parse_args(argv)
    sys.path.insert(0, str(ROOT / "qmx-agents" / "packages" / "qmx-apps" / "src"))
    from qmx_apps.road.check import check  # noqa: PLC0415

    args.evidence.mkdir(parents=True, exist_ok=True)
    folder = view(args.evidence / "e61-pack-alpha")
    lines: list[str] = ["# E61: qmx app check on a pack view", ""]
    passed = True
    for case in CASES:
        found = check(folder, declared=case.declared, served=case.served, toolset=case.toolset)
        refusals = " | ".join(found.refusals) or "no refusal"
        hit = case.expected == "ok" and found.ok
        hit = hit or any(row.startswith(case.expected) for row in found.refusals)
        passed = passed and hit
        lines.append(f"{'PASS' if hit else 'FAIL'}  {case.name}: {refusals}")
        if case.expected == "ok" and found.ok:
            lines.append(f"      tools: {', '.join(found.tools)}")
    shutil.rmtree(folder.parent / "e61-pack-alpha", ignore_errors=True)
    lines += ["", f"E61 {'PASS' if passed else 'FAIL'}", ""]
    log = args.evidence / LOG
    log.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
