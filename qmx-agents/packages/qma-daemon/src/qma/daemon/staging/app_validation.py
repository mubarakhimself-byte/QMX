"""MA03 trusted checks and immutable results on MA02's existing owner substrate."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from qma.core.app_candidate import json_object
from qma.core.operations import OperationDescriptor, parse_operation_descriptor
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.bootstrap_config import CONFIG_NAME
from qma.daemon.plugins.loader import PluginLoader
from qma.daemon.sessions.operation_bindings import declared_operation_point
from qma.daemon.staging.app_candidate import AppCandidateService
from qma.wire.app_candidate import CANDIDATE_CAPABILITIES, invalid_input, policy_rejection
from qma.wire.invocation_envelope import parse_utc_iso_z, validate_input_payload
from qma.wire.pack_ui_request import PackUiView
from qma.wire.panel_composition import (
    RESULT_SCHEMA,
    VALIDATOR_ID,
    ValidationLimits,
    catalog_definition,
    data_bytes,
    error,
    parse_validation_args,
    require_validation_capability,
    validate_structure,
)
from qma.wire.schemas import validate_instance
from qmf.core import Fingerprint, Ok, Result, is_refusal
from qmf.core.fingerprint import fingerprint_bytes
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal
from qmf.data.store.refusals import storage_failure

VALIDATED_EVENT = "app_candidate.validated"
_TABLE = """CREATE TABLE IF NOT EXISTS app_candidate_validation (
validation_fp1 TEXT PRIMARY KEY NOT NULL, candidate_id TEXT NOT NULL,
revision TEXT NOT NULL, payload TEXT NOT NULL, journal_seq INTEGER NOT NULL,
receipt_fp1 TEXT NOT NULL)"""


def unavailable() -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
        retryability=Retryability.AFTER_CONDITION,
        context={
            "field": "miniapp_validation_limits",
            "reason": "operator host limits are required",
        },
        after_condition_descriptor=("configure miniapp_validation_limits in operator-config.json"),
    )


@dataclass
class AppValidationService:
    candidates: AppCandidateService
    loader: PluginLoader
    descriptors: Callable[[], tuple[OperationDescriptor, ...]]
    root: Path
    _dirty: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.candidates.sqlite.execute(_TABLE)

    def limits(self) -> Result[ValidationLimits | None]:
        path = self.root / CONFIG_NAME
        if not path.is_file():
            return Ok(None)
        try:
            if path.stat().st_size > 65536:
                return invalid_input("operator-config", "config exceeds existing 64KiB bound")
            body = json_object(path.read_bytes())
        except OSError as exc:
            return storage_failure(str(exc))
        if is_refusal(body):
            return body
        if "miniapp_validation_limits" not in body.value:
            return Ok(None)
        parsed = ValidationLimits.parse(body.value["miniapp_validation_limits"])
        if is_refusal(parsed):
            return parsed
        return Ok(parsed.value)

    def capabilities(self) -> dict[str, object]:
        limits = self.limits()
        return {
            "get_app_ui_catalog": True,
            "get_app_candidate_validation": True,
            "validate_app_candidate": isinstance(limits, Ok) and limits.value is not None,
        }

    def _catalog(self, limits: ValidationLimits | None) -> dict[str, object]:
        return {
            **catalog_definition(),
            "validator_id": VALIDATOR_ID,
            "limits": None if limits is None else limits.to_payload(),
        }

    @staticmethod
    def _fp(body: object) -> str:
        return fingerprint_bytes(data_bytes(body)).value

    def _operations(self, scope: str | None) -> list[dict[str, object]]:
        result: list[dict[str, object]] = []
        for key in self.loader.loaded_ids():
            loaded = self.loader.get(key)
            if loaded is None or (scope is not None and scope != loaded.instance_id):
                continue
            for contribution in self.loader.published_contributions():
                if contribution.plugin_id != key or contribution.qualified_id is None:
                    continue
                for descriptor in self.descriptors():
                    if (
                        descriptor.op_id != "qmb.analysis.project"
                        or descriptor.effect_class.value != "read"
                        or declared_operation_point(descriptor.op_id, contribution.qualified_id)
                        != contribution.point
                    ):
                        continue
                    result.append(
                        {
                            "instance_id": loaded.instance_id,
                            "qualified_id": contribution.qualified_id,
                            "package_version": contribution.package_version,
                            "availability_revision": loaded.availability_revision,
                            "op_id": descriptor.op_id,
                            "op_version": descriptor.version,
                            "input_schema": descriptor.input_schema,
                            "output_shape": descriptor.output_shape.value,
                            "descriptor_fp1": self._fp(dict(descriptor.to_payload())),
                            "descriptor": dict(descriptor.to_payload()),
                        }
                    )
        return sorted(
            result,
            key=lambda row: (str(row["instance_id"]), str(row["qualified_id"]), str(row["op_id"])),
        )

    def _dependencies(
        self,
        body: Mapping[str, object],
        scope: str | None,
        version: Mapping[str, object],
        archived_operations: list[dict[str, object]] | None = None,
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        problems: list[dict[str, object]] = []
        dependencies: list[dict[str, object]] = []
        operations = self._operations(scope) if archived_operations is None else archived_operations
        bindings = cast(dict[str, dict[str, object]], body["bindings"])
        source_refs = cast(
            list[dict[str, object]], cast(dict[str, object], version["content"])["source_refs"]
        )
        for ident, binding in sorted(bindings.items()):
            path = "$/bindings/" + ident
            op = next(
                (
                    row
                    for row in operations
                    if row["instance_id"] == binding["instance_id"]
                    and row["qualified_id"] == binding["qualified_id"]
                    and row["op_id"] == binding["op_id"]
                ),
                None,
            )
            if op is None:
                problems.append(
                    error(
                        path,
                        "UNAVAILABLE_OPERATION",
                        "No declared read adapter in this scope",
                        "Refresh scoped catalog operations",
                    )
                )
                continue
            pins = {key: value for key, value in op.items() if key != "descriptor"}
            if any(binding[key] != value for key, value in pins.items()):
                problems.append(
                    error(
                        path,
                        "STALE_DEPENDENCY",
                        "Operation identity or schema has changed",
                        "Refresh exact operation pins",
                    )
                )
                continue
            descriptor_result = parse_operation_descriptor(op["descriptor"])
            if is_refusal(descriptor_result):
                problems.append(
                    error(
                        path,
                        "OPERATION_SCHEMA",
                        "Owner descriptor invalid",
                        "Refresh the owner descriptor",
                    )
                )
                continue
            descriptor = descriptor_result.value
            if (
                descriptor.op_id != "qmb.analysis.project"
                or descriptor.effect_class.value != "read"
                or descriptor.op_id != op["op_id"]
                or descriptor.version != op["op_version"]
                or descriptor.input_schema != op["input_schema"]
                or descriptor.output_shape.value != op["output_shape"]
                or self._fp(dict(descriptor.to_payload())) != op["descriptor_fp1"]
                or declared_operation_point(descriptor.op_id, cast(str, op["qualified_id"])) is None
            ):
                problems.append(
                    error(
                        path,
                        "OPERATION_SCHEMA",
                        "Descriptor differs from adapter pins",
                        "Refresh the owner descriptor",
                    )
                )
                continue
            parameters = cast(dict[str, object], binding["parameters"])
            checked = validate_input_payload(descriptor, parameters)
            if is_refusal(checked) or set(checked.value) != set(parameters):
                problems.append(
                    error(
                        path + "/parameters",
                        "OPERATION_SCHEMA",
                        "Parameters differ from owner input schema",
                        "Use only declared required and optional inputs",
                    )
                )
                continue
            # MA03 narrows the current read adapter to immutable owner-declared inputs.
            # It does not invent stream/URL/credential operations or execute a read.
            for key, value in parameters.items():
                if key.endswith("_fp1") or key.endswith("_ref"):
                    parsed = Fingerprint.try_create(value)
                    if is_refusal(parsed):
                        problems.append(
                            error(
                                path + "/parameters/" + key,
                                "REFERENCE",
                                "Input must be a valid owner run fingerprint",
                                "Use the exact run identity; readiness remains an owner read check",
                            )
                        )
                elif key == "as_of":
                    if value is not None and is_refusal(parse_utc_iso_z("as_of", value)):
                        problems.append(
                            error(
                                path + "/parameters/as_of",
                                "OPERATION_SCHEMA",
                                "Invalid owner time parameter",
                                "Use a UTC ISO8601 Z timestamp",
                            )
                        )
            for source in source_refs:
                held = self.candidates.read_reference(source)
                if is_refusal(held):
                    problems.append(
                        error(
                            path + "/parameters",
                            "STALE_REFERENCE",
                            "Source bytes unavailable or changed",
                            "Restage exact source and revalidate",
                        )
                    )
            dependencies.append({"binding_id": ident, **dict(binding)})
        return dependencies, problems

    def request(
        self,
        name: str,
        args: object,
        *,
        principal_class: object,
        owner_principal: object,
        capabilities: object,
    ) -> Result[Mapping[str, object]]:
        gated = require_validation_capability(name, capabilities)
        if is_refusal(gated):
            return gated
        parsed = parse_validation_args(name, args)
        if is_refusal(parsed):
            return parsed
        params = parsed.value
        if principal_class is not PrincipalClass.OPERATOR:
            return policy_rejection("principal_class", "MA03 requires an operator pairing")
        with self.candidates.authority_lock:
            if self._dirty:
                restored = self.restore_from_journal()
                if is_refusal(restored):
                    return restored
            session = self.candidates.sessions.get(params["product_session_ref"])
            if is_refusal(session):
                return session
            if not isinstance(owner_principal, str) or not owner_principal:
                return policy_rejection("owner_principal", "local operator unavailable")
            if session.value.principal != PrincipalClass.OPERATOR.value:
                return policy_rejection("principal", "operator-owned ProductSession required")
            scope = session.value.app_instance_id
            limits = self.limits()
            if is_refusal(limits):
                return limits
            catalog = self._catalog(limits.value)
            catalog_fp1 = self._fp(catalog)
            if name == "get_app_ui_catalog":
                return Ok(
                    {
                        "catalog_fp1": catalog_fp1,
                        "catalog": catalog,
                        "operations": self._operations(scope),
                        "authorizes_invoke": False,
                        "validation_available": limits.value is not None,
                    }
                )
            selected = self.candidates.request(
                "get_app_candidate",
                {key: params[key] for key in ("product_session_ref", "candidate_id", "revision")},
                principal_class=principal_class,
                owner_principal=owner_principal,
                capabilities=dict.fromkeys(CANDIDATE_CAPABILITIES, True),
            )
            if is_refusal(selected):
                return selected
            version = cast(dict[str, object], selected.value["version"])
            if name == "get_app_candidate_validation":
                rows = self.candidates.sqlite.execute(
                    "SELECT payload, receipt_fp1 FROM app_candidate_validation "
                    "WHERE validation_fp1=? AND candidate_id=? AND revision=?",
                    (params["validation_fp1"], params["candidate_id"], params["revision"]),
                )
                if not rows:
                    return invalid_input(
                        "validation_fp1", "no recorded proof for exact candidate/version"
                    )
                projected = json_object(cast(str, rows[0][0]).encode("utf-8"))
                if is_refusal(projected):
                    return projected
                result = projected.value
                if self._fp(result) != params["validation_fp1"]:
                    return invalid_input("validation_fp1", "derived result identity mismatch")
                problems = sorted(
                    self._current_errors(
                        result, version, scope, catalog_fp1, selected.value["current_revision"]
                    ),
                    key=lambda item: (str(item["path"]), str(item["code"])),
                )[: limits.value.max_errors if limits.value is not None else 64]
                return Ok(
                    {
                        "result": result,
                        "validation_fp1": params["validation_fp1"],
                        "receipt_fp1": rows[0][1],
                        "validation_current": not problems,
                        "current_errors": problems,
                        "publication_supported": False,
                        "authorizes_invoke": False,
                    }
                )
            if session.value.profile != "authoring":
                return policy_rejection("profile", "app-use cannot validate an authoring candidate")
            if params["expected_context_revision"] != session.value.context_revision:
                return policy_rejection(
                    "expected_context_revision",
                    "stale authoring context",
                    current=session.value.context_revision,
                )
            if limits.value is None:
                return unavailable()
            if params["catalog_fp1"] != catalog_fp1:
                return policy_rejection(
                    "catalog_fp1", "stale host catalog; refresh before validation"
                )
            return self._validate(
                params, version, catalog, catalog_fp1, limits.value, owner_principal, scope
            )

    def _validate(
        self,
        params: Mapping[str, object],
        version: Mapping[str, object],
        catalog: dict[str, object],
        catalog_fp1: str,
        limits: ValidationLimits,
        owner: str,
        scope: str | None,
    ) -> Result[Mapping[str, object]]:
        content = cast(dict[str, object], version["content"])
        ref = cast(dict[str, object], content["composition_ref"])
        raw = self.candidates.read_reference(ref)
        if is_refusal(raw):
            return raw
        problems: list[dict[str, object]] = []
        dependencies: list[dict[str, object]] = []
        body: dict[str, object] = {}
        if len(raw.value) > limits.max_bytes:
            problems.append(
                error("$", "LIMIT", "Composition bytes exceed host bound", "Reduce bytes")
            )
        else:
            parsed = json_object(raw.value)
            if is_refusal(parsed):
                problems.append(
                    error(
                        "$",
                        "JSON",
                        "Composition is not finite unambiguous Unicode JSON",
                        "Correct the JSON",
                    )
                )
            else:
                body = parsed.value
                problems.extend(validate_structure(body, limits))
                if not problems:
                    if body["catalog_fp1"] != catalog_fp1:
                        problems.append(
                            error(
                                "$/catalog_fp1",
                                "STALE_CATALOG",
                                "Composition pins a different catalog",
                                "Save a new version against current catalog",
                            )
                        )
                    dependencies, errors = self._dependencies(body, scope, version)
                    problems.extend(errors)
        if content["asset_refs"]:
            problems.append(
                error(
                    "$/asset_refs",
                    "UNSUPPORTED_ASSET",
                    "Custom assets require MA13",
                    "Use catalog components only",
                )
            )
        # Scope is immutable candidate scope, even under an unbound authoring caller.
        if version.get("instance_id") is not None and any(
            dep["instance_id"] != version["instance_id"] for dep in dependencies
        ):
            problems.append(
                error(
                    "$/bindings",
                    "SCOPE",
                    "Maintenance dependency outside candidate instance",
                    "Use dependencies on the immutable candidate scope",
                )
            )
        staged_catalog = self.candidates.artifacts.stage_complete_bytes(data_bytes(catalog))
        if is_refusal(staged_catalog):
            return staged_catalog
        operations = self._operations(scope)
        for dependency in dependencies:
            op = next(
                (
                    row
                    for row in operations
                    if all(
                        dependency[key] == value
                        for key, value in row.items()
                        if key != "descriptor"
                    )
                ),
                None,
            )
            if op is None:
                return policy_rejection(
                    "dependencies", "operation pins changed during validation; refresh and retry"
                )
            descriptor_bytes = data_bytes(op["descriptor"])
            staged_descriptor = self.candidates.artifacts.stage_complete_bytes(descriptor_bytes)
            if is_refusal(staged_descriptor):
                return staged_descriptor
            dependency["descriptor_ref"] = {
                "fp1": staged_descriptor.value.fp1,
                "byte_count": staged_descriptor.value.byte_count,
                "media_type": "application/json",
            }
        input_body = {
            "candidate_id": version["candidate_id"],
            "revision": version["revision"],
            "content_fp1": version["content_fp1"],
            "composition_ref": ref,
            "catalog_fp1": catalog_fp1,
            "validator_id": VALIDATOR_ID,
            "dependencies": dependencies,
            "owner_principal": owner,
            "product_session_ref": params["product_session_ref"],
            "context_revision": params["expected_context_revision"],
        }
        result = {
            **input_body,
            "schema": RESULT_SCHEMA,
            "validator_input_fp1": self._fp(input_body),
            "status": "invalid" if problems else "valid",
            "errors": sorted(problems, key=lambda e: (str(e["path"]), str(e["code"])))[
                : limits.max_errors
            ],
            "catalog_byte_count": staged_catalog.value.byte_count,
        }
        result["view_requests"] = (
            []
            if problems
            else [
                dict(
                    PackUiView(
                        view_id=f"view:{version['candidate_id']}:panel:{i}",
                        view_version=1,
                        op_id=cast(
                            str,
                            cast(dict[str, dict[str, object]], body["bindings"])[
                                cast(str, panel["data"])
                            ]["op_id"],
                        ),
                        renderer="json-render",
                        slot="canvas-widget",
                        parameter_schema=cast(
                            str,
                            cast(dict[str, dict[str, object]], body["bindings"])[
                                cast(str, panel["data"])
                            ]["input_schema"],
                        ),
                        ui_resource=cast(str, ref["fp1"]),
                        catalog_ref=catalog_fp1,
                    ).to_payload()
                )
                for i, panel in enumerate(cast(list[dict[str, object]], body.get("panels", [])))
            ]
        )
        schema_check = validate_instance(result, "miniapp_validation")
        if is_refusal(schema_check):
            return schema_check
        if len(data_bytes(result)) > 65536:
            return invalid_input("validation_result", "proof exceeds 64KiB; reduce composition")
        validation_fp1 = self._fp(result)
        rows = self.candidates.sqlite.execute(
            "SELECT receipt_fp1 FROM app_candidate_validation WHERE validation_fp1=?",
            (validation_fp1,),
        )
        if rows:
            return Ok(
                {
                    "result": result,
                    "validation_fp1": validation_fp1,
                    "receipt_fp1": rows[0][0],
                    "publication_supported": False,
                    "authorizes_invoke": False,
                }
            )
        held = self.candidates.artifacts.stage_complete_bytes(data_bytes(result))
        if is_refusal(held):
            return held
        event = self.candidates.journal.append_event(
            VALIDATED_EVENT,
            payload={
                "schema": RESULT_SCHEMA,
                "candidate_id": version["candidate_id"],
                "revision": version["revision"],
                "validation_fp1": validation_fp1,
                "byte_count": held.value.byte_count,
                "owner_principal": owner,
            },
        )
        if is_refusal(event):
            self._dirty = True
            return event
        try:
            self._insert(
                validation_fp1,
                result,
                event.value.record.journal_seq,
                event.value.record.fingerprint,
            )
        except (RuntimeError, sqlite3.Error) as exc:
            self._dirty = True
            return storage_failure(
                str(exc),
                context={
                    "operation_committed": True,
                    "validation_fp1": validation_fp1,
                    "retry_same_input": True,
                },
            )
        return Ok(
            {
                "result": result,
                "validation_fp1": validation_fp1,
                "receipt_fp1": event.value.record.fingerprint,
                "publication_supported": False,
                "authorizes_invoke": False,
            }
        )

    def _current_errors(
        self,
        result: dict[str, object],
        version: Mapping[str, object],
        scope: str | None,
        catalog_fp1: str,
        current_revision: object,
    ) -> list[dict[str, object]]:
        problems: list[dict[str, object]] = []
        if result["status"] != "valid":
            problems.append(
                error(
                    "$",
                    "INVALID_RESULT",
                    "Recorded validation failed",
                    "Correct errors in a new candidate version",
                )
            )
        if result["catalog_fp1"] != catalog_fp1 or result["validator_id"] != VALIDATOR_ID:
            problems.append(
                error(
                    "$",
                    "STALE_CATALOG",
                    "Host catalog/limits/validator changed",
                    "Revalidate exact candidate",
                )
            )
        if version["revision"] != current_revision:
            problems.append(
                error(
                    "$/revision",
                    "STALE_CANDIDATE",
                    "Candidate head has changed",
                    "Validate the intended current head",
                )
            )
        origin = self.candidates.sessions.get(result["product_session_ref"])
        if is_refusal(origin) or origin.value.context_revision != result["context_revision"]:
            problems.append(
                error(
                    "$/context_revision",
                    "STALE_CONTEXT",
                    "Authoring context changed",
                    "Revalidate under current authoring context",
                )
            )
        if is_refusal(
            self.candidates.read_reference(cast(dict[str, object], result["composition_ref"]))
        ):
            problems.append(
                error(
                    "$/composition_ref",
                    "STALE_REFERENCE",
                    "Exact composition bytes unavailable",
                    "Restage exact composition and revalidate",
                )
            )
        deps = cast(list[dict[str, object]], result["dependencies"])
        for dep in deps:
            if is_refusal(
                self.candidates.read_reference(cast(dict[str, object], dep["descriptor_ref"]))
            ):
                problems.append(
                    error(
                        "$/dependencies",
                        "STALE_REFERENCE",
                        "Archived descriptor bytes unavailable",
                        "Restore exact descriptor and revalidate",
                    )
                )
        bindings = {
            cast(str, dep["binding_id"]): {
                key: value
                for key, value in dep.items()
                if key not in {"binding_id", "descriptor_ref"}
            }
            for dep in deps
        }
        _, errors = self._dependencies({"bindings": bindings}, scope, version)
        problems.extend(errors)
        return problems

    def _insert(self, fp1: str, result: Mapping[str, object], seq: int, receipt: str) -> None:
        self.candidates.sqlite.execute(
            "INSERT OR REPLACE INTO app_candidate_validation VALUES (?,?,?,?,?,?)",
            (
                fp1,
                result["candidate_id"],
                result["revision"],
                json.dumps(result, sort_keys=True, ensure_ascii=True),
                seq,
                receipt,
            ),
        )

    def restore_from_journal(self) -> Result[int]:
        """Verify complete immutable receipts before replacing the derived projection."""
        events = self.candidates.journal.read_events()
        if is_refusal(events):
            return events
        recovered: list[tuple[str, dict[str, object], int, str]] = []
        for event in events.value:
            if event.event != VALIDATED_EVENT:
                continue
            identity = event.verify_identity()
            if is_refusal(identity):
                return identity
            payload = event.payload
            if (
                set(payload)
                != {
                    "schema",
                    "candidate_id",
                    "revision",
                    "validation_fp1",
                    "byte_count",
                    "owner_principal",
                }
                or payload["schema"] != RESULT_SCHEMA
            ):
                return invalid_input("app_candidate_validation", "malformed validation receipt")
            if (
                isinstance(payload["byte_count"], bool)
                or not isinstance(payload["byte_count"], int)
                or not 1 <= payload["byte_count"] <= 65536
            ):
                return invalid_input(
                    "app_candidate_validation", "recorded proof exceeds byte ceiling"
                )
            held = self.candidates.read_reference(
                {"fp1": payload["validation_fp1"], "byte_count": payload["byte_count"]}
            )
            if is_refusal(held):
                return held
            parsed = json_object(held.value)
            if is_refusal(parsed):
                return parsed
            result = parsed.value
            schema_check = validate_instance(result, "miniapp_validation")
            if is_refusal(schema_check):
                return schema_check
            required = {
                "schema",
                "candidate_id",
                "revision",
                "content_fp1",
                "composition_ref",
                "catalog_fp1",
                "validator_id",
                "dependencies",
                "owner_principal",
                "product_session_ref",
                "context_revision",
                "validator_input_fp1",
                "status",
                "errors",
                "catalog_byte_count",
                "view_requests",
            }
            if (
                set(result) != required
                or result["schema"] != RESULT_SCHEMA
                or not isinstance(result["status"], str)
                or result["status"] not in {"valid", "invalid"}
                or not isinstance(result["errors"], list)
                or not isinstance(result["dependencies"], list)
            ):
                return invalid_input("app_candidate_validation", "malformed validation result")
            if (result["status"] == "valid") != (not result["errors"]):
                return invalid_input("app_candidate_validation", "inconsistent result status")
            if (
                not isinstance(result["context_revision"], int)
                or isinstance(result["context_revision"], bool)
                or result["context_revision"] < 0
            ):
                return invalid_input(
                    "app_candidate_validation", "invalid recorded context revision"
                )
            for key in (
                "candidate_id",
                "revision",
                "content_fp1",
                "catalog_fp1",
                "validator_id",
                "validator_input_fp1",
                "owner_principal",
                "product_session_ref",
            ):
                if not isinstance(result[key], str) or not result[key]:
                    return invalid_input(
                        "app_candidate_validation", "invalid recorded identity field"
                    )
            input_body = {
                key: value
                for key, value in result.items()
                if key
                not in {
                    "schema",
                    "status",
                    "errors",
                    "validator_input_fp1",
                    "catalog_byte_count",
                    "view_requests",
                }
            }
            if (
                self._fp(input_body) != result["validator_input_fp1"]
                or self._fp(result) != payload["validation_fp1"]
                or any(
                    result[key] != payload[key]
                    for key in ("candidate_id", "revision", "owner_principal")
                )
            ):
                return invalid_input("app_candidate_validation", "validation identity mismatch")
            version = self.candidates.version_record(
                cast(str, result["candidate_id"]), cast(str, result["revision"])
            )
            if (
                version is None
                or any(result[key] != version[key] for key in ("content_fp1", "owner_principal"))
                or result["composition_ref"]
                != cast(dict[str, object], version["content"])["composition_ref"]
            ):
                return invalid_input(
                    "app_candidate_validation", "validation does not match candidate"
                )
            session = self.candidates.sessions.get(result["product_session_ref"])
            if (
                is_refusal(session)
                or session.value.profile != "authoring"
                or session.value.principal != PrincipalClass.OPERATOR.value
            ):
                return invalid_input(
                    "app_candidate_validation", "validation origin is not authoring"
                )
            catalog = self.candidates.read_reference(
                {"fp1": result["catalog_fp1"], "byte_count": result["catalog_byte_count"]}
            )
            if is_refusal(catalog):
                return catalog
            archived_catalog = json_object(catalog.value)
            if is_refusal(archived_catalog):
                return archived_catalog
            archived_limits = ValidationLimits.parse(archived_catalog.value.get("limits"))
            if is_refusal(archived_limits) or archived_catalog.value != self._catalog(
                archived_limits.value
            ):
                return invalid_input("app_candidate_validation", "unsupported archived catalog")
            if result["validator_id"] != VALIDATOR_ID:
                return invalid_input("app_candidate_validation", "unsupported validator identity")
            if result["status"] == "valid":
                composition = self.candidates.read_reference(
                    cast(dict[str, object], result["composition_ref"])
                )
                if is_refusal(composition):
                    return composition
                body = json_object(composition.value)
                if is_refusal(body):
                    return body
                if (
                    len(composition.value) > archived_limits.value.max_bytes
                    or validate_structure(body.value, archived_limits.value)
                    or body.value.get("catalog_fp1") != result["catalog_fp1"]
                ):
                    return invalid_input(
                        "app_candidate_validation", "successful proof has invalid composition"
                    )
                archived_ops: list[dict[str, object]] = []
                deps = cast(list[dict[str, object]], result["dependencies"])
                for dep in deps:
                    descriptor_ref = cast(dict[str, object], dep["descriptor_ref"])
                    if descriptor_ref["fp1"] != dep["descriptor_fp1"]:
                        return invalid_input("app_candidate_validation", "descriptor ref mismatch")
                    descriptor_bytes = self.candidates.read_reference(descriptor_ref)
                    if is_refusal(descriptor_bytes):
                        return descriptor_bytes
                    descriptor_body = json_object(descriptor_bytes.value)
                    if is_refusal(descriptor_body):
                        return descriptor_body
                    archived_ops.append(
                        {
                            key: value
                            for key, value in dep.items()
                            if key not in {"binding_id", "descriptor_ref", "parameters"}
                        }
                        | {"descriptor": descriptor_body.value}
                    )
                recovered_deps, problems = self._dependencies(
                    body.value, session.value.app_instance_id, version, archived_ops
                )
                stripped_deps = [
                    {key: value for key, value in dep.items() if key != "descriptor_ref"}
                    for dep in deps
                ]
                if problems or recovered_deps != stripped_deps:
                    return invalid_input(
                        "app_candidate_validation", "successful proof dependencies fail replay"
                    )
                if version.get("instance_id") is not None and any(
                    dep["instance_id"] != version["instance_id"] for dep in deps
                ):
                    return invalid_input(
                        "app_candidate_validation", "successful proof changes candidate scope"
                    )
                expected_views = [
                    dict(
                        PackUiView(
                            view_id=f"view:{version['candidate_id']}:panel:{i}",
                            view_version=1,
                            op_id=cast(
                                str,
                                cast(dict[str, dict[str, object]], body.value["bindings"])[
                                    cast(str, panel["data"])
                                ]["op_id"],
                            ),
                            renderer="json-render",
                            slot="canvas-widget",
                            parameter_schema=cast(
                                str,
                                cast(dict[str, dict[str, object]], body.value["bindings"])[
                                    cast(str, panel["data"])
                                ]["input_schema"],
                            ),
                            ui_resource=cast(
                                str, cast(dict[str, object], result["composition_ref"])["fp1"]
                            ),
                            catalog_ref=cast(str, result["catalog_fp1"]),
                        ).to_payload()
                    )
                    for i, panel in enumerate(cast(list[dict[str, object]], body.value["panels"]))
                ]
                if expected_views != result["view_requests"]:
                    return invalid_input(
                        "app_candidate_validation", "successful proof adapter changed"
                    )
            recovered.append(
                (cast(str, payload["validation_fp1"]), result, event.journal_seq, event.fingerprint)
            )
        try:

            def rebuild(conn: sqlite3.Connection) -> None:
                conn.execute("DELETE FROM app_candidate_validation")
                for fp1, result, seq, receipt in recovered:
                    conn.execute(
                        "INSERT INTO app_candidate_validation VALUES (?,?,?,?,?,?)",
                        (
                            fp1,
                            result["candidate_id"],
                            result["revision"],
                            json.dumps(result, sort_keys=True, ensure_ascii=True),
                            seq,
                            receipt,
                        ),
                    )

            self.candidates.sqlite.run(rebuild)
        except (RuntimeError, sqlite3.Error) as exc:
            return storage_failure(str(exc))
        self._dirty = False
        return Ok(len(recovered))
