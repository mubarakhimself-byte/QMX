"""The battery's tasks and the slot text the copilot is tested with. Tasks come with the run input
(`tasks`, the Library items tagged `eval-task` the caller read); a run started with
`{"fixture": true}` reads the 20 seed tasks in `fixtures/tasks.json`. `surface` is the persona,
methodology and skills index text under test, empty for the plain model. Refuses a task with no
id, no prompt, a repeated id or a grade it cannot read."""

import json
import sys
from pathlib import Path

CHECKS = {"matches", "contains", "excludes", "json_keys", "count", "max_chars"}

given = json.load(sys.stdin).get("in") or {}
if given.get("fixture"):
    seeds = json.loads((Path(__file__).parents[1] / "fixtures" / "tasks.json").read_text("utf-8"))
    given = {**seeds, "surface": given.get("surface", "")}
tasks = given.get("tasks") or []
problems = []
seen = set()
for task in tasks:
    name = task.get("id") if isinstance(task, dict) else None
    grade = task.get("grade") if isinstance(task, dict) else None
    if not isinstance(name, str) or not name or name in seen:
        problems.append(f"task {name!r} has no id or repeats one")
    elif not isinstance(task.get("prompt"), str) or not task["prompt"].strip():
        problems.append(f"task {name} has no prompt")
    elif not isinstance(grade, dict) or grade.get("by") not in ("code", "judge"):
        problems.append(f"task {name} is graded neither by code nor by the judge")
    elif grade["by"] == "judge" and not str(grade.get("rubric") or "").strip():
        problems.append(f"task {name} is judged with no rubric")
    elif grade["by"] == "code" and (
        not grade.get("checks") or any(c.get("kind") not in CHECKS for c in grade["checks"])
    ):
        problems.append(f"task {name} names a code check the battery does not have")
    seen.add(name)
if not tasks or problems:
    sys.stderr.write("; ".join(problems) or "the run input names no task")
    raise SystemExit(2)
print(json.dumps({"surface": str(given.get("surface") or ""), "tasks": tasks}))
