"""Resolved locations for the UI factory.

State lives in a stable sibling worktree root derived from the main
checkout, never nested as QMX-worktrees/QMX-worktrees.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

FACTORY_DIR = Path(__file__).resolve().parent
REPO_ROOT = FACTORY_DIR.parent.parent
USER_SKILL = Path.home() / ".grok" / "skills" / "run-ui-epics"
USER_WORKFLOW = Path.home() / ".grok" / "workflows" / "ui-epic-build.rhai"
PLUGIN_DIR = Path.home() / ".grok" / "plugins" / "ui-epic-factory"
MARKETPLACE_DIR = Path.home() / "grok-plugins" / "ui-epic-factory"
DESTINATION_BRANCH = "ui-integration"
BACKEND_BRANCH = "integration"
MAIN_BRANCH = "main"
PRODUCT_HOST = "apps/qmx-ui"
FIXTURE_HOST = "tools/ui_factory/fixtures/factory-test-app"


def env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    if raw == "":
        return default
    return Path(raw)


def git_common_dir(start: Path) -> Path | None:
    proc = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=start,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    if text == "":
        return None
    return Path(text)


def main_checkout(start: Path | None = None) -> Path:
    common = git_common_dir(start or FACTORY_DIR)
    if common is None:
        return REPO_ROOT
    if common.name == ".git":
        return common.parent
    return common.parent


def default_worktree_root() -> Path:
    main = main_checkout()
    return main.parent / f"{main.name}-worktrees"


def state_dir() -> Path:
    return env_path("QMX_UI_FACTORY_STATE", default_worktree_root() / "_ui-factory")


def worktree_root() -> Path:
    return env_path("QMX_UI_FACTORY_WORKTREES", default_worktree_root())


def expand_user(path: Path) -> Path:
    return path.expanduser().resolve()


SOURCE_SKILL = REPO_ROOT / ".grok" / "skills" / "run-ui-epics"
