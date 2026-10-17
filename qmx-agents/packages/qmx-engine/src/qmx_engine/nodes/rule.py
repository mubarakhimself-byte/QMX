"""The `rule` node: a safe expression (`qmx_engine.definition.expr`) over its inputs that routes to
the `true` or `false` port."""

from __future__ import annotations

from qmx_engine.definition.expr import RuleError, RuleRefused, evaluate
from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok


def _failed(code: str, message: str) -> Failed:
    return Failed(code, message, signature(code, message), retryable=False)


class Rule:
    def run(self, job: NodeJob) -> NodeResult:
        parameters = job.node_definition.get("parameters")
        expr = parameters.get("expr") if isinstance(parameters, dict) else None
        if not isinstance(expr, str):
            return _failed("rule_refused", "parameters.expr is not a string")
        try:
            routed = evaluate(expr, job.inputs)
        except RuleRefused as error:
            return _failed("rule_refused", str(error))
        except RuleError as error:
            return _failed("rule_error", str(error))
        ports = job.inputs if isinstance(job.inputs, dict) else {}
        return Ok({"true" if routed else "false": ports.get("in")})
