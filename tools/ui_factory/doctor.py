"""Setup/doctor: toolchain, MCP, destination branch, no-story waiting."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ui_factory.config import FactoryConfig, load_pins
from ui_factory.paths import SOURCE_SKILL, USER_SKILL, USER_WORKFLOW
from ui_factory.quality import find_host_root
from ui_factory.validate_inputs import validate_inputs


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    kind: str = "local"  # local | mcp | ci | pin-mismatch


@dataclass
class DoctorReport:
    checks: list[Check] = field(default_factory=list)
    ready: bool = False
    waiting_for_input: bool = False
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "waiting_for_input": self.waiting_for_input,
            "checks": [asdict(c) for c in self.checks],
            "limitations": self.limitations,
        }


def _run(argv: list[str]) -> tuple[int, str]:
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    text = (proc.stdout or "") + (proc.stderr or "")
    return int(proc.returncode), text.strip()


def _node_version() -> str:
    code, text = _run(["node", "-v"])
    if code != 0:
        return ""
    return text.lstrip("v").split()[0]


def _in_range(version: str, spec: str) -> bool:
    # spec like ">=22.12.0 <23.0.0"
    if version == "":
        return False
    parts = [int(p) for p in version.split(".")[:3]]
    while len(parts) < 3:
        parts.append(0)
    major, minor, patch = parts
    if ">=22.12.0" in spec and (major, minor, patch) < (22, 12, 0):
        return False
    return not ("<23.0.0" in spec and major >= 23)


def run_doctor(config: FactoryConfig, *, mcp: dict[str, bool] | None) -> DoctorReport:
    report = DoctorReport()
    pins = load_pins()
    node_spec = str(pins.get("node_range") or ">=22.12.0 <23.0.0")
    node = _node_version()
    node_ok = _in_range(node, node_spec)
    report.checks.append(
        Check(
            "node",
            node != "",
            f"found {node or 'missing'}; pin {node_spec}",
            "pin-mismatch" if node and not node_ok else "local",
        )
    )
    if node and not node_ok:
        report.limitations.append(
            f"Workstation Node {node} is outside ADR pin {node_spec}. "
            "CI uses Node 22.12.0. Vite 8 engines are "
            "^20.19.0 || >=22.12.0 so Node 24 can run Vite; "
            "do not label a Node 24 run as ADR Node 22."
        )
    pnpm = shutil.which("pnpm")
    report.checks.append(
        Check("pnpm", pnpm is not None, pnpm or "pnpm missing", "local")
    )
    report.checks.append(
        Check("python", True, sys.version.split()[0], "local")
    )
    uv = shutil.which("uv")
    report.checks.append(Check("uv", uv is not None, uv or "uv missing", "local"))
    gh = shutil.which("gh")
    report.checks.append(
        Check(
            "gh",
            gh is not None,
            gh or "gh missing; live CI wait unavailable",
            "ci",
        )
    )
    if gh is None:
        report.limitations.append(
            "Live GitHub CI wait is unproven until gh is used against "
            "a factory-candidate/ui tag or ui-integration push."
        )
    dest = config.destination_branch
    report.checks.append(
        Check(
            "destination_branch",
            dest not in {config.backend_branch, "main", "integration"},
            f"UI destination is {dest}; backend remains {config.backend_branch}",
            "local",
        )
    )
    report.checks.append(
        Check(
            "source_skill",
            SOURCE_SKILL.is_dir(),
            str(SOURCE_SKILL),
            "local",
        )
    )
    report.checks.append(
        Check(
            "installed_skill",
            (USER_SKILL / "SKILL.md").is_file(),
            str(USER_SKILL),
            "local",
        )
    )
    report.checks.append(
        Check(
            "installed_workflow",
            USER_WORKFLOW.is_file(),
            str(USER_WORKFLOW),
            "local",
        )
    )
    host = find_host_root(config.repo_root, config.host_app_roots)
    report.checks.append(
        Check(
            "host_app",
            host is not None,
            str(host) if host else "no package.json host yet (product stories will add it)",
            "local",
        )
    )
    mcp_map = mcp or {}
    for name, present in mcp_map.items():
        report.checks.append(
            Check(f"mcp:{name}", present, "connected" if present else "absent", "mcp")
        )
        if not present:
            report.limitations.append(
                f"MCP {name} is not connected in this session. "
                "CLI readiness is separate from MCP readiness."
            )
    validation = validate_inputs(config)
    waiting = validation.status == "waiting_for_input"
    report.waiting_for_input = waiting
    report.checks.append(
        Check(
            "stories",
            validation.stories > 0,
            validation.status + f" stories={validation.stories}",
            "local",
        )
    )
    if waiting:
        report.limitations.append(
            "No UI stories supplied. Setup is complete and waiting for BMAD "
            "epics/stories. The factory will not generate a backlog."
        )
    blocking = [
        c
        for c in report.checks
        if not c.ok and c.name in {"python", "uv", "destination_branch", "source_skill"}
    ]
    report.ready = not blocking
    return report


def write_restart_safe_report(path: Path, report: DoctorReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
