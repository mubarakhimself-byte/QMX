"""The failure ladder's doctor (AD-16, SOLUTION-DESIGN 10.2): one `llm` call on the `doctor` role
that classifies a failed attempt from its slot's events. It never edits a definition. Any answer it
cannot give becomes `unavailable`, which parks the slot.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast, get_args

from pydantic import JsonValue

from qmx_engine.admission import Admission
from qmx_engine.nodes.base import Ok
from qmx_engine.nodes.llm import call
from qmx_engine.ports.harness_adapter import HarnessPort
from qmx_engine.roles import order, resolve
from qmx_engine.runner import Classification, Consult, Engine, Verdict, workspace

ROLE: Final = "doctor"
RUN_SECONDS: Final = 300.0
EVENT_KEYS: Final = ("code", "message", "reason", "step", "classification", "hint")
SCHEMA: Final[dict[str, JsonValue]] = {
    "type": "object",
    "properties": {
        "classification": {"enum": list[JsonValue](get_args(Classification.__value__))},
        "hint": {"type": ["string", "null"]},
    },
    "required": ["classification", "hint"],
}
PROMPT: Final = (
    "You are the doctor of a workflow engine. A node attempt failed. Classify the failure as one "
    "of: transient (a retry may pass), bad_input (its input is wrong), bad_output (the model's "
    "answer had the wrong shape), logic (the node's own definition is wrong), unavailable (you "
    "cannot tell). Give a one-sentence hint for the next attempt, or null."
)


def consult_text(consult: Consult) -> str:
    events = [
        {"kind": e.kind, **{k: e.data[k] for k in EVENT_KEYS if k in e.data}}
        for e in consult.events
        if e.kind in ("node_failed", "ladder_step", "doctor_verdict")
    ]
    lines = [
        PROMPT,
        "Reply with exactly one JSON document that matches this JSON schema, and nothing else:\n"
        + json.dumps(SCHEMA, sort_keys=True),
        "The node:\n" + json.dumps(consult.node_definition, sort_keys=True),
        "What happened to it:\n" + json.dumps(events, sort_keys=True),
    ]
    return "\n\n".join(lines)


class LlmDoctor:
    def __init__(
        self,
        harness: HarnessPort,
        admission: Admission,
        settings: Mapping[str, object],
        workspace: Path,
    ) -> None:
        self.harness = harness
        self.admission = admission
        self.settings = settings
        self.workspace = workspace

    @classmethod
    def of(cls, engine: Engine) -> LlmDoctor | None:
        """The doctor of an engine that has a harness; None for one without."""
        if engine.harness is None or engine.admission is None:
            return None
        doctors = workspace(engine.home, "engine-doctor")
        return cls(engine.harness, engine.admission, engine.settings, doctors)

    async def classify(self, consult: Consult) -> Verdict:
        candidates = order(self.settings, ROLE, consult.mode)
        candidate = resolve(candidates, self.harness.profiles(), None)
        if isinstance(candidate, str):
            return Verdict("unavailable", candidate)
        slot = consult.slot
        title = f"{consult.run_id}:{slot.node_id}:{slot.iteration}:{slot.partition}:"
        result = await call(
            self.harness,
            self.admission,
            candidate,
            title=f"{title}{consult.attempt}:doctor",
            text=consult_text(consult),
            schema=SCHEMA,
            workspace=self.workspace,
            run_seconds=RUN_SECONDS,
        )
        if not isinstance(result, Ok) or not isinstance(found := result.outputs["main"], dict):
            return Verdict("unavailable")
        hint = found.get("hint")
        return Verdict(
            cast(Classification, found["classification"]),
            hint if isinstance(hint, str) else None,
        )
