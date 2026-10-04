"""Example composition root for an explicitly supplied operator analysis source.

The operator's module:function returns (CT-32, CT29ProjectionSource) in an Ok.
It supplies locators, never admission evidence: project() still reopens CT-10/12,
CT-13 and the terminal ledger and verifies every provenance relationship.
The shipped examples contain no invented durable rows or test-module imports.
"""

from __future__ import annotations

import argparse
import importlib
from collections.abc import Callable
from pathlib import Path
from typing import cast

from qmb.analysis import CT29ProjectionSource
from qmf.core.refusal import Result, is_ok


def operator_analysis_source() -> tuple[object, CT29ProjectionSource]:
    parser = argparse.ArgumentParser(description="Read the operator's completed recorded replay")
    parser.add_argument("--operator-builder", required=True, help="Trusted local module:function")
    parser.add_argument("--runtime-root", required=True, type=Path)
    args = parser.parse_args()
    module_name, separator, entrypoint = str(args.operator_builder).partition(":")
    if not separator or not module_name or not entrypoint:
        parser.error("--operator-builder uses module:function")
    module = importlib.import_module(module_name)
    candidate: object = getattr(module, entrypoint, None)
    if not callable(candidate):
        parser.error("the operator builder names a callable")
    builder = cast(Callable[[Path], Result[object]], candidate)
    result = builder(args.runtime_root)
    if not is_ok(result):
        raise ValueError(f"operator source could not be reopened: {result}")
    raw: object = result.value
    if type(raw) is not tuple:
        raise TypeError("operator builder returns a CT-32 and its CT-13 source locator")
    pair = cast(tuple[object, ...], raw)
    if len(pair) != 2:
        raise TypeError("operator builder returns a CT-32 and its CT-13 source locator")
    artifact, source = pair
    if not isinstance(source, CT29ProjectionSource):
        raise TypeError("operator source must supply a CT-13 reader locator")
    return artifact, source
