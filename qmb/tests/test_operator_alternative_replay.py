"""Strict operator descriptor selection for the existing backtest CLI."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, TypeVar, cast

from qmb.host.operator_alternative_replay import (
    execute_operator_alternative_replay,
    operator_alternative_binding_present,
    read_operator_alternative_binding,
)
from qmb.host.qma_cli import QmaBacktestContext
from qmf.core import Fingerprint, Result, fingerprint, is_ok, is_refusal

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(character: str) -> Fingerprint:
    return _ok(Fingerprint.try_create(f"fp1:sha256:{character * 64}"))


def _context() -> QmaBacktestContext:
    return QmaBacktestContext(
        job_id="job-atc-runtime",
        attempt_id=3,
        experiment_spec_fp1=_fp("a"),
        evidence_ref=_fp("b"),
        split_manifest_fp1=_fp("c"),
        environment_ref="env:local-replay",
        occupancy_key="run:atc-runtime",
        mints_ct32=False,
    )


def _write_descriptor(root: Path, context: QmaBacktestContext) -> Path:
    roots = {
        name: str(root / name) for name in ("raw", "registry", "journal", "alternative_terminal")
    }
    for value in roots.values():
        Path(value).mkdir(parents=True, exist_ok=True)
    state = {"cash_units": 1_000_000, "position_units": 0}
    initial_state_fp = _ok(fingerprint(state)).value
    operator_binding: dict[str, object] = {
        "class": "qmb-operator-alternative-binding-v1",
        "format_version": 1,
        "experiment_spec_fp1": context.experiment_spec_fp1.value,
        "evidence_ref": context.evidence_ref.value,
        "split_manifest_fp1": context.split_manifest_fp1.value,
        "composition_fp1": _fp("d").value,
        "policy_pair_identity": {"policy_pair_id": "pair", "policy_pair_version": 1},
        "source_fp1": _fp("e").value,
        "split_fp1": context.split_manifest_fp1.value,
        "split_role": "train",
        "registry_fp1": _fp("f").value,
        "interpreter_registration_fp1": _fp("1").value,
        "journal_writer": {
            "machine": "test-host",
            "role": "qmb",
            "stream": "atc-stream",
            "boot_epoch_id": "boot-1",
        },
        "journal_stream": "atc-stream",
        "terminal_root": roots["alternative_terminal"],
        "lineage_writer": {
            "machine": "test-host",
            "role": "qmb",
            "stream": "lineage-stream",
            "boot_epoch_id": "boot-1",
        },
        "roots": roots,
        "registry_as_of_ns": 0,
        "registry_writer": {
            "machine": "test-host",
            "role": "qmb",
            "stream": "registry-stream",
            "boot_epoch_id": "boot-1",
        },
        "initial_accounting_state": state,
        "initial_accounting_state_fp1": initial_state_fp,
        "command_owner_epoch": 18,
        "trial_label": {
            "class": "qmb-alternative-trial-label-v1",
            "present": False,
            "label": {},
        },
    }
    builder_files = {"builder.py": "def build(context, binding):\n    return None\n"}
    builder_fp1 = _ok(
        fingerprint({"class": "qmb-operator-alternative-builder-v1", "files": builder_files})
    ).value
    body: dict[str, object] = {
        "class": "qmb-operator-alternative-binding-v1",
        "format_version": 1,
        "composition_class": "alternative",
        "experiment_spec_fp1": context.experiment_spec_fp1.value,
        "evidence_ref": context.evidence_ref.value,
        "split_manifest_fp1": context.split_manifest_fp1.value,
        "operator_binding": operator_binding,
        "operator_binding_fp1": _ok(fingerprint(operator_binding)).value,
        "builder_files": builder_files,
        "builder_fp1": builder_fp1,
        "entrypoint": "builder:build",
    }
    body["descriptor_fp1"] = _ok(fingerprint(dict(body))).value
    directory = (
        root
        / context.experiment_spec_fp1.value.replace(":", "-")
        / context.evidence_ref.value.replace(":", "-")
    )
    directory.mkdir(parents=True)
    path = directory / "operator-alternative-binding.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def test_descriptor_selects_alternative_and_typed_shape_is_pinned(tmp_path: Path) -> None:
    context = _context()
    path = _write_descriptor(tmp_path, context)

    selected = _ok(
        operator_alternative_binding_present(runtime_root=str(tmp_path), context=context)
    )
    binding = _ok(read_operator_alternative_binding(runtime_root=str(tmp_path), context=context))

    assert selected is True
    assert binding.context == context
    assert binding.entrypoint == "builder:build"
    assert binding.identity["terminal_root"] == str(tmp_path / "alternative_terminal")
    assert is_refusal(
        execute_operator_alternative_replay(runtime_root=str(tmp_path), context=context)
    )
    assert path.exists()


def test_malformed_or_ambiguous_alternative_descriptor_never_falls_through(
    tmp_path: Path,
) -> None:
    context = _context()
    path = _write_descriptor(tmp_path, context)
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    descriptor["builder_fp1"] = _fp("9").value
    path.write_text(json.dumps(descriptor), encoding="utf-8")

    selected = _ok(
        operator_alternative_binding_present(runtime_root=str(tmp_path), context=context)
    )
    assert selected is True
    assert is_refusal(
        read_operator_alternative_binding(runtime_root=str(tmp_path), context=context)
    )

    (path.parent / "operator-binding.json").write_text("{}", encoding="utf-8")
    assert is_refusal(
        operator_alternative_binding_present(runtime_root=str(tmp_path), context=context)
    )


def test_no_alternative_descriptor_selects_existing_book_branch(tmp_path: Path) -> None:
    context = _context()
    directory = (
        tmp_path
        / context.experiment_spec_fp1.value.replace(":", "-")
        / context.evidence_ref.value.replace(":", "-")
    )
    directory.mkdir(parents=True)

    assert not _ok(
        operator_alternative_binding_present(runtime_root=str(tmp_path), context=context)
    )


def test_nominal_malformed_qma_context_refuses_before_composition_lookup(tmp_path: Path) -> None:
    context = _context()
    malformed: tuple[tuple[str, object], ...] = (
        ("experiment_spec_fp1", None),
        ("evidence_ref", Fingerprint("not-fp1")),
        ("split_manifest_fp1", None),
        ("attempt_id", True),
        ("job_id", []),
        ("occupancy_key", None),
    )
    for field, value in malformed:
        candidate = replace(cast(Any, context), **{field: value})
        result = operator_alternative_binding_present(
            runtime_root=tmp_path / "absent-runtime", context=candidate
        )
        assert is_refusal(result), (field, result)
        assert result.context.get("field") == field
