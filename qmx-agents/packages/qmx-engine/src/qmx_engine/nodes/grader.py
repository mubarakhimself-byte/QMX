"""The `grader` node in `deterministic` mode: a check script reads the input on stdin and prints
`{"verdict": "pass" | "fail", "feedback": ...}`. The node sends the input with the verdict and
feedback on the port the verdict names, and the span records the verdict. The `llm` judge mode
runs once `llm` nodes do (EP10)."""

from __future__ import annotations

from pydantic import JsonValue

from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok
from qmx_engine.nodes.script import HostScript, failed


class Grader:
    def __init__(self, host: HostScript) -> None:
        self.host = host

    async def run(self, job: NodeJob) -> NodeResult:
        parameters = job.node_definition.get("parameters")
        mode = parameters.get("mode") if isinstance(parameters, dict) else None
        if mode != "deterministic":
            return failed(
                "grader_mode_unavailable", "only deterministic graders run", retryable=False
            )
        found = await self.host.run(job, "script")
        if isinstance(found, Failed):
            return found
        verdict = found.get("verdict") if isinstance(found, dict) else None
        if verdict not in ("pass", "fail"):
            return failed(
                "grader_output", "the check printed no pass or fail verdict", retryable=False
            )
        feedback = found.get("feedback") if isinstance(found, dict) else None
        subject: JsonValue = job.inputs.get("in") if isinstance(job.inputs, dict) else None
        graded: JsonValue = {"input": subject, "verdict": verdict, "feedback": feedback}
        return Ok({verdict: graded}, verdict=verdict)
