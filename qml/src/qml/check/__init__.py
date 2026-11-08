"""The unit checker (AD-110): layers A to F, the ``qmx.check/1`` result, and layer G's functions.

``check`` runs every layer that can run and names every problem at once. Layer G lives in
``qml.check.layer_g``, imported on its own, because it drives a compiled unit.
"""

from __future__ import annotations

from qml.check.layers import Found, check_block, check_layers
from qml.check.result import CHECK_SCHEMA, CHECKER_FORMAT_VERSION, CheckResult, Verdict
from qml.check.run import check, check_and_compile

__all__ = [
    "CHECKER_FORMAT_VERSION",
    "CHECK_SCHEMA",
    "CheckResult",
    "Found",
    "Verdict",
    "check",
    "check_and_compile",
    "check_block",
    "check_layers",
]
