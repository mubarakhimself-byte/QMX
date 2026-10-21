"""What each try sees: the slot text and every task's id and prompt. The grade stays out, so no try
is shown the answer it is graded against."""

import json
import sys

given = json.load(sys.stdin)["in"]
tasks = [{"id": task["id"], "prompt": task["prompt"]} for task in given["tasks"]]
print(json.dumps({"surface": given["surface"], "tasks": tasks}))
