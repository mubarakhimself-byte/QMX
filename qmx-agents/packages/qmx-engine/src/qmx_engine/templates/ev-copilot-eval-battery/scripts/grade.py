"""Grades every try of every task by code where the task says so, and lists the rest for the judge.

Its input is the tasks with their grades and the three tries' answers. A try that gave no answer
for a task fails it. The checks, all case-insensitive: `matches` (a regular expression found in
the answer), `contains` (every listed text appears), `excludes` (no listed text appears),
`json_keys` (the answer, fences stripped, is a JSON object with every listed key), `count` (the
text appears exactly `equals` times) and `max_chars`. A code-graded try passes when every check
holds; `why` names the first that did not."""

import json
import re
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
tasks = next(v["tasks"] for v in given if isinstance(v, dict) and "tasks" in v)
tries = [
    {str(a.get("id")): str(a.get("answer", "")) for a in v["answers"]}
    for v in given
    if isinstance(v, dict) and "answers" in v
]


def unfenced(text):
    found = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", text, re.DOTALL)
    return found.group(1) if found else text


def failed_check(check, answer):
    low = answer.lower()
    match check["kind"]:
        case "matches":
            ok = re.search(check["pattern"], answer, re.IGNORECASE | re.MULTILINE) is not None
        case "contains":
            ok = all(text.lower() in low for text in check["all"])
        case "excludes":
            ok = not any(text.lower() in low for text in check["any"])
        case "json_keys":
            try:
                parsed = json.loads(unfenced(answer))
            except ValueError:
                parsed = None
            ok = isinstance(parsed, dict) and all(key in parsed for key in check["keys"])
        case "count":
            ok = low.count(check["text"].lower()) == check["equals"]
        case "max_chars":
            ok = len(answer) <= check["n"]
        case _:
            ok = False
    return None if ok else check["kind"]


code, items = [], []
for task in tasks:
    for n, answers in enumerate(tries, 1):
        answer = answers.get(task["id"])
        if answer is None:
            code.append({"id": task["id"], "try": n, "passed": False, "why": "no answer"})
        elif task["grade"]["by"] == "code":
            why = next((f for c in task["grade"]["checks"] if (f := failed_check(c, answer))), None)
            code.append({"id": task["id"], "try": n, "passed": why is None, "why": why})
        else:
            item = {"key": f"{task['id']}#{n}", "prompt": task["prompt"], "answer": answer}
            items.append(item | {"rubric": task["grade"]["rubric"]})
listed = [{"id": t["id"], "graded_by": t["grade"]["by"]} for t in tasks]
print(json.dumps({"tasks": listed, "tries": len(tries), "code": code, "items": items}))
