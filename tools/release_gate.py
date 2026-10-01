"""Validate product acceptance against one candidate and artifact inventory."""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import cast

DISTRIBUTIONS = {
    "qmf_core",
    "qmf_data",
    "qmf_registry",
    "qmf_indicators",
    "qmf_structure",
    "qmf_risk",
    "qmf_venue",
    "qmf_calendar_forex",
    "qml",
    "qmb",
    "qmn",
    "qma_core",
    "qma_wire",
    "qma_daemon",
}

REQUIRED = (
    "factory",
    "root",
    "nested",
    "source_coverage",
    "independent_review",
    "installed_launch",
    "selected_bot",
    "economic_ledger",
    "data_numeric",
    "node_contracts",
    "optimization",
    "atc",
    "browser_journeys",
    "second_pack",
    "cancel_reconnect_restart",
    "windows_recovery",
    "security",
)


def evaluate(manifest: object, *, evidence_root: Path | None = None) -> list[str]:
    """Missing, stale, skipped and blocked acceptance never become PASS."""
    if not isinstance(manifest, Mapping):
        return ["release evidence must be an object"]
    manifest = cast("Mapping[str, object]", manifest)
    errors: list[str] = []
    candidate = manifest.get("candidate")
    if (
        not isinstance(candidate, str)
        or len(candidate) != 40
        or any(char not in "0123456789abcdef" for char in candidate)
    ):
        errors.append("candidate must be a full commit SHA")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping) or not artifacts:
        errors.append("artifact inventory is missing")
        artifacts = {}
    artifacts = cast("Mapping[str, object]", artifacts)
    for name, digest in artifacts.items():
        if (
            not name
            or not isinstance(digest, str)
            or (len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest))
        ):
            errors.append(f"{name}: artifact SHA256 is invalid")
    wheel_names = {str(name).split("-")[0] for name in artifacts if str(name).endswith(".whl")}
    for name in sorted(DISTRIBUTIONS - wheel_names):
        errors.append(f"{name}: required wheel is missing")
    for suffix in ("ui.tar.gz", "launcher.py", "requirements.lock", "pack-resources.json"):
        if not any(str(name).endswith(suffix) for name in artifacts):
            errors.append(f"{suffix}: required product artifact is missing")
    if evidence_root is not None:
        for name, digest in artifacts.items():
            path = _local_file(evidence_root, name)
            if path is None or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                errors.append(f"{name}: artifact is absent or checksum differs")
            else:
                errors.extend(_artifact_errors(path))
    checks = manifest.get("checks")
    if not isinstance(checks, Mapping):
        checks = {}
    checks = cast("Mapping[str, object]", checks)
    for name in REQUIRED:
        check = checks.get(name)
        if not isinstance(check, Mapping):
            errors.append(f"{name}: mandatory evidence is missing")
            continue
        check = cast("Mapping[str, object]", check)
        if check.get("status") != "PASS":
            errors.append(f"{name}: acceptance is {check.get('status', 'NOT RUN')}")
        if check.get("candidate") != candidate:
            errors.append(f"{name}: evidence belongs to another candidate")
        if check.get("artifacts") != artifacts or not artifacts:
            errors.append(f"{name}: evidence does not bind the artifact inventory")
        if (
            not isinstance(check.get("command"), str)
            or not str(check.get("command")).strip()
            or (not isinstance(check.get("trace"), str) or not str(check.get("trace")).strip())
        ):
            errors.append(f"{name}: command and trace are required")
        if evidence_root is not None and _local_file(evidence_root, check.get("trace")) is None:
            errors.append(f"{name}: trace is absent or outside evidence root")
    return errors


def _local_file(root: Path, name: object) -> Path | None:
    if not isinstance(name, str):
        return None
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size == 0:
        return None
    return path


def _artifact_errors(path: Path) -> list[str]:
    """Empty or wrongly formatted files cannot impersonate built product artifacts."""
    try:
        if path.suffix == ".whl":
            with zipfile.ZipFile(path) as wheel:
                metadata = [
                    name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
                ]
                if len(metadata) != 1 or b"Name: " not in wheel.read(metadata[0]):
                    return [f"{path.name}: missing wheel distribution metadata"]
        elif path.name.endswith("ui.tar.gz"):
            with tarfile.open(path) as packed:
                if "index.html" not in packed.getnames():
                    return [f"{path.name}: missing UI entrypoint"]
        elif path.name.endswith("pack-resources.json"):
            resources: object = json.loads(path.read_text())
            if not isinstance(resources, dict) or len(cast("dict[str, object]", resources)) < 5:
                return [f"{path.name}: mandatory pack resource inventory is missing"]
        elif path.name.endswith("requirements.lock") and "==" not in path.read_text():
            return [f"{path.name}: runtime versions are not pinned"]
    except (OSError, ValueError, zipfile.BadZipFile, tarfile.TarError, KeyError) as exc:
        return [f"{path.name}: invalid artifact format: {exc}"]
    return []


def main(path: Path) -> int:
    """Read a saved evidence record; malformed or missing records fail closed."""
    try:
        manifest: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"release: FAIL: {exc}")
        return 1
    errors = evaluate(manifest, evidence_root=path.parent)
    for error in errors:
        print(f"release: FAIL: {error}")
    if not errors:
        print("release: PASS")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
