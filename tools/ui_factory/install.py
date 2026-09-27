"""Copy version-controlled source into the user Grok skill/plugin locations."""

from __future__ import annotations

import shutil
from pathlib import Path

from ui_factory.paths import (
    MARKETPLACE_DIR,
    PLUGIN_DIR,
    SOURCE_SKILL,
    USER_SKILL,
    USER_WORKFLOW,
)


def _copytree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def install_user_copy() -> dict[str, str]:
    if not SOURCE_SKILL.is_dir():
        raise FileNotFoundError(f"source skill missing: {SOURCE_SKILL}")
    USER_SKILL.parent.mkdir(parents=True, exist_ok=True)
    _copytree(SOURCE_SKILL, USER_SKILL)
    workflow_src = SOURCE_SKILL / "references" / "ui-epic-build.rhai"
    USER_WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(workflow_src, USER_WORKFLOW)
    plugin_skill = PLUGIN_DIR / "skills" / "run-ui-epics"
    plugin_skill.parent.mkdir(parents=True, exist_ok=True)
    _copytree(SOURCE_SKILL, plugin_skill)
    marketplace_skill = MARKETPLACE_DIR / "skills" / "run-ui-epics"
    marketplace_skill.parent.mkdir(parents=True, exist_ok=True)
    _copytree(SOURCE_SKILL, marketplace_skill)
    return {
        "source": str(SOURCE_SKILL),
        "user_skill": str(USER_SKILL),
        "user_workflow": str(USER_WORKFLOW),
        "plugin": str(PLUGIN_DIR),
        "marketplace": str(MARKETPLACE_DIR),
    }
