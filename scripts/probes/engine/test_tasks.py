"""Each E23 task's checker fails on an empty folder and passes on the task's reference answer.

uv run --no-sync python -m pytest scripts/probes/engine/test_tasks.py -q
"""

# ruff: noqa: S101

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tasks import Task, load

TASKS = load()


def test_the_set_holds_ten_tasks() -> None:
    assert len(TASKS) == 10


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.slug)
def test_checker_fails_on_an_empty_folder(task: Task, tmp_path: Path) -> None:
    passed, _ = task.check(tmp_path)
    assert passed is False


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.slug)
def test_checker_fails_on_the_untouched_seed(task: Task, tmp_path: Path) -> None:
    task.seed(tmp_path / "work")
    passed, _ = task.check(tmp_path / "work")
    assert passed is False


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.slug)
def test_checker_passes_on_the_reference_answer(task: Task, tmp_path: Path) -> None:
    work = tmp_path / "work"
    task.seed(work)
    shutil.copytree(task.folder / "reference", work, dirs_exist_ok=True)
    passed, message = task.check(work)
    assert (passed, message) == (True, "")
