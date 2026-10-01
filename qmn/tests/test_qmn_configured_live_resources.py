"""The installed resolver rejects replay-only profiles as LIVE resources."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from qmf.core import Result, is_ok, is_refusal
from qmn.host.configured_live_resources import resolve_configured_live_resources
from qmn.host.configured_runtime import assess_configured_runtime
from test_qmn_configured_composition import (
    offline_profile,
    valid_deployment,
    write_v2_deployment,
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_closed_resolver_refuses_missing_profile(tmp_path: Path) -> None:
    deployment = valid_deployment(tmp_path)
    assessment = _ok(assess_configured_runtime(deployment, qmx_root=tmp_path))

    refused = resolve_configured_live_resources(assessment)

    assert is_refusal(refused)
    assert refused.context.get("failure_id") == "configured_runtime.host_profile_missing"


def test_closed_resolver_validates_then_refuses_replay_profile_for_live(
    tmp_path: Path,
) -> None:
    initial = _ok(assess_configured_runtime(valid_deployment(tmp_path), qmx_root=tmp_path))
    deployment = write_v2_deployment(tmp_path, offline_profile(initial, tmp_path))
    assessment = _ok(assess_configured_runtime(deployment, qmx_root=tmp_path))

    refused = resolve_configured_live_resources(assessment)

    assert is_refusal(refused)
    assert refused.context.get("failure_id") == "configured_runtime.hosted_resources_missing"
    assert "QMB replay evidence" in str(refused.context.get("reason"))
