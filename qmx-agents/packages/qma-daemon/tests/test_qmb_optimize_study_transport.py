"""QMA validates the private, complete Study result on the existing QMB door."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

from pytest import MonkeyPatch
from qma.daemon.backtest import service as backtest_service
from qma.daemon.backtest.cli import _runtime_preflight  # pyright: ignore[reportPrivateUsage]
from qmf.core import fingerprint, is_ok, is_refusal


def _fp(label: str) -> str:
    built = fingerprint({"test-study-value": label})
    assert is_ok(built), built
    return built.value.value


def _placement_payload() -> dict[str, object]:
    return {
        "job_id": "qmb:env-docker:task-study",
        "attempt_id": 1,
        "environment_ref": "env:docker",
        "occupancy_key": "docker",
        "experiment_spec_fp1": _fp("spec"),
        "evidence_ref": _fp("request"),
        "split_manifest_fp1": _fp("split"),
        "command": "optimize.run",
    }


def _preflight(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "class": "qmb-runtime-preflight-v1",
        "format_version": 1,
        **{key: value for key, value in payload.items() if key != "command"},
        "composition_class": "alternative-study",
        "mints_ct32": False,
        "operator_descriptor_fp1": _fp("descriptor"),
        "study_fp1": _fp("study"),
        "operational_fp1": _fp("operational"),
        "generation_count": 2,
        "batch_size": 1,
    }


def test_optimize_run_preflight_pins_non_ct32_study_plan(monkeypatch: MonkeyPatch) -> None:
    payload = _placement_payload()
    response = _preflight(payload)

    def run(*_args: object, **_kwargs: object) -> object:
        return type(
            "Completed",
            (),
            {"returncode": 0, "stdout": json.dumps(response), "stderr": ""},
        )()

    monkeypatch.setattr("qma.daemon.backtest.cli.subprocess.run", run)
    parsed = _runtime_preflight(("qmb", "optimize", "run"), {}, payload)
    assert is_ok(parsed), parsed
    assert parsed.value["composition_class"] == "alternative-study"
    assert parsed.value["mints_ct32"] is False
    assert parsed.value["study_fp1"] == response["study_fp1"]
    assert parsed.value["operational_fp1"] == response["operational_fp1"]


def test_optimize_preflight_refuses_book_alias_and_untyped_study_counts(
    monkeypatch: MonkeyPatch,
) -> None:
    payload = _placement_payload()
    cases = (
        {**_preflight(payload), "composition_class": "book", "mints_ct32": True},
        {**_preflight(payload), "mints_ct32": 0},
        {**_preflight(payload), "generation_count": True},
        {key: value for key, value in _preflight(payload).items() if key != "study_fp1"},
    )
    for response in cases:

        def run(
            *_args: object, _response: dict[str, object] = response, **_kwargs: object
        ) -> object:
            return type(
                "Completed",
                (),
                {"returncode": 0, "stdout": json.dumps(_response), "stderr": ""},
            )()

        monkeypatch.setattr(
            "qma.daemon.backtest.cli.subprocess.run",
            run,
        )
        parsed = _runtime_preflight(("qmb", "optimize", "run"), {}, payload)
        assert is_refusal(parsed), response


def _study_result() -> dict[str, object]:
    study_fp = _fp("study")

    def trial(generation: int) -> dict[str, object]:
        return {
            "class": "qmb-prior-trial",
            "generation_index": generation,
            "ask_index": 0,
            "parameters": {"risk_fraction": {"numerator": 1, "denominator": 10}},
            "objective_num": -1,
            "objective_den": 2,
        }

    return {
        "class": "qmb-operator-alternative-study-result-v1",
        "format_version": 1,
        "study_fp1": study_fp,
        "operational_fp1": _fp("operational"),
        "generation_run": {
            "class": "qmb-study-generation-run",
            "completed_generations": [[trial(0)], [trial(1)]],
            "generation_count": 2,
            "study_fp": study_fp,
            "writes_evidence": False,
        },
        "terminal_artifact_fp1s": [_fp("terminal-0"), _fp("terminal-1")],
        "occurrence_event_fp1": _fp("occurrence"),
    }


def test_study_completion_requires_exact_plan_and_full_ordered_history() -> None:
    expected: dict[str, object] = {
        "job_id": "qmb:env-docker:task-study",
        "attempt_id": 1,
        "experiment_spec_fp1": _fp("spec"),
        "evidence_ref": _fp("request"),
        "split_manifest_fp1": _fp("split"),
        "mints_ct32": False,
        "operator_descriptor_fp1": _fp("descriptor"),
        "composition_class": "alternative-study",
        "class": "qmb-operator-alternative-study-result-v1",
        "study_fp1": _fp("study"),
        "operational_fp1": _fp("operational"),
        "generation_count": 2,
        "batch_size": 1,
    }
    service = backtest_service.BacktestingService()
    result = _study_result()
    accepted = service._validate_terminal_payload(  # pyright: ignore[reportPrivateUsage]
        result, expected
    )
    assert is_ok(accepted), accepted

    incomplete = dict(result)
    incomplete["terminal_artifact_fp1s"] = [_fp("terminal-0")]
    refused = service._validate_terminal_payload(  # pyright: ignore[reportPrivateUsage]
        incomplete, expected
    )
    assert is_refusal(refused)

    foreign = dict(result)
    foreign["operational_fp1"] = _fp("different-operational-plan")
    refused_foreign = service._validate_terminal_payload(  # pyright: ignore[reportPrivateUsage]
        foreign, expected
    )
    assert is_refusal(refused_foreign)

    partial = dict(result)
    partial_history = dict(cast(Mapping[str, object], partial["generation_run"]))
    partial_history["generation_count"] = 1
    generations = cast(list[object], partial_history["completed_generations"])
    partial_history["completed_generations"] = [generations[0]]
    partial["generation_run"] = partial_history
    refused_partial = service._validate_terminal_payload(  # pyright: ignore[reportPrivateUsage]
        partial, expected
    )
    assert is_refusal(refused_partial)
