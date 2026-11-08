"""The `proposal-card` block's one step: land what waits for his click as a card (Part B AD-213).

Its input is `{"in": {"proposal": {...}}}` with `subject` (the unit, market or version the
proposal is about), `ask` (one of the `proposal-card` kind's asks, such as `paper`), `evidence`
(the Library object ids it rests on, at least one), and optionally `why`, `cost` (an object, such
as the tokens and backtests spent), `verdict`, `tries`, `preset` and `placeholders`.

It lands one `artifact` of type `proposal-card` on the run's own ref, with the kind's fields and
`made_by` set to this run, and prints the card. It moves nothing: no unit, no ref on `main`, no
lifecycle row. Publishing, paper and live are his clicks. A proposal missing a field fails the
step with every problem named.
"""

import json
import os
import sys
from importlib.resources import files
from pathlib import Path

FAILURE = "[QMX_FAILURE]"
KIND = json.loads(
    (files("qmx_library") / "kinds" / "proposal-card.schema.json").read_text(encoding="utf-8")
)
ASKS = KIND["fields"]["properties"]["ask"]["enum"]
CARRIED = ("why", "cost", "verdict", "tries", "preset", "placeholders")

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
proposal = next((r["proposal"] for r in rows if isinstance(r.get("proposal"), dict)), None)
if proposal is None:
    print(f"{FAILURE} the proposal-card block needs a proposal")
    raise SystemExit(0)

problems = []
subject, ask, evidence = proposal.get("subject"), proposal.get("ask"), proposal.get("evidence")
if not isinstance(subject, str) or not subject:
    problems.append("subject names no unit, market or version")
if ask not in ASKS:
    problems.append(f"ask {ask!r} is not one of {', '.join(ASKS)}")
if not isinstance(evidence, list) or not evidence or not all(isinstance(e, str) for e in evidence):
    problems.append("evidence lists no Library object id")
if "cost" in proposal and not isinstance(proposal["cost"], dict):
    problems.append("cost is not an object")
if problems:
    print(f"{FAILURE} {'; '.join(problems)}")
    raise SystemExit(0)

run_id = os.environ["QMX_RUN_ID"]
card = {
    "subject": subject,
    "ask": ask,
    "evidence": evidence,
    **{key: proposal[key] for key in CARRIED if key in proposal},
    "made_by": f"run:{run_id}",
}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "proposal-card.json").write_text(json.dumps(card, sort_keys=True), encoding="utf-8")
write = {
    "op": "put_artifact",
    "type": "proposal-card",
    "body": "library/proposal-card.json",
    "metadata": card,
    "intent_key": f"proposal|{subject}|{ask}|{'|'.join(sorted(evidence))}",
}
print(json.dumps({"card": card, "library": [write]}))
