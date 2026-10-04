"""Exclusive operator composition selection for authenticated QMA run envelopes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import cast

from qmf.core import Ok, Result, is_refusal

from qmb._refuse import invalid, policy, unavailable
from qmb.host.operator_alternative_replay import (
    execute_operator_alternative_replay,
    read_operator_alternative_binding,
    verify_operator_alternative_result,
)
from qmb.host.operator_replay import (
    execute_operator_replay,
    project_operator_replay,
    read_operator_replay_binding,
    verify_operator_replay_result,
)
from qmb.host.operator_study_replay import invoke_operator_study, select_operator_composition
from qmb.host.qma_cli import decode_qma_backtest_context


def invoke_delegated_run(
    *, command: str, environ: Mapping[str, str], caller_values: tuple[object, ...]
) -> Result[Mapping[str, object]]:
    decoded = decode_qma_backtest_context(
        payload_text=environ.get("QMA_QMB_DOOR_PAYLOAD"), environ=environ
    )
    if is_refusal(decoded):
        return decoded
    context = decoded.value
    if context.command != command or any(value is not None for value in caller_values):
        return policy("qma_payload", "QMA envelope matches the door without caller runtime values")
    root = environ.get("QMB_REPLAY_RUNTIME_ROOT")
    if root is None:
        return unavailable("operator_runtime", "QMB has no operator-owned replay runtime root")
    selected = select_operator_composition(runtime_root=root, context=context)
    if is_refusal(selected):
        return selected
    composition = selected.value
    if (command == "optimize.run") != (composition == "alternative-study"):
        return policy("command", "optimize selects Study; backtest selects Book or Alternative")
    preflight = environ.get("QMA_QMB_PREFLIGHT") == "1"
    verify = environ.get("QMA_QMB_VERIFY") == "1"
    if preflight and verify:
        return policy("qmb_cli_mode", "preflight and verification are distinct invocations")
    if preflight:
        if context.operator_descriptor_fp1 is not None:
            return policy("operator_descriptor_fp1", "preflight does not accept a caller pin")
        study: Mapping[str, object] = {}
        if composition == "alternative-study":
            prepared = invoke_operator_study(runtime_root=root, context=context, mode="preflight")
            if is_refusal(prepared):
                return prepared
            study = prepared.value
            descriptor = study["operator_descriptor_fp1"]
        elif composition == "alternative":
            binding = read_operator_alternative_binding(
                runtime_root=root, context=replace(context, mints_ct32=False)
            )
            if is_refusal(binding):
                return binding
            descriptor = binding.value.descriptor_fp1.value
        else:
            binding = read_operator_replay_binding(
                runtime_root=root, context=replace(context, mints_ct32=True)
            )
            if is_refusal(binding):
                return binding
            descriptor = binding.value.descriptor_fp1.value
        return Ok(
            {
                "class": "qmb-runtime-preflight-v1",
                "format_version": 1,
                "job_id": context.job_id,
                "attempt_id": context.attempt_id,
                "environment_ref": context.environment_ref,
                "occupancy_key": context.occupancy_key,
                "experiment_spec_fp1": context.experiment_spec_fp1.value,
                "evidence_ref": context.evidence_ref.value,
                "split_manifest_fp1": context.split_manifest_fp1.value,
                "composition_class": composition,
                "mints_ct32": composition == "book",
                "operator_descriptor_fp1": descriptor,
                **study,
            }
        )
    if context.operator_descriptor_fp1 is None:
        return policy(
            "operator_descriptor_fp1", "execution and verification retain the preflight pin"
        )
    claimed: object = None
    if verify and environ.get("QMA_QMB_VERIFY_DURABLE") != "1":
        path = environ.get("QMA_QMB_VERIFY_CLAIM_FILE")
        if path is None or not Path(path).is_absolute():
            return invalid("claimed_result", "QMA verification supplies an absolute claim file")
        try:
            claim = Path(path)
            if claim.is_symlink() or claim.stat().st_size > 262_144:
                return invalid("claimed_result", "claim is regular bounded JSON")
            claimed = json.loads(claim.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
            if not isinstance(claimed, Mapping):
                return invalid("claimed_result", "claim is a JSON object")
            claimed = cast(Mapping[str, object], claimed)
        except (OSError, ValueError, TypeError) as exc:
            return invalid("claimed_result", "claim is strict JSON", error=str(exc))
    if composition == "alternative-study":
        cancel_file = environ.get("QMA_QMB_CANCEL_PATH")
        return invoke_operator_study(
            runtime_root=root,
            context=context,
            mode="verify" if verify else "execute",
            claimed_result=claimed,
            cancelled=lambda: bool(cancel_file and Path(cancel_file).exists()),
        )
    if composition == "alternative":
        return (
            verify_operator_alternative_result(
                runtime_root=root, context=context, claimed_result=claimed
            )
            if verify
            else execute_operator_alternative_replay(runtime_root=root, context=context)
        )
    return (
        verify_operator_replay_result(runtime_root=root, context=context, claimed_result=claimed)
        if verify
        else execute_operator_replay(runtime_root=root, context=context)
    )


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def invoke_delegated_projection(*, environ: Mapping[str, str]) -> Result[Mapping[str, object]]:
    """Reopen the original pinned Book context; this read never publishes evidence."""
    try:
        raw = json.loads(environ.get("QMA_QMB_DOOR_PAYLOAD", ""), object_pairs_hook=_unique_pairs)
    except (ValueError, TypeError):
        return invalid("projection", "delegated projection is strict JSON")
    if not isinstance(raw, Mapping):
        return invalid("projection", "delegated projection is an object")
    row = cast(Mapping[str, object], raw)
    if set(row) != {
        "command",
        "original_run",
        "source_result",
        "predicate",
        "as_of",
    }:
        return invalid(
            "projection", "delegated projection carries exactly its original run and query"
        )
    if row["command"] != "analysis.project" or not isinstance(row["original_run"], Mapping):
        return invalid("projection", "projection retains the original registered run envelope")
    context = decode_qma_backtest_context(
        payload_text=json.dumps(row["original_run"]), environ=environ
    )
    if is_refusal(context):
        return context
    selected = select_operator_composition(
        runtime_root=environ.get("QMB_REPLAY_RUNTIME_ROOT"), context=context.value
    )
    if is_refusal(selected):
        return selected
    if selected.value != "book" or context.value.command != "backtest.run":
        return policy("projection", "saved views require a verified Book CT-32/CT-29 source")
    verified = verify_operator_replay_result(
        runtime_root=environ.get("QMB_REPLAY_RUNTIME_ROOT"),
        context=context.value,
        claimed_result=row["source_result"],
    )
    if is_refusal(verified):
        return verified
    projected = project_operator_replay(
        runtime_root=environ.get("QMB_REPLAY_RUNTIME_ROOT"),
        context=context.value,
        predicate=row["predicate"],
        as_of=row["as_of"],
    )
    if is_refusal(projected):
        return projected
    return Ok(projected.value.body())
