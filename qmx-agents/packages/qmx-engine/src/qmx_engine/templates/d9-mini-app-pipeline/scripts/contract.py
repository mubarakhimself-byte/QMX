"""The contract test on recorded fixtures (card D9 step 4 and its gates). Its inputs, the apps
read, the compatibility check and any transform, are told apart by shape.

The producer's recorded artifact is validated against its own `provides` schema first: a run never
consumes an unvalidated artifact. Then it passes through the transform (a field mapping; none when
the schemas already match) and the result must validate against the consumer's `feeds` schema.
"""

import json
import sys

from jsonschema import Draft202012Validator

given = json.load(sys.stdin)["in"]
apps = next(v for v in given if "fixture" in v)
compat = next(v for v in given if "compatible" in v)
transform = next((v for v in given if "mapping" in v), None)


def read(value, path):
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def errors(schema, value):
    return [e.message for e in Draft202012Validator(schema).iter_errors(value)][:5]


producer_errors = errors(apps["provides"], apps["fixture"])
if transform is None:
    shaped = apps["fixture"]
else:
    shaped = {
        m["field"]: read(apps["fixture"], m["from"]) if "from" in m else m.get("value")
        for m in transform["mapping"]
    }
consumer_errors = errors(apps["feeds"], shaped)
unmapped = transform["unmapped"] if transform else []
passed = not compat["problems"] and not producer_errors and not consumer_errors and not unmapped
print(
    json.dumps(
        {
            "passed": passed,
            "producer_errors": producer_errors,
            "consumer_errors": consumer_errors,
            "unmapped": unmapped,
            "transform": transform["mapping"] if transform else None,
            "problems": compat["problems"],
            "producer_version": apps["producer"]["version"],
            "consumer_version": apps["consumer"]["version"],
        }
    )
)
