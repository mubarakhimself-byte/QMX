"""Real delegated optimize door with complete pinned recorded inputs and restart witnesses."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from operator_study_fixture_support import (  # pyright: ignore[reportMissingTypeStubs]
    ok,
    prepare_study_inputs,
    write_study_binding,
)
from qmb.host.operator_study_replay import invoke_operator_study
from qmf.core import Fingerprint, is_refusal


def _file_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_incomplete_study_verification_cannot_finish_trials_or_create_witness(
    tmp_path: Path,
) -> None:
    inputs = prepare_study_inputs(tmp_path / "recorded")
    runtime = tmp_path / "runtime"
    _, inputs, _ = write_study_binding(runtime, inputs)
    interrupted = invoke_operator_study(
        runtime_root=runtime,
        context=inputs.context,
        mode="execute",
        cancelled=inputs.terminal_store.path.exists,
    )
    assert is_refusal(interrupted), interrupted
    assert (
        len(
            ok(
                inputs.terminal_store.read(
                    journal_store=inputs.journal_store, registry=inputs.registry_persistence
                )
            )
        )
        == 1
    )
    before = _file_hashes(tmp_path)
    refused = invoke_operator_study(runtime_root=runtime, context=inputs.context, mode="verify")
    assert is_refusal(refused), refused
    assert _file_hashes(tmp_path) == before
    completed = ok(
        invoke_operator_study(runtime_root=runtime, context=inputs.context, mode="execute")
    )
    assert len(cast(list[object], completed["terminal_artifact_fp1s"])) == 2
    before = _file_hashes(tmp_path)
    reopened = ok(
        invoke_operator_study(runtime_root=runtime, context=inputs.context, mode="verify")
    )
    assert reopened == completed and _file_hashes(tmp_path) == before
    refused = invoke_operator_study(
        runtime_root=runtime,
        context=replace(inputs.context, attempt_id=inputs.context.attempt_id + 1),
        mode="verify",
    )
    assert is_refusal(refused), refused
    assert _file_hashes(tmp_path) == before


@pytest.mark.parametrize(
    "mutation",
    ["missing-field", "unknown-objective", "wrong-unit", "changed-builder", "study-fingerprint"],
)
def test_study_descriptor_refuses_before_any_trial(tmp_path: Path, mutation: str) -> None:
    inputs = prepare_study_inputs(tmp_path / "recorded")
    path, inputs, _ = write_study_binding(tmp_path / "runtime", inputs)
    body = json.loads(path.read_text())
    if mutation == "missing-field":
        del body["alternative_binding"]["operator_binding"]["roots"]
    elif mutation == "unknown-objective":
        body["study"]["objective"]["measure_identity"] = "unregistered"
    elif mutation == "wrong-unit":
        body["study"]["objective"]["unit_kind"] = "ratio"
    elif mutation == "changed-builder":
        body["alternative_binding"]["builder_files"]["builder.py"] += "\n# changed source\n"
    else:
        body["study_fp1"] = "fp1:sha256:" + "0" * 64
    from qmf.core import fingerprint

    body["descriptor_fp1"] = ok(
        fingerprint({k: v for k, v in body.items() if k != "descriptor_fp1"})
    ).value
    path.write_text(json.dumps(body))
    # Supply the new outer pin so the test reaches nested/content validation.
    context = replace(
        inputs.context, operator_descriptor_fp1=ok(Fingerprint.try_create(body["descriptor_fp1"]))
    )
    rejected = invoke_operator_study(
        runtime_root=tmp_path / "runtime", context=context, mode="execute"
    )
    assert is_refusal(rejected), rejected
    assert not inputs.terminal_store.path.exists()
