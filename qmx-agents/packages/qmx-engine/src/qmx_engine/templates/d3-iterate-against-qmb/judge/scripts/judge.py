"""The `judge` block's one step: the core's verdict on landed results, decided by script (Part B
AD-207). Agents explain the verdict after this step; none of them decides it.

Its input is `{"in": {...}}` with `spec` (a study spec's fields), `study` (its id), `results` (each
`{result_id, fields, trades}`, the trades from the result's report), `tries` (the fields of every
`try` of the results' families), `family` (other landed results of those families, the same shape
as `results`), `principal` (who asked) and `checker` (the checker version). It prints the verdict's
fields, its item and its plain words. Landing the verdict is the calling template's `library`
step; a refusal fails this step with every problem.
"""

import json
import sys

from qmx_judge.judge import JudgedResult, JudgeRefused, judge, parse_spec

given = json.load(sys.stdin)["in"]
given = next((v for v in (given if isinstance(given, list) else [given]) if "spec" in v), None)
if not isinstance(given, dict):
    print("[QMX_FAILURE] the judge block needs a study spec, its results and their tries")
    raise SystemExit(0)


def read(rows):
    return [JudgedResult.read(r["result_id"], r["fields"], r.get("trades", [])) for r in rows]


try:
    verdict = judge(
        parse_spec(given["spec"]),
        study=given["study"],
        results=read(given["results"]),
        tries=given.get("tries", []),
        family=read(given.get("family", [])),
        principal=given.get("principal", "workflow"),
        versions={"checker": given.get("checker", "")},
    )
except JudgeRefused as refused:
    print(f"[QMX_FAILURE] {'; '.join(refused.problems)}")
    raise SystemExit(0) from None
print(json.dumps({"item": verdict.item, "verdict": verdict.fields(), "says": verdict.says()}))
