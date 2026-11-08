"""The verdict as the Library holds it, for the rule to route on. Zero tokens. The same file in
every template that asks the referee.

Its inputs are `scripts/hand.py`'s answer and what the `library` node read. It prints `overall`,
the stored outcome; `unit`, the unit it judged; `verdict`, the fields the later steps read, every
value the Library's; and `cards`, the core's papers on this verdict by kind, each with its
`object_id`.

A model's copy decides nothing here. The run stops, by name, when the object is not a verdict, when
it judged another unit, when it judged other results than the referee named or other runs than this
run's, which is a true verdict of an earlier run, or when a paper its outcome calls for is missing
or names another verdict.

A recorded run has no real verdict to read, so its replay lands stand-ins on its own ref, and they
read as the kinds they stand for. That holds only in a test run: a `fixture` on a live run stops
here, so no stand-in ever routes.
"""

import json
import os
import sys

FAILURE = "[QMX_FAILURE]"
PAPERS = {
    "pass": ("baseline-card", "proposal-card"),
    "fail": ("death-certificate",),
    "no_trades": ("death-certificate",),
}
"""What the core's `land_judgement` lands for each outcome. The others wait, and land none."""


def refuse(why):
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


given = json.load(sys.stdin)["in"]
rows = []
for value in given if isinstance(given, list) else [given]:
    rows += value if isinstance(value, list) else [value]
hand = next(r for r in rows if "refs" in r)
read = [r for r in rows if "ref" in r]
recorded = hand["recorded"]
if recorded and os.environ["QMX_MODE"] != "test":
    refuse("this live run names a fixture, and a recorded verdict stands only in a test run")


def held(row):
    """The row's kind and fields, a stand-in's as what it stands for."""
    if not recorded:
        return row["kind"], row["fields"]
    fields = {k: v for k, v in row["fields"]["metadata"].items() if k != "write_key"}
    return row["fields"]["type"], fields


found = next(r for r in read if r["ref"] == hand["verdict"])
verdict_id = found["object_id"]
kind, verdict = held(found)
if kind != "verdict":
    refuse(f"{verdict_id} is a {kind}, not a verdict")
if not recorded:
    if verdict.get("unit") != hand["unit"]:
        refuse(
            f"the verdict {verdict_id} judged {verdict.get('unit')}, and this run tested "
            f"{hand['unit']}"
        )
    results = {
        r["object_id"]: r["fields"].get("run_id") for r in read if r["kind"] == "backtest-result"
    }
    if sorted(verdict["results"]) != sorted(results):
        refuse(f"the verdict {verdict_id} judged other results than the referee named")
    if sorted(set(results.values())) != sorted(set(hand["runs"])):
        refuse(f"the verdict {verdict_id} judged other runs than this run's")
overall = verdict["overall"]
cards = {}
for row in read:
    paper, fields = held(row)
    ours = recorded or fields.get("verdict") == verdict_id
    if ours and paper in PAPERS["pass"] + PAPERS["fail"]:
        cards[paper] = {"object_id": row["object_id"], **fields}
missing = [paper for paper in PAPERS.get(overall, ()) if paper not in cards]
if missing:
    refuse(f"the verdict {verdict_id} is {overall}, and the referee named no {missing[0]} of it")
print(
    json.dumps(
        {
            "overall": overall,
            "unit": verdict["unit"],
            "verdict": {
                "verdict_id": verdict_id,
                "result_ids": verdict["results"],
                **{
                    name: verdict[name]
                    for name in ("overall", "says", "raw_tries", "effective_tries", "per_market")
                },
            },
            "cards": cards,
        }
    )
)
