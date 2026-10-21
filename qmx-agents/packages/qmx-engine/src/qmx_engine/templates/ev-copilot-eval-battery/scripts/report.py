"""pass^3 per task: a task passes only when every one of its three tries passed (engine AD-66).

Its input is the code verdicts and the judge's verdicts. A judged try the judge gave no verdict
for fails. Prints each task's tries in order, its pass^3, why each failed try failed, and the
count of tasks that passed."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
graded = next(v for v in given if isinstance(v, dict) and "code" in v)
judged = next((v for v in given if isinstance(v, dict) and "verdicts" in v), {"verdicts": []})
verdicts = {str(v.get("key")): v for v in judged["verdicts"]}

found = []
for task in graded["tasks"]:
    tries = []
    for n in range(1, graded["tries"] + 1):
        if task["graded_by"] == "code":
            seen = next(c for c in graded["code"] if c["id"] == task["id"] and c["try"] == n)
            tries.append({"passed": seen["passed"], "why": seen["why"]})
        else:
            verdict = verdicts.get(f"{task['id']}#{n}")
            coded = next(
                (c for c in graded["code"] if c["id"] == task["id"] and c["try"] == n), None
            )
            if coded is not None:
                tries.append({"passed": False, "why": coded["why"]})
            elif verdict is None:
                tries.append({"passed": False, "why": "the judge gave no verdict"})
            else:
                passed = verdict.get("verdict") == "pass"
                tries.append({"passed": passed, "why": None if passed else verdict.get("why")})
    found.append(
        {
            "id": task["id"],
            "graded_by": task["graded_by"],
            "tries": [t["passed"] for t in tries],
            "pass3": len(tries) == 3 and all(t["passed"] for t in tries),
            "why": [t["why"] for t in tries if not t["passed"]],
        }
    )
passed = sum(t["pass3"] for t in found)
print(json.dumps({"tasks": found, "passed": passed, "total": len(found)}))
