"""Setup/doctor: observed tools, honest MCP, readiness levels."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ui_factory.config import FactoryConfig, load_pins
from ui_factory.gitops import observed_toolchain
from ui_factory.paths import PRODUCT_HOST, SOURCE_SKILL, USER_SKILL, USER_WORKFLOW
from ui_factory.quality import find_host_root
from ui_factory.validate_inputs import validate_inputs


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    kind: str = "local"


@dataclass
class DoctorReport:
    checks: list[Check] = field(default_factory=list)
    installed: bool = False
    setup_ready: bool = False
    waiting_for_input: bool = False
    runtime_ready: bool = False
    ready: bool = False
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "installed": self.installed,
            "setup_ready": self.setup_ready,
            "waiting_for_input": self.waiting_for_input,
            "runtime_ready": self.runtime_ready,
            "ready": self.ready,
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
    if version == "":
        return False
    parts = [int(p) for p in version.split(".")[:3]]
    while len(parts) < 3:
        parts.append(0)
    major, minor, patch = parts
    if ">=22.12.0" in spec and (major, minor, patch) < (22, 12, 0):
        return False
    return not ("<23.0.0" in spec and major >= 23)


def run_doctor(
    config: FactoryConfig,
    *,
    mcp: dict[str, dict[str, object]] | None,
) -> DoctorReport:
    report = DoctorReport()
    pins = load_pins()
    node_spec = str(pins.get("node_range") or ">=22.12.0 <23.0.0")
    node = _node_version()
    node_ok = _in_range(node, node_spec)
    report.checks.append(
        Check(
            "node",
            node_ok,
            f"found {node or 'missing'}; pin {node_spec}",
            "pin-mismatch" if node and not node_ok else "local",
        )
    )
    if node and not node_ok:
        report.limitations.append(
            f"Workstation Node {node} is outside ADR pin {node_spec}. "
            "runtime_ready is false until Node 22.12.x is used or an operator "
            "amendment is recorded. Vite 8 engines allow Node 24; that is not "
            "an ADR amendment."
        )
    for name, version in observed_toolchain():
        report.checks.append(
            Check(f"observed:{name}", version != "missing", version, "local")
        )
    pnpm = shutil.which("pnpm")
    report.checks.append(Check("pnpm", pnpm is not None, pnpm or "pnpm missing"))
    report.checks.append(Check("python", True, sys.version.split()[0]))
    uv = shutil.which("uv")
    report.checks.append(Check("uv", uv is not None, uv or "uv missing"))
    gh = shutil.which("gh")
    report.checks.append(
        Check("gh", gh is not None, gh or "gh missing; live CI wait unavailable", "ci")
    )
    dest = config.destination_branch
    report.checks.append(
        Check(
            "destination_branch",
            dest not in {config.backend_branch, "main", "integration"},
            f"UI destination is {dest}; backend remains {config.backend_branch}",
        )
    )
    report.checks.append(Check("source_skill", SOURCE_SKILL.is_dir(), str(SOURCE_SKILL)))
    report.checks.append(
        Check("installed_skill", (USER_SKILL / "SKILL.md").is_file(), str(USER_SKILL))
    )
    report.checks.append(
        Check("installed_workflow", USER_WORKFLOW.is_file(), str(USER_WORKFLOW))
    )
    product = find_host_root(config.repo_root, config.host_app_roots, factory_mode="product")
    fixture = find_host_root(config.repo_root, config.host_app_roots, factory_mode="fixture")
    report.checks.append(
        Check(
            "product_host",
            product is not None,
            str(product) if product else f"missing {PRODUCT_HOST}",
        )
    )
    report.checks.append(
        Check(
            "fixture_host",
            fixture is not None,
            str(fixture) if fixture else "fixture app absent",
        )
    )
    mcp_map = mcp or {}
    if not mcp_map:
        report.checks.append(
            Check("mcp", False, "MCP not probed this run; status unknown", "mcp")
        )
        report.limitations.append(
            "MCP readiness is unknown until an orchestrator writes probed evidence."
        )
    for name, info in mcp_map.items():
        probed = bool(info.get("probed")) if isinstance(info, dict) else False
        ok = bool(info.get("ok")) if isinstance(info, dict) else False
        detail = ""
        if isinstance(info, dict):
            detail = str(info.get("detail") or "")
        if not probed:
            report.checks.append(
                Check(f"mcp:{name}", False, detail or "unknown (not probed)", "mcp")
            )
        else:
            report.checks.append(Check(f"mcp:{name}", ok, detail or "probed", "mcp"))
    validation = validate_inputs(config)
    waiting = validation.status == "waiting_for_input"
    report.waiting_for_input = waiting
    report.checks.append(
        Check(
            "stories",
            validation.stories > 0,
            f"{validation.status} stories={validation.stories}",
        )
    )
    if waiting:
        report.limitations.append(
            "No UI stories supplied. Setup can complete while waiting for BMAD."
        )
    report.installed = (USER_SKILL / "SKILL.md").is_file()
    report.setup_ready = uv is not None and SOURCE_SKILL.is_dir()
    report.runtime_ready = (
        report.setup_ready
        and node_ok
        and product is not None
        and bool(mcp_map)
        and all(
            isinstance(v, dict) and bool(v.get("probed")) and bool(v.get("ok"))
            for v in mcp_map.values()
        )
        if mcp_map
        else False
    )
    report.ready = report.setup_ready
    return report


def write_restart_safe_report(path: Path, report: DoctorReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
