"""The last check of every template. Its input is the finished output, alone or with the evidence it
was made from. The output is the one input that matches `schemas/output.json`. Every number written
in its prose fields, the schema's `x-prose` keys, must appear in the evidence: the output's other
fields and every other input. A number may be rounded, and single digits are counts, not checked.

Prints the grader verdict. A pass names which input is the output (None when there was one input),
for the deliver step; a failure names each problem."""

import json
import re
import sys
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

NUMBER = re.compile(r"\d+(?:[.,]\d+)*")

schema = json.loads((Path(__file__).parents[1] / "schemas" / "output.json").read_text("utf-8"))
validator = Draft202012Validator(schema)
given = json.load(sys.stdin)["in"]
inputs = given if isinstance(given, list) else [given]


def numbers(value):
    found = []
    if isinstance(value, str):
        found += [Decimal(text.replace(",", "")) for text in NUMBER.findall(value)]
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


outputs = [i for i, value in enumerate(inputs) if not list(validator.iter_errors(value))]
if len(outputs) != 1:
    errors = [
        f"{'/'.join(map(str, e.absolute_path)) or 'output'}: {e.message}"
        for value in inputs
        for e in list(validator.iter_errors(value))[:3]
    ]
    feedback = {"problems": [f"{len(outputs)} inputs match the output schema", *errors[:6]]}
    print(json.dumps({"verdict": "fail", "feedback": feedback}))
    raise SystemExit(0)

output = inputs[outputs[0]]
prose_keys = schema.get("x-prose", [])
prose = {key: output.get(key) for key in prose_keys}
evidence = numbers({k: v for k, v in output.items() if k not in prose_keys})
evidence += numbers([value for i, value in enumerate(inputs) if i != outputs[0]])
checked = [n for n in numbers(prose) if n >= 10 or n != n.to_integral_value()]
unresolved = sorted({str(n) for n in checked if not resolves(n, evidence)})
if unresolved:
    feedback = {"problems": [f"numbers not found in the evidence: {', '.join(unresolved)}"]}
    print(json.dumps({"verdict": "fail", "feedback": feedback}))
else:
    at = outputs[0] if isinstance(given, list) else None
    print(
        json.dumps({"verdict": "pass", "feedback": {"numbers_checked": len(checked), "output": at}})
    )
