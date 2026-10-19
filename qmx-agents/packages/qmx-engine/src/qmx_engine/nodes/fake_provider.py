"""The fake provider (SOLUTION-DESIGN 6.2, 9): the `llm` and `agent` executor that calls no model,
for a no-spend dry run (B-77). It runs only when a run is started with the explicit `fake` switch;
`mode: test` alone never selects it (ruling 51).

It answers with the node's pinned data when the test run has some, else the recorded answer file
`parameters.recording_ref`, else a canned document built from the node's schema (`schema_ref`, or
an agent's `output_schema_ref`). A chunk of a `chunk` edge gets the recorded answer cut to its own
items, as a real model answers only what it was given (B-85): each list in the answer keeps the
entries whose `*_id` field names an `id` of an item in the chunk, and an answer whose entries name
no item id is kept whole.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import JsonValue

from qmx_engine.nodes.base import NodeJob, NodeResult, Ok
from qmx_engine.nodes.llm import node_schema, read_ref
from qmx_engine.nodes.script import failed

type JsonObject = dict[str, JsonValue]

PROFILE = "fake"


def canned(schema: JsonValue) -> JsonValue:
    """The smallest document of the schema's shape: each required property, `const`, the first
    `enum` value, or the type's empty value."""
    if not isinstance(schema, dict):
        return None
    if "const" in schema:
        return schema["const"]
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return enum[0]
    kind = schema.get("type")
    kind = kind[0] if isinstance(kind, list) and kind else kind
    match kind:
        case "object":
            properties = schema.get("properties")
            required = schema.get("required")
            props: JsonObject = properties if isinstance(properties, dict) else {}
            names = required if isinstance(required, list) else list(props)
            return {str(n): canned(props.get(str(n))) for n in names}
        case "array":
            return []
        case "string":
            return ""
        case "integer" | "number":
            return 0
        case "boolean":
            return False
        case _:
            return None


class FakeProvider:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def run(self, job: NodeJob) -> NodeResult:
        if job.pinned_outputs is not None:
            return Ok(job.pinned_outputs, span={"fake": "pinned"})
        found = job.node_definition.get("parameters")
        parameters: JsonObject = found if isinstance(found, dict) else {}
        recorded = read_ref(self.root, parameters, "recording_ref")
        if recorded is not None:
            try:
                answer: JsonValue = json.loads(recorded)
            except ValueError:
                return failed("bad_definition", "recording_ref is not JSON", retryable=False)
            if job.partition is not None:
                answer = own_items(answer, job.inputs)
            return Ok({"main": answer}, span={"fake": "recorded"})
        schema = node_schema(self.root, parameters) or node_schema(
            self.root, parameters, "output_schema_ref"
        )
        if schema is None:
            return failed("bad_definition", "a model node needs a JSON schema", retryable=False)
        return Ok({"main": canned(schema)}, span={"fake": "canned"})


def own_items(answer: JsonValue, inputs: JsonValue) -> JsonValue:
    """The answer with each top-level list cut to the entries that name an item of this chunk."""
    given = inputs.get("in") if isinstance(inputs, dict) else None
    items = given if isinstance(given, list) else []
    ids = {
        found
        for item in items
        if isinstance(item, dict) and isinstance(found := item.get("id"), str)
    }
    if not ids or not isinstance(answer, dict):
        return answer
    cut: JsonObject = {}
    for key, value in answer.items():
        if isinstance(value, list) and any(isinstance(e, dict) and refs(e) for e in value):
            cut[key] = [e for e in value if not isinstance(e, dict) or refs(e) & ids]
        else:
            cut[key] = value
    return cut


def refs(entry: JsonObject) -> set[str]:
    return {v for k, v in entry.items() if k.endswith("_id") and isinstance(v, str)}
