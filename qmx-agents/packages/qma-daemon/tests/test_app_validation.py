"""MA03 owner/API, bounded adversarial validation and journal recovery cases."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.process import DaemonProcess
from qma.wire.panel_composition import (
    COMPONENTS,
    VALIDATION_CAPABILITIES,
    ValidationLimits,
    budget,
    validate_structure,
)
from qmf.core import Result, is_ok, is_refusal
from test_app_candidate import mint, process, save

LIMITS = {
    "max_bytes": 32768,
    "max_panels": 12,
    "max_elements": 80,
    "max_depth": 8,
    "max_json_depth": 20,
    "max_nodes": 2000,
    "max_array_items": 100,
    "max_string_bytes": 1024,
    "max_errors": 16,
}
CAPS = dict.fromkeys(VALIDATION_CAPABILITIES, True)


def need[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def validation(p: DaemonProcess, name: str, args: object) -> Any:
    return p.app_validation_request(
        name, args, operator_principal=PrincipalClass.OPERATOR, capabilities=CAPS
    )


@pytest.fixture
def owner(tmp_path: Path) -> Iterator[DaemonProcess]:
    (tmp_path / "operator-config.json").write_text(
        json.dumps({"miniapp_validation_limits": LIMITS})
    )
    p = process(tmp_path)
    mint(p)
    mint(p, "psess:app", "app-use", "pack:analysis-backtest")
    mint(p, "psess:other", "app-use", "pack:dev-factory")
    try:
        yield p
    finally:
        p.close()


def example(p: DaemonProcess) -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = validation(p, "get_app_ui_catalog", {"product_session_ref": "psess:author"})
    assert is_ok(catalog), catalog
    operation: Any = next(
        op for op in catalog.value["operations"] if op["op_id"] == "qmb.analysis.project"
    )
    staged = p.artifacts.stage_complete_bytes(b'{"recorded":"input"}')
    assert is_ok(staged)
    binding: dict[str, Any] = {
        key: value for key, value in operation.items() if key != "descriptor"
    }
    binding["parameters"] = {"run_fp1": staged.value.fp1}
    body: dict[str, Any] = {
        "schema": "qma.miniapp.composition.v1",
        "catalog_fp1": catalog.value["catalog_fp1"],
        "bindings": {"read": binding},
        "panels": [
            {
                "title": "First read",
                "data": "read",
                "root": "page",
                "elements": {
                    "page": {"type": "Stack", "children": ["table", "text"]},
                    "table": {"type": "Table", "props": {"columns": ["Evidence"], "rows": []}},
                    "text": {"type": "Text", "props": {"text": "No invented results"}},
                },
            },
            {
                "title": "Second read",
                "data": "read",
                "root": "page",
                "elements": {
                    "page": {"type": "Grid", "props": {"min": 9}, "children": ["metric", "button"]},
                    "metric": {
                        "type": "Metric",
                        "props": {"label": "Current value", "value": None},
                    },
                    "button": {"type": "Button", "props": {"label": "Refresh", "action": "read"}},
                },
            },
        ],
    }
    source = {
        "fp1": staged.value.fp1,
        "byte_count": staged.value.byte_count,
        "media_type": "application/json",
    }
    return body, source


def candidate(
    p: DaemonProcess, body: dict[str, Any], source: dict[str, Any], **extra: object
) -> Any:
    encoded = json.dumps(body, ensure_ascii=True).encode()
    staged = p.artifacts.stage_complete_bytes(encoded)
    assert is_ok(staged)
    return save(
        p,
        {
            "schema": "qma.miniapp.candidate-content.v1",
            "kind": "data-only",
            "metadata": {"title": "Reads", "description": ""},
            "composition_ref": {
                "fp1": staged.value.fp1,
                "byte_count": len(encoded),
                "media_type": "application/json",
            },
            "source_refs": [source],
            "asset_refs": [],
        },
        str(body)[:20] + str(extra),
        **extra,
    )


def validate(p: DaemonProcess, version: Any, catalog_fp1: Any) -> Any:
    result = validation(
        p,
        "validate_app_candidate",
        {
            "product_session_ref": "psess:author",
            "candidate_id": version["candidate_id"],
            "revision": version["revision"],
            "expected_context_revision": 0,
            "catalog_fp1": catalog_fp1,
        },
    )
    assert is_ok(result), result
    return result.value


def read(p: DaemonProcess, version: Any, proof: Any, session: str = "psess:author") -> Any:
    return validation(
        p,
        "get_app_candidate_validation",
        {
            "product_session_ref": session,
            "candidate_id": version["candidate_id"],
            "revision": version["revision"],
            "validation_fp1": proof["validation_fp1"],
        },
    )


def test_valid_two_reads_determinism_adapter_restart_and_rebuild(
    owner: DaemonProcess, tmp_path: Path
) -> None:
    p = owner
    body, source = example(p)
    version = candidate(p, body, source, instance_id="pack:analysis-backtest")
    result = validate(p, version, body["catalog_fp1"])
    assert result["result"]["status"] == "valid"
    assert len(result["result"]["view_requests"]) == 2
    assert result["result"]["view_requests"][0]["renderer"] == "json-render"
    assert validate(p, version, body["catalog_fp1"]) == result
    assert is_ok(read(p, version, result, "psess:app"))
    assert is_refusal(read(p, version, result, "psess:other"))
    assert read(p, version, result).value["validation_current"]
    assert (
        len([e for e in need(p.journal.read_events()) if e.event == "app_candidate.validated"]) == 1
    )
    p.close()
    # Actual projection location is owner-exposed; perform loss before close in other case.
    reopened = process(tmp_path, "ma03-reopen")
    try:
        assert read(reopened, version, result).value["result"] == result["result"]
        assert read(reopened, version, result).value["receipt_fp1"] == result["receipt_fp1"]
    finally:
        reopened.close()


@pytest.mark.parametrize(
    "mutation",
    [
        "cycle",
        "orphan",
        "missing_child",
        "duplicate_child",
        "leaf_child",
        "wrong_type",
        "unsupported",
        "url",
        "code",
        "grant",
        "bad_action",
        "bad_props",
        "bad_columns",
        "chart_seed",
        "chart_color",
        "unknown_input",
        "input_type",
        "missing_input",
        "op_version",
        "schema_version",
        "output_shape",
        "descriptor",
        "availability",
        "package",
        "instance",
        "contribution",
        "effect_op",
        "source",
        "stale_catalog",
    ],
)
def test_adversarial_cases_produce_bounded_actionable_errors(
    owner: DaemonProcess, mutation: str
) -> None:
    body, source = example(owner)
    panel = body["panels"][0]
    binding = body["bindings"]["read"]
    if mutation == "cycle":
        panel["elements"]["page"]["children"].append("page")
    elif mutation == "orphan":
        panel["elements"]["orphan"] = {"type": "Text", "props": {"text": "unused"}}
    elif mutation == "missing_child":
        panel["elements"]["page"]["children"].append("missing")
    elif mutation == "duplicate_child":
        panel["elements"]["page"]["children"].append("table")
    elif mutation == "leaf_child":
        panel["elements"]["text"]["children"] = ["table"]
    elif mutation == "wrong_type":
        panel["elements"]["page"]["children"] = "table"
    elif mutation == "unsupported":
        panel["elements"]["text"]["type"] = "Exec"
    elif mutation == "url":
        panel["data"] = "https://example.invalid/"
    elif mutation == "code":
        panel["elements"]["page"]["props"] = {"eval": "__import__('os')"}
    elif mutation == "grant":
        binding["grant_id"] = "fabricated"
    elif mutation == "bad_action":
        body["panels"][1]["elements"]["button"]["props"]["action"] = {}
    elif mutation == "bad_props":
        panel["elements"]["table"]["props"]["rows"] = "x"
    elif mutation == "bad_columns":
        panel["elements"]["table"]["props"]["rows"] = [["one", "extra"]]
    elif mutation in {"chart_seed", "chart_color"}:
        panel["elements"]["text"] = {
            "type": "LineChart",
            "props": {"series": [{"label": "A", "values": []}]},
        }
        panel["elements"]["text"]["props"]["series"][0][
            "seed" if mutation == "chart_seed" else "color"
        ] = 3 if mutation == "chart_seed" else "url(file:///secret)"
    elif mutation == "unknown_input":
        binding["parameters"]["provider"] = "code"
    elif mutation == "input_type":
        binding["parameters"]["run_fp1"] = True
    elif mutation == "missing_input":
        binding["parameters"] = {}
    elif mutation == "op_version":
        binding["op_version"] = True
    elif mutation == "schema_version":
        binding["input_schema"] += ".future"
    elif mutation == "output_shape":
        binding["output_shape"] = "value"
    elif mutation == "descriptor":
        binding["descriptor_fp1"] = source["fp1"]
    elif mutation == "availability":
        binding["availability_revision"] += 1
    elif mutation == "package":
        binding["package_version"] = "9.0.0"
    elif mutation == "instance":
        binding["instance_id"] = "pack:dev-factory"
    elif mutation == "contribution":
        binding["qualified_id"] = "analysis-backtest:replay"
    elif mutation == "effect_op":
        binding["op_id"] = "qmb.backtest.run"
    elif mutation == "source":
        binding["parameters"]["run_fp1"] = "not-a-run-fingerprint"
    elif mutation == "stale_catalog":
        body["catalog_fp1"] = source["fp1"]
    version = candidate(owner, body, source)
    catalog = validation(owner, "get_app_ui_catalog", {"product_session_ref": "psess:author"}).value
    result = validate(owner, version, catalog["catalog_fp1"])["result"]
    assert result["status"] == "invalid", mutation
    assert result["view_requests"] == []
    assert 0 < len(result["errors"]) <= LIMITS["max_errors"]
    assert all(set(e) == {"path", "code", "message", "remediation"} for e in result["errors"])


def test_app_use_cannot_validate_and_stale_context_catalog_refuse(owner: DaemonProcess) -> None:
    body, source = example(owner)
    version = candidate(owner, body, source, instance_id="pack:analysis-backtest")
    args = {
        "product_session_ref": "psess:app",
        "candidate_id": version["candidate_id"],
        "revision": version["revision"],
        "expected_context_revision": 0,
        "catalog_fp1": body["catalog_fp1"],
    }
    assert is_refusal(validation(owner, "validate_app_candidate", args))
    args["product_session_ref"] = "psess:author"
    args["expected_context_revision"] = 1
    assert is_refusal(validation(owner, "validate_app_candidate", args))
    args["expected_context_revision"] = 0
    args["catalog_fp1"] = source["fp1"]
    assert is_refusal(validation(owner, "validate_app_candidate", args))


def test_changed_head_and_host_limits_invalidate_proof(
    owner: DaemonProcess, tmp_path: Path
) -> None:
    body, source = example(owner)
    version = candidate(owner, body, source)
    result = validate(owner, version, body["catalog_fp1"])
    body["panels"][0]["title"] = "Changed"
    candidate(
        owner,
        body,
        source,
        candidate_id=version["candidate_id"],
        expected_revision=version["revision"],
    )
    assert not read(owner, version, result).value["validation_current"]
    (tmp_path / "operator-config.json").write_text(
        json.dumps({"miniapp_validation_limits": {**LIMITS, "max_depth": 7}})
    )
    assert "STALE_CATALOG" in {
        e["code"] for e in read(owner, version, result).value["current_errors"]
    }


def test_all_documented_components_and_empty_chart(owner: DaemonProcess) -> None:
    body, _ = example(owner)
    panel = body["panels"][0]
    panel["elements"] = {
        "root": {"type": "Stack", "children": ["grid"]},
        "grid": {
            "type": "Grid",
            "children": ["h", "t", "m", "table", "chart", "badge", "callout", "button"],
        },
        "h": {"type": "Heading", "props": {"text": "Heading"}},
        "t": {"type": "Text", "props": {"text": "Text"}},
        "m": {"type": "Metric", "props": {"label": "Metric", "value": 1}},
        "table": {"type": "Table", "props": {"columns": ["Value"], "rows": []}},
        "chart": {"type": "LineChart", "props": {"series": [{"label": "Recorded", "values": []}]}},
        "badge": {"type": "Badge", "props": {"text": "Empty"}},
        "callout": {"type": "Callout", "props": {"text": "No results", "tone": "info"}},
        "button": {"type": "Button", "props": {"label": "Read", "action": "read"}},
    }
    panel["root"] = "root"
    limits = need(ValidationLimits.parse(LIMITS))
    assert not validate_structure(body, limits)
    assert {e["type"] for e in panel["elements"].values()} == set(COMPONENTS)


@pytest.mark.parametrize(
    "limit",
    [
        "max_bytes",
        "max_panels",
        "max_elements",
        "max_depth",
        "max_json_depth",
        "max_nodes",
        "max_array_items",
        "max_string_bytes",
    ],
)
def test_every_resource_bound(owner: DaemonProcess, limit: str) -> None:
    body, _ = example(owner)
    selected = {**LIMITS, limit: 1}
    problems = validate_structure(body, need(ValidationLimits.parse(selected)))
    assert problems and any(e["code"] == "LIMIT" for e in problems)


def test_python_cycles_unicode_and_finite_json() -> None:
    limits = need(ValidationLimits.parse(LIMITS))
    cycle: dict[str, object] = {}
    cycle["self"] = cycle
    assert budget(cycle, limits)[0]["code"] == "CYCLE"
    assert budget({"unicode": "\ud800"}, limits)[0]["code"] == "UNICODE"
    assert budget({"nonfinite": float("inf")}, limits)[0]["code"] == "TYPE"
    assert not budget({"unicode": "हेलो 🚀"}, limits)


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        {"max_bytes": True},
        {**LIMITS, "max_depth": 33},
        {**LIMITS, "max_bytes": 65537},
        {**LIMITS, "max_errors": 0},
    ],
)
def test_host_limit_configuration_closed_and_bounded(value: object) -> None:
    assert is_refusal(ValidationLimits.parse(value))


def test_projection_loss_and_postcommit_failure_recover_same_receipt(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    body, source = example(owner)
    version = candidate(owner, body, source)
    service = owner.app_validation

    def fail(*args: object) -> None:
        raise sqlite3.OperationalError("injected projection failure")

    args = {
        "product_session_ref": "psess:author",
        "candidate_id": version["candidate_id"],
        "revision": version["revision"],
        "expected_context_revision": 0,
        "catalog_fp1": body["catalog_fp1"],
    }
    with monkeypatch.context() as injection:
        injection.setattr(service, "_insert", fail)
        denied = validation(owner, "validate_app_candidate", args)
        assert is_refusal(denied) and denied.context["operation_committed"]
    recovered = validation(owner, "validate_app_candidate", args)
    assert is_ok(recovered)
    owner.sqlite.execute("DELETE FROM app_candidate_validation")
    assert is_ok(service.restore_from_journal())
    assert read(owner, version, recovered.value).value["result"] == recovered.value["result"]
    assert (
        len([e for e in need(owner.journal.read_events()) if e.event == "app_candidate.validated"])
        == 1
    )


def test_run_identity_is_not_a_blob_identity(owner: DaemonProcess) -> None:
    body, source = example(owner)
    body["bindings"]["read"]["parameters"]["run_fp1"] = "fp1:sha256:" + "1" * 64
    version = candidate(owner, body, source)
    proof = validate(owner, version, body["catalog_fp1"])
    assert proof["result"]["status"] == "valid"
    assert proof["authorizes_invoke"] is False


def test_unconfigured_validation_has_no_default(tmp_path: Path) -> None:
    p = process(tmp_path)
    try:
        assert p.app_validation.capabilities()["validate_app_candidate"] is False
    finally:
        p.close()


def test_dependency_disable_invalidates_current_proof(owner: DaemonProcess) -> None:
    body, source = example(owner)
    version = candidate(owner, body, source)
    proof = validate(owner, version, body["catalog_fp1"])
    need(owner.roster.loader.disable("analysis-backtest"))
    reply = need(read(owner, version, proof))
    assert not reply["validation_current"]
    assert "UNAVAILABLE_OPERATION" in {e["code"] for e in reply["current_errors"]}


def test_missing_source_after_save_is_typed_and_proof_stale(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    body, source = example(owner)
    version = candidate(owner, body, source)
    proof = validate(owner, version, body["catalog_fp1"])
    original = owner.artifacts.get

    def missing(fp1: str) -> Any:
        return None if fp1 == source["fp1"] else original(fp1)

    monkeypatch.setattr(owner.artifacts, "get", missing)
    rejected = validate(owner, version, body["catalog_fp1"])
    assert rejected["result"]["status"] == "invalid"
    reply = need(read(owner, version, proof))
    assert not reply["validation_current"]
    assert "STALE_REFERENCE" in {e["code"] for e in reply["current_errors"]}


def test_self_consistent_forged_success_fails_structural_replay(owner: DaemonProcess) -> None:
    from qma.wire.panel_composition import data_bytes
    from qmf.core.fingerprint import fingerprint_bytes

    body, source = example(owner)
    body["panels"][0]["elements"]["text"]["type"] = "Script"
    version = candidate(owner, body, source)
    proof = validate(owner, version, body["catalog_fp1"])
    forged = dict(proof["result"], status="valid", errors=[])
    staged = need(owner.artifacts.stage_complete_bytes(data_bytes(forged)))
    assert fingerprint_bytes(data_bytes(forged)).value == staged.fp1
    need(
        owner.journal.append_event(
            "app_candidate.validated",
            payload={
                "schema": "qma.miniapp.validation.v1",
                "candidate_id": version["candidate_id"],
                "revision": version["revision"],
                "validation_fp1": staged.fp1,
                "byte_count": staged.byte_count,
                "owner_principal": forged["owner_principal"],
            },
        )
    )
    before = owner.sqlite.execute("SELECT * FROM app_candidate_validation")
    refused = owner.app_validation.restore_from_journal()
    assert is_refusal(refused)
    assert refused.context["field"] == "app_candidate_validation"
    assert owner.sqlite.execute("SELECT * FROM app_candidate_validation") == before


def test_optional_grid_dimensions_do_not_impose_demo_defaults(owner: DaemonProcess) -> None:
    body, _ = example(owner)
    body["panels"] = [
        {
            "title": "Small grid",
            "root": "root",
            "data": "read",
            "elements": {
                "root": {"type": "Grid", "children": ["text"]},
                "text": {"type": "Text", "props": {"text": "Empty"}},
            },
        }
    ]
    assert not validate_structure(
        body, need(ValidationLimits.parse({**LIMITS, "max_array_items": 1}))
    )
