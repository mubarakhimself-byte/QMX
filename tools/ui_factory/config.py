"""Load factory config. Destination branch is never hardcoded to integration."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from ui_factory.paths import (
    BACKEND_BRANCH,
    DESTINATION_BRANCH,
    FACTORY_DIR,
    PRODUCT_HOST,
    REPO_ROOT,
    state_dir,
    worktree_root,
)

CONFIG_FILE = FACTORY_DIR / "config.json"
PROFILES_FILE = FACTORY_DIR / "quality_profiles.json"
PINS_FILE = FACTORY_DIR / "pins.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be a JSON object")
    return cast(dict[str, Any], raw)


@dataclass(frozen=True)
class FactoryConfig:
    destination_branch: str
    backend_branch: str
    repo_root: Path
    state_dir: Path
    worktree_root: Path
    epic_globs: tuple[str, ...]
    python_quality: Mapping[str, str]
    host_app_roots: tuple[str, ...]
    shared_serial_paths: tuple[str, ...]
    max_parallel_epics: int
    max_repair_rounds: int
    ci_timeout_seconds: int
    product_host: str
    fixture_host: str
    required_ci_checks: tuple[str, ...]

    @property
    def merge_tmp_name(self) -> str:
        return f"merge-{self.destination_branch}-tmp"


def load_config(repo_root: Path | None = None) -> FactoryConfig:
    root = repo_root or REPO_ROOT
    data = _read_json(CONFIG_FILE)
    dest = str(data.get("destination_branch") or DESTINATION_BRANCH)
    backend = str(data.get("backend_branch") or BACKEND_BRANCH)
    if dest == backend:
        raise ValueError(
            "UI destination_branch must be a dedicated branch; "
            f"got {dest!r} which equals the backend branch"
        )
    globs = data.get("epic_globs") or [
        "_bmad-output/planning-artifacts/epics-UI*.md",
        "_bmad-output/planning-artifacts/epics-ui*.md",
    ]
    python_quality = data.get("python_quality") or {
        "lint": "uv run --project {worktree} poe lint",
        "typecheck": "uv run --project {worktree} poe types",
        "test": "uv run --project {worktree} poe test",
    }
    host_roots = data.get("host_app_roots") or [PRODUCT_HOST]
    serial = data.get("shared_serial_paths") or [
        "pnpm-lock.yaml",
        "package.json",
        f"{PRODUCT_HOST}/src/lib/tokens.css",
        f"{PRODUCT_HOST}/src/lib/components/ui",
    ]
    checks = data.get("required_ci_checks") or ["Skylos", "QA Battery", "UI quality"]
    return FactoryConfig(
        destination_branch=dest,
        backend_branch=backend,
        repo_root=root,
        state_dir=state_dir(),
        worktree_root=worktree_root(),
        epic_globs=tuple(str(g) for g in globs),
        python_quality={str(k): str(v) for k, v in python_quality.items()},
        host_app_roots=tuple(str(p) for p in host_roots),
        shared_serial_paths=tuple(str(p) for p in serial),
        max_parallel_epics=int(data.get("max_parallel_epics") or 2),
        max_repair_rounds=int(data.get("max_repair_rounds") or 3),
        ci_timeout_seconds=int(data.get("ci_timeout_seconds") or 1800),
        product_host=str(data.get("product_host") or PRODUCT_HOST),
        fixture_host=str(
            data.get("fixture_host") or "tools/ui_factory/fixtures/factory-test-app"
        ),
        required_ci_checks=tuple(str(c) for c in checks),
    )


def load_profiles() -> dict[str, Any]:
    return _read_json(PROFILES_FILE)


def load_pins() -> dict[str, Any]:
    return _read_json(PINS_FILE)
