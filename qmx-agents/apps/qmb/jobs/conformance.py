"""The `conformance` run kind, which the contract requires and B12 fills with its golden pack."""

from __future__ import annotations

from collections.abc import Mapping

import qmb_tester as tester


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    return tester.failed(str(inputs["run_id"]), "conformance pack arrives in B12")
