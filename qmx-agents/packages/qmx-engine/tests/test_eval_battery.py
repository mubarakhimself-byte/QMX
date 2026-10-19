"""The copilot eval battery (AD-66): its grading scripts on recorded tries, the judge's family, and
the battery run end to end on a `FakePort` with the model under change beside the baseline."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fake_port import TOKENS, FakePort

from qmx_engine.ports.harness_adapter import Turn
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.service.api import EngineService
from qmx_engine.settings import DEFAULTS
from qmx_engine.templates import battery
from qmx_engine.templates.battery import Judge, Side, family, judge_for

FOLDER = battery.FOLDER
SEEDS: list[dict[str, Any]] = json.loads((FOLDER / "fixtures" / "tasks.json").read_text("utf-8"))[
    "tasks"
]
DEEPSEEK = "openrouter/deepseek/deepseek-chat"
HAIKU = "claude/haiku"
KIMI = "openrouter/moonshotai/kimi-k2.5"


def script(name: str, given: Any) -> Any:
    done = subprocess.run(
        [sys.executable, str(FOLDER / "scripts" / name)],
        input=json.dumps({"in": given}),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(done.stdout)


def code_task(task_id: str, *checks: dict[str, Any]) -> dict[str, Any]:
    return {"id": task_id, "prompt": "p", "grade": {"by": "code", "checks": list(checks)}}


def tries(*answers: dict[str, str]) -> list[dict[str, Any]]:
    return [{"answers": [{"id": k, "answer": v} for k, v in a.items()]} for a in answers]


def test_pass3_holds_only_for_the_task_that_passed_all_three_recorded_tries() -> None:
    number = code_task("n", {"kind": "matches", "pattern": r"^\s*391\s*$"})
    judged = {"id": "j", "prompt": "p", "grade": {"by": "judge", "rubric": "r"}}
    tasks = {"surface": "", "tasks": [number, judged]}
    graded = script(
        "grade.py",
        [tasks, *tries({"n": "391", "j": "a"}, {"n": "391", "j": "b"}, {"n": "391", "j": "c"})],
    )
    verdicts = [
        {"key": "j#1", "verdict": "pass", "why": "ok"},
        {"key": "j#2", "verdict": "fail", "why": "it named a tool"},
        {"key": "j#3", "verdict": "pass", "why": "ok"},
    ]

    report = script("report.py", [graded, {"verdicts": verdicts}])

    assert report == {
        "tasks": [
            {"id": "n", "graded_by": "code", "tries": [True, True, True], "pass3": True, "why": []},
            {
                "id": "j",
                "graded_by": "judge",
                "tries": [True, False, True],
                "pass3": False,
                "why": ["it named a tool"],
            },
        ],
        "passed": 1,
        "total": 2,
    }


def test_code_grading_on_a_fixture_task_names_the_check_that_failed() -> None:
    task = next(t for t in SEEDS if t["id"] == "b51-json-only")
    tasks = {"surface": "", "tasks": [task]}
    fenced = '```json\n{"answer": "Paris", "confidence": "high"}\n```'
    answers = tries(
        {"b51-json-only": fenced},
        {"b51-json-only": "Paris, with high confidence."},
        {"b51-json-only": '{"answer": "Lyon", "confidence": "low"}'},
    )

    graded = script("grade.py", [tasks, *answers])

    assert [(c["try"], c["passed"], c["why"]) for c in graded["code"]] == [
        (1, True, None),
        (2, False, "json_keys"),
        (3, False, "contains"),
    ]
    assert graded["items"] == []


def test_a_try_with_no_answer_fails_and_the_grades_never_reach_the_tries() -> None:
    tasks = script("tasks.py", {"fixture": True, "surface": "Be brief."})
    brief = script("brief.py", tasks)
    graded = script("grade.py", [tasks, *tries({}, {}, {})])

    assert len(tasks["tasks"]) == 20
    assert brief["surface"] == "Be brief."
    assert {key for t in brief["tasks"] for key in t} == {"id", "prompt"}
    assert {c["why"] for c in graded["code"]} == {"no answer"}
    assert len(graded["code"]) == 60


def test_the_judge_resolves_to_another_family_than_every_graded_model() -> None:
    assert family(DEEPSEEK) == "deepseek"
    assert family(HAIKU) == "anthropic"
    assert family(KIMI) == "moonshot"
    assert family("kimi/k3") == "moonshot"
    assert family("gpt/gpt-5.5@high") == "openai"
    assert judge_for([DEEPSEEK, HAIKU], [HAIKU, "claude/sonnet", KIMI]) == Judge(KIMI, False)
    assert judge_for([HAIKU, HAIKU], [HAIKU, DEEPSEEK]) == Judge(DEEPSEEK, False)
    assert judge_for([HAIKU, KIMI], [HAIKU, KIMI]) == Judge(HAIKU, True)


def answering(wrong: frozenset[str] = frozenset()) -> FakePort:
    """Every try answers from the recorded answers, except that a chat on a model in `wrong`
    answers every task with nothing useful; the judge passes every item it is given."""
    recorded = (FOLDER / "fixtures" / "recorded" / "answers.json").read_text("utf-8")

    async def answer(port: FakePort, chat: str) -> Turn:
        opened = port.chats[int(chat.removeprefix("chat-")) - 1]
        sent = next(sent for to, sent in reversed(port.sent) if to == chat)
        text = f"{opened['system'] or ''}\n\n{sent}"
        given = json.loads(text.rsplit("Input:\n", 1)[-1])["in"]
        if "You grade answers" in text:
            keys = [item["key"] for item in given["items"]]
            verdicts = [{"key": k, "verdict": "pass", "why": "meets the rubric"} for k in keys]
            return Turn(json.dumps({"verdicts": verdicts}), dict(TOKENS))
        if opened["model"] in wrong:
            blank = [{"id": t["id"], "answer": "I am not sure."} for t in given["tasks"]]
            return Turn(json.dumps({"answers": blank}), dict(TOKENS))
        return Turn(recorded, dict(TOKENS))

    return FakePort(*[answer] * 40)


def battery_run(home: Path, port: FakePort, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    values = {**DEFAULTS, "roles.test_only": (DEEPSEEK, KIMI)}
    with EngineService.open(home, settings=StaticSettings(values), harness=port) as svc:
        return asyncio.run(
            battery.run(
                svc,
                tasks,
                Side(DEEPSEEK),
                Side(HAIKU),
                judges=(HAIKU, KIMI),
                subject=f"copilot-model:{HAIKU}->{DEEPSEEK}",
                mode="test",
            )
        )


def test_a_model_change_reports_pass3_per_task_for_the_new_model_and_the_baseline(
    tmp_path: Path,
) -> None:
    port = answering(wrong=frozenset({"deepseek/deepseek-chat"}))
    tasks = [t for t in SEEDS if t["id"] in ("quant-basis-points", "op-hard-truth")]

    result = battery_run(tmp_path, port, tasks)

    assert result["per_task"] == [
        {"id": "quant-basis-points", "candidate": False, "baseline": True},
        {"id": "op-hard-truth", "candidate": True, "baseline": True},
    ]
    assert (result["candidate"]["ran_on"], result["baseline"]["ran_on"]) == (
        [DEEPSEEK],
        [HAIKU],
    )
    assert result["judge"] == {"row": KIMI, "family": "moonshot", "same_family": False}
    assert result["candidate"]["judged_on"] == [KIMI]
    assert (result["candidate"]["passed"], result["baseline"]["passed"]) == (1, 2)
    assert sorted(str(c["model"]) for c in port.chats) == sorted(
        ["deepseek/deepseek-chat"] * 3 + ["haiku"] * 3 + ["moonshotai/kimi-k2.5"] * 2
    )


def test_a_side_whose_tries_ran_on_another_model_reports_no_pass3(tmp_path: Path) -> None:
    values = {**DEFAULTS, "roles.test_only": ("kimi/k3", KIMI)}
    tasks = [t for t in SEEDS if t["id"] == "quant-basis-points"]
    with EngineService.open(tmp_path, settings=StaticSettings(values), harness=answering()) as svc:
        result: Any = asyncio.run(
            battery.run(
                svc,
                tasks,
                Side("kimi/k3"),
                Side(HAIKU),
                judges=(KIMI,),
                subject="no kimi profile",
                mode="test",
            )
        )

    assert result["candidate"]["status"] == "fell back to another model"
    assert result["candidate"]["fell_back"] == ["try_1", "try_2", "try_3"]
    assert result["per_task"] == [{"id": "quant-basis-points", "candidate": None, "baseline": True}]


def test_the_template_test_run_on_its_seed_tasks_passes_all_20(tmp_path: Path) -> None:
    result = battery_run(tmp_path, answering(), SEEDS)

    assert (result["candidate"]["passed"], result["candidate"]["total"]) == (20, 20)
    assert [t["id"] for t in result["per_task"]] == [t["id"] for t in SEEDS]
    assert result["candidate"]["surface_digest"] == result["baseline"]["surface_digest"]
