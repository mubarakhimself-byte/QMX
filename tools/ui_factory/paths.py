"""Resolved locations for the UI factory.

The shared laptop checkout is never this worktree. State lives beside the
repo, next to other QMX-worktrees, not inside git.
"""

from __future__ import annotations

import os
from pathlib import Path

FACTORY_DIR = Path(__file__).resolve().parent
REPO_ROOT = FACTORY_DIR.parent.parent
WORKTREE_ROOT_DEFAULT = REPO_ROOT.parent / "QMX-worktrees"
STATE_DIR_DEFAULT = WORKTREE_ROOT_DEFAULT / "_ui-factory"
SOURCE_SKILL = REPO_ROOT / ".grok" / "skills" / "run-ui-epics"
USER_SKILL = Path.home() / ".grok" / "skills" / "run-ui-epics"
USER_WORKFLOW = Path.home() / ".grok" / "workflows" / "ui-epic-build.rhai"
PLUGIN_DIR = Path.home() / ".grok" / "plugins" / "ui-epic-factory"
MARKETPLACE_DIR = Path.home() / "grok-plugins" / "ui-epic-factory"
DESTINATION_BRANCH = "ui-integration"
BACKEND_BRANCH = "integration"
MAIN_BRANCH = "main"


def env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    if raw == "":
        return default
    return Path(raw)


def state_dir() -> Path:
    return env_path("QMX_UI_FACTORY_STATE", STATE_DIR_DEFAULT)


def worktree_root() -> Path:
    return env_path("QMX_UI_FACTORY_WORKTREES", WORKTREE_ROOT_DEFAULT)


def expand_user(path: Path) -> Path:
    return path.expanduser().resolve()
