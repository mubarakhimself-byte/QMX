"""Shared declared adapter boundary used by host grants and MA03 validation."""

from __future__ import annotations

from qma.daemon.request_runtime.spot_state import SPOT_CONTRIBUTION


def declared_operation_point(op_id: str, qualified_id: str) -> str | None:
    if op_id == "qma.procedure.start":
        return "graph_template"
    if op_id in {"qmb.backtest.run", "qmb.optimize.run", "qmb.analysis.project"}:
        return "tool" if qualified_id == "analysis-backtest:qmb" else None
    if op_id == "qmn.spot.paper.query":
        return "tool" if qualified_id == SPOT_CONTRIBUTION else None
    return None
