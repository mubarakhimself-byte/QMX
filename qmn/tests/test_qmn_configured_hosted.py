"""Assessed host resources remain bound to the full compiled node config."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TypeVar

from qmf.core import Result, is_ok, is_refusal
from qmn.config.compiler import ResolvedNodeConfig, compile_node_config
from qmn.host.configured_hosted import validate_assessed_path_config

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_path_uses_exact_full_assessed_config_rows() -> None:
    assessed = _ok(compile_node_config())
    path = SimpleNamespace(resolved_node_config=assessed)

    assert is_ok(validate_assessed_path_config(path, assessed))

    different = _ok(compile_node_config(config_version=2))
    refused = validate_assessed_path_config(
        SimpleNamespace(resolved_node_config=different), assessed
    )
    assert is_refusal(refused)
    assert refused.context.get("field") == "node_config"


def test_path_config_refuses_absence_and_stale_declared_identity() -> None:
    assessed = _ok(compile_node_config())
    absent = validate_assessed_path_config(SimpleNamespace(), assessed)
    assert is_refusal(absent)

    stale = ResolvedNodeConfig(
        format_version=assessed.format_version,
        config_version=assessed.config_version + 1,
        rows=assessed.rows,
        fingerprint=assessed.fingerprint,
        roster_identity=assessed.roster_identity,
        branches_from=assessed.branches_from,
    )
    refused = validate_assessed_path_config(SimpleNamespace(resolved_node_config=stale), assessed)
    assert is_refusal(refused)
    assert refused.context.get("field") == "node_config"
