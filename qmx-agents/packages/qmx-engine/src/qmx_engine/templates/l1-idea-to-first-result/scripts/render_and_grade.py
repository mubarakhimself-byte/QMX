"""The last check of every template. Its input is the finished output, alone or with what it was
made from. The output is the one input that matches `schemas/output.json`. Every number written in
its prose fields, the schema's `x-prose` keys, must appear in the run's evidence set (engine AD-45).

The evidence set is what the run recorded and no model wrote: the inputs the run was pinned to, and
the output of every node whose kind is not `llm`, `agent`, `sandbox_python`, `sandbox_bash` or
`agent-tool`. A model's output is never evidence for a number it states, and neither is the output
being graded. Timestamps, dates, times, run ids, hashes and version strings are cut from both sides
before a number is compared, so a year that appears only in a timestamp is no evidence. A number may
be rounded, and single digits are counts, not checked.

Prints the verdict. A pass names which input is the output, for the deliver step; a failure names
each problem."""

import json
import os
import re
import sys
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from qmx_engine.ledger.store import Reader
from qmx_engine.workers.zones import home_of

NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
CUT = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"
    r"|\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{2}:\d{2}(?::\d{2})?\b"
    r"|\b[0-9a-f]{16,}\b"
    r"|\b\d+\.\d+\.\d+\b"
    r"|\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b"
)
"""A timestamp, a date, a time, a hex digest, a semver or a uuid, all of which a run writes and no
source states."""
MODEL_WRITTEN = frozenset({"llm", "agent", "sandbox_python", "sandbox_bash", "agent-tool"})
"""The node kinds whose output no source states: a model wrote it, or a model wrote the code."""

schema = json.loads((Path(__file__).parents[1] / "schemas" / "output.json").read_text("utf-8"))
validator = Draft202012Validator(schema)
given = json.load(sys.stdin)["in"]


def flat(given):
    """The inputs, with each grader's envelope opened, so a check before this one passes on what it
    checked."""
    found = []
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and set(value) == {"input", "verdict", "feedback"}:
            found += flat(value["input"])
        else:
            found.append(value)
    return found


inputs = flat(given)


def cut(value):
    """`value` with every run-written stamp removed, at any depth."""
    if isinstance(value, str):
        return CUT.sub(" ", value)
    if isinstance(value, dict):
        return {key: cut(item) for key, item in value.items()}
    if isinstance(value, list):
        return [cut(item) for item in value]
    return value


def numbers(value):
    found = []
    if isinstance(value, str):
        found += [Decimal(text.replace(",", "")) for text in NUMBER.findall(cut(value))]
    elif isinstance(value, bool) or value is None:
        pass
    elif isinstance(value, int | float):
        found.append(abs(Decimal(str(value))))
    elif isinstance(value, dict):
        for item in value.values():
            found += numbers(item)
    elif isinstance(value, list):
        for item in value:
            found += numbers(item)
    return found


def resolves(number, evidence):
    places = max(-number.as_tuple().exponent, 0)
    return any(round(seen, places) == number for seen in evidence)


def model_written():
    """Every value a model wrote in this run, as canonical JSON: the output of each `llm`, `agent`,
    `sandbox_python`, `sandbox_bash` or `agent-tool` node. None of them is evidence for a number."""
    home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
    run_id = os.environ["QMX_RUN_ID"]
    definition = json.loads((Path(os.environ["QMX_CODE"]) / "definition.json").read_text("utf-8"))
    kinds = {node["id"]: node["type"] for node in definition["nodes"]}
    found = set()
    with Reader.open(home) as reader:
        for event in reader.events(run_id):
            if event.kind != "node_finished":
                continue
            if kinds.get(event.data.get("node_id")) not in MODEL_WRITTEN:
                continue
            value = (event.data.get("outputs") or {}).get("main")
            found.add(json.dumps(value, sort_keys=True))
    return found


def fail(problems):
    print(json.dumps({"verdict": "fail", "feedback": {"problems": problems}}))
    raise SystemExit(0)


outputs = [i for i, value in enumerate(inputs) if not list(validator.iter_errors(value))]
if len(outputs) != 1:
    errors = [
        f"{'/'.join(map(str, e.absolute_path)) or 'output'}: {e.message}"
        for value in inputs
        for e in list(validator.iter_errors(value))[:3]
    ]
    fail([f"{len(outputs)} inputs match the output schema", *errors[:6]])

output = inputs[outputs[0]]
prose_keys = schema.get("x-prose", [])
prose = cut({key: output.get(key) for key in prose_keys})
mine = model_written()
evidence = numbers(cut({key: value for key, value in output.items() if key not in prose_keys}))
evidence += numbers(
    [
        value
        for i, value in enumerate(inputs)
        if i != outputs[0] and json.dumps(value, sort_keys=True) not in mine
    ]
)
checked = [n for n in numbers(prose) if n >= 10 or n != n.to_integral_value()]
unresolved = sorted({str(n) for n in checked if not resolves(n, evidence)})
if unresolved:
    fail([f"numbers not found in the evidence: {', '.join(unresolved)}"])
print(
    json.dumps(
        {
            "verdict": "pass",
            "feedback": {"numbers_checked": len(checked), "output": outputs[0]},
        }
    )
)
