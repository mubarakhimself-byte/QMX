"""The change cards carry the copilot eval battery's result (engine AD-66): a task is one Library
put, and a card reads the latest result for its change without waiting on a battery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from qmx_control.service import (
    EVAL_TASK,
    ControlError,
    ControlService,
    LibraryInput,
    draft_subject,
    eval_run_input,
    model_subject,
)


def side(model: str, digest: str, passed: int) -> dict[str, Any]:
    return {
        "model": model,
        "surface_digest": digest,
        "run_id": f"run-{model}",
        "status": "passed",
        "passed": passed,
        "total": 2,
    }


def result(subject: str, candidate_digest: str = "aa") -> Any:
    return {
        "subject": subject,
        "mode": "live",
        "judge": {"row": "openrouter/moonshotai/kimi-k2.5", "family": "moonshot"},
        "candidate": side("openrouter/deepseek/deepseek-chat", candidate_digest, 1),
        "baseline": side("claude/opus", "aa", 2),
        "per_task": [
            {"id": "t1", "candidate": True, "baseline": True},
            {"id": "t2", "candidate": False, "baseline": True},
        ],
    }


def test_a_new_failure_becomes_a_task_with_one_put(tmp_path: Path) -> None:
    control = ControlService(tmp_path)
    task: Any = {
        "id": "t9",
        "prompt": "p",
        "grade": {"by": "judge", "rubric": "r"},
        "source": "chat",
    }
    control.library_save(LibraryInput(title="t9", kind="artifact", content=task, tags=[EVAL_TASK]))
    control.library_save(LibraryInput(title="other", kind="artifact", content={}, tags=["eval"]))

    assert control.library_eval_tasks() == [task]


def test_the_model_card_returns_pass3_per_task_for_both_models(tmp_path: Path) -> None:
    control = ControlService(tmp_path)
    control.settings_put("agents", {"copilot_model": "claude/opus"})
    new = "openrouter/deepseek/deepseek-chat"
    before: Any = control.settings_model_card(new)
    control.library_save(eval_run_input(result(model_subject("claude/opus", new))))

    card: Any = control.settings_model_card(new)

    assert before["battery"] == {
        "status": "not run",
        "subject": "copilot-model:claude/opus->openrouter/deepseek/deepseek-chat",
    }
    assert card["change"] == {
        "section": "agents",
        "key": "copilot_model",
        "from": "claude/opus",
        "to": new,
    }
    battery = card["battery"]
    assert battery["per_task"] == [
        {"id": "t1", "candidate": True, "baseline": True},
        {"id": "t2", "candidate": False, "baseline": True},
    ]
    assert (battery["candidate"]["passed"], battery["baseline"]["passed"]) == (1, 2)
    assert card["surface_digest"] == {"from": "aa", "to": "aa", "changed": False}


def test_a_persona_draft_card_carries_the_battery_and_the_digest_change(tmp_path: Path) -> None:
    control = ControlService(tmp_path)
    published: Any = control.library_save(
        LibraryInput(title="p", kind="persona", content="Be brief.")
    )
    draft = control.library_save(
        LibraryInput(title="p", kind="persona", content="Be blunt.", previous_id=published["id"])
    )
    control.library_save(eval_run_input(result(draft_subject(str(draft["id"])), "bb")))

    card: Any = control.library_publish_card(str(draft["id"]))

    assert card["change"] == {"kind": "persona", "item": draft["id"], "replaces": published["id"]}
    assert card["battery"]["status"] == "ran"
    assert card["surface_digest"] == {"from": "aa", "to": "bb", "changed": True}
    note = control.library_save(LibraryInput(title="n", kind="artifact", content="a note"))
    with pytest.raises(ControlError) as refused:
        control.library_publish_card(str(note["id"]))
    assert refused.value.code == "not_a_slot_item"
