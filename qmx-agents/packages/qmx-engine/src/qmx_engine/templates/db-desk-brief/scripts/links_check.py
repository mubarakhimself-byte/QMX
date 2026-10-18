"""The writer's check: every watch line links to a source the gather found, every decision names a
run the gather listed, and there are no more decisions than items waiting on him, so the writer can
neither invent a source nor a decision. Its inputs, the ranked day and the writer's brief, are told
apart by shape. Prints the verdict and each problem."""

import json
import sys

given = json.load(sys.stdin)["in"]
day = next(v for v in given if "ranked" in v)
brief = next(v for v in given if "headline" in v)
links = {item["link"] for item in day["ranked"] if item.get("link")}
runs = {item["run_id"] for item in day["ranked"] if item["kind"] == "decision"}
problems = [
    f"watch line {n} links to a source the gather did not find: {line['link']}"
    for n, line in enumerate(brief["watch_today"], start=1)
    if line["link"] not in links
]
problems += [
    f"decision {n} names a run with nothing waiting: {decision['run_id']}"
    for n, decision in enumerate(brief["decisions"], start=1)
    if decision["run_id"] not in runs
]
if len(brief["decisions"]) > len(runs):
    problems.append(f"{len(brief['decisions'])} decisions for {len(runs)} items waiting on him")
verdict = "fail" if problems else "pass"
print(json.dumps({"verdict": verdict, "feedback": {"problems": problems}}))
