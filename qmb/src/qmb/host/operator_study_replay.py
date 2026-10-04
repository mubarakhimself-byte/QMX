"""Private, fully pinned Alternative Study binding behind the existing QMB door."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

from qmf.core import Fingerprint, Ok, Result, fingerprint, is_refusal
from qmf.core.exact import RoundingMode

from qmb._refuse import invalid, policy, unavailable
from qmb.host.operator_alternative import OperatorAlternativeInputs
from qmb.host.operator_alternative_replay import (
    OperatorAlternativeBinding,
    decode_operator_alternative_binding,
    with_operator_alternative_inputs,
)
from qmb.host.operator_alternative_study import (
    OperatorAlternativeStudyPlan,
    run_operator_alternative_study,
    verify_operator_alternative_study,
)
from qmb.host.qma_cli import QmaBacktestContext, validate_qma_backtest_context
from qmb.optimize.alternative_study import AlternativeParameterBinding, AlternativeStudyObjective
from qmb.optimize.space import coerce_study_space

STUDY_BINDING_FILENAME = "operator-alternative-study-binding.json"
STUDY_BINDING_CLASS = "qmb-operator-alternative-study-binding-v1"
_FIELDS = frozenset(
    {
        "class",
        "format_version",
        "composition_class",
        "alternative_binding",
        "study",
        "study_fp1",
        "descriptor_fp1",
    }
)
_STUDY_FIELDS = frozenset(
    {
        "parameter_space",
        "seed",
        "direction",
        "rounding",
        "batch_size",
        "generation_count",
        "objective",
        "parameter_bindings",
    }
)


@dataclass(frozen=True, slots=True)
class OperatorStudyBinding:
    base: OperatorAlternativeBinding
    study: Mapping[str, object]
    study_fp1: Fingerprint
    descriptor_fp1: Fingerprint


def select_operator_composition(*, runtime_root: object, context: object) -> Result[str]:
    """Presence selects exactly one branch; malformed descriptors never fall through."""
    checked = validate_qma_backtest_context(context)
    if is_refusal(checked):
        return checked
    if not isinstance(runtime_root, str | Path) or not Path(runtime_root).is_absolute():
        return invalid("runtime_root", "operator runtime root is absolute")
    directory = (
        Path(runtime_root)
        / checked.value.experiment_spec_fp1.value.replace(":", "-")
        / checked.value.evidence_ref.value.replace(":", "-")
    )
    selected: list[str] = []
    for name, filename in (
        ("book", "operator-binding.json"),
        ("alternative", "operator-alternative-binding.json"),
        ("alternative-study", STUDY_BINDING_FILENAME),
    ):
        try:
            # lstat includes broken links, which must select and then refuse.
            (directory / filename).lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            return unavailable(
                "operator_binding", "descriptor presence is readable", error=str(exc)
            )
        selected.append(name)
    if len(selected) != 1:
        return policy("composition_class", "exactly one complete operator descriptor is selected")
    return Ok(selected[0])


def read_operator_study_binding(
    *, runtime_root: object, context: object
) -> Result[OperatorStudyBinding]:
    selected = select_operator_composition(runtime_root=runtime_root, context=context)
    if is_refusal(selected):
        return selected
    if selected.value != "alternative-study" or not isinstance(context, QmaBacktestContext):
        return policy("composition_class", "Study uses its explicitly selected private descriptor")
    if context.command != "optimize.run" or context.mints_ct32 is not False:
        return policy("command", "Study is admitted only through the non-CT-32 optimize door")
    path = (
        Path(cast(str | Path, runtime_root))
        / context.experiment_spec_fp1.value.replace(":", "-")
        / context.evidence_ref.value.replace(":", "-")
        / STUDY_BINDING_FILENAME
    )
    try:
        if path.is_symlink():
            return policy("operator_binding", "Study descriptor is a regular operator file")
        with path.open("rb") as stream:
            raw = stream.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            return invalid("operator_binding", "Study descriptor stays within its bounded size")
        body = json.loads(raw, object_pairs_hook=_unique_pairs)
    except (OSError, ValueError, TypeError) as exc:
        return invalid(
            "operator_binding", "Study descriptor is readable strict JSON", error=str(exc)
        )
    if not isinstance(body, Mapping):
        return invalid("operator_binding", "Study descriptor has exactly its versioned fields")
    row = cast(Mapping[str, object], body)
    if set(row) != set(_FIELDS):
        return invalid("operator_binding", "Study descriptor has exactly its versioned fields")
    if (
        row["class"] != STUDY_BINDING_CLASS
        or type(row["format_version"]) is not int
        or row["format_version"] != 1
        or row["composition_class"] != "alternative-study"
    ):
        return invalid("operator_binding", "Study descriptor has its declared class and version")
    descriptor = Fingerprint.try_create(row["descriptor_fp1"])
    actual = fingerprint({key: value for key, value in row.items() if key != "descriptor_fp1"})
    if is_refusal(descriptor):
        return descriptor
    if is_refusal(actual) or actual.value != descriptor.value:
        return policy("descriptor_fp1", "complete Study descriptor matches its fingerprint")
    if (
        context.operator_descriptor_fp1 is not None
        and context.operator_descriptor_fp1 != descriptor.value
    ):
        return policy("operator_descriptor_fp1", "Study placement retains its exact preflight pin")
    base = decode_operator_alternative_binding(
        row["alternative_binding"], context=replace(context, operator_descriptor_fp1=None)
    )
    if is_refusal(base):
        return base
    study = row["study"]
    if not isinstance(study, Mapping):
        return invalid("study", "private Study declaration has exactly its typed planning fields")
    study_map = cast(Mapping[str, object], study)
    if set(study_map) != set(_STUDY_FIELDS):
        return invalid("study", "private Study declaration has exactly its typed planning fields")
    study_fp = Fingerprint.try_create(row["study_fp1"])
    if is_refusal(study_fp):
        return study_fp
    pinned_context = replace(context, operator_descriptor_fp1=descriptor.value)
    return Ok(
        OperatorStudyBinding(
            replace(base.value, context=pinned_context, descriptor_fp1=descriptor.value),
            study_map,
            study_fp.value,
            descriptor.value,
        )
    )


def _plan(
    inputs: OperatorAlternativeInputs, binding: OperatorStudyBinding
) -> Result[OperatorAlternativeStudyPlan]:
    row = binding.study
    space_identity = row["parameter_space"]
    if not isinstance(space_identity, Mapping):
        return invalid("parameter_space", "Study pins its canonical parameter-space identity")
    space_map = cast(Mapping[str, object], space_identity)
    if set(space_map) != {
        "class",
        "format_version",
        "parameter_order",
        "parameters",
    }:
        return invalid("parameter_space", "Study pins its canonical parameter-space identity")
    space = coerce_study_space(space_map.get("parameters"))
    if is_refusal(space):
        return space
    space_fp = fingerprint(space_map)
    rebuilt_space_fp = space.value.fingerprint()
    if (
        is_refusal(space_fp)
        or is_refusal(rebuilt_space_fp)
        or space_fp.value != rebuilt_space_fp.value
    ):
        return policy(
            "parameter_space", "canonical Study space reconstructs through CT-33 admission"
        )
    objective = row["objective"]
    if not isinstance(objective, Mapping):
        return invalid("objective", "Study objective uses its exact registered measure schema")
    obj = cast(Mapping[str, object], objective)
    if (
        set(obj)
        not in (
            {"class", "measure_identity", "direction", "unit_kind"},
            {"class", "measure_identity", "direction", "unit_kind", "currency"},
        )
        or obj.get("class") != "qmb-atc-study-objective-v1"
    ):
        return invalid("objective", "Study objective uses its exact registered measure schema")
    parsed_objective = AlternativeStudyObjective.try_create(
        obj["measure_identity"], obj["direction"], obj["unit_kind"], obj.get("currency")
    )
    if is_refusal(parsed_objective):
        return parsed_objective
    raw_bindings = row["parameter_bindings"]
    if not isinstance(raw_bindings, list | tuple):
        return invalid("parameter_bindings", "Study binds an ordered parameter sequence")
    bindings: list[AlternativeParameterBinding] = []
    for raw in cast(Sequence[object], raw_bindings):
        if not isinstance(raw, Mapping):
            return invalid("parameter_bindings", "Study binding uses its exact registered schema")
        item = cast(Mapping[str, object], raw)
        if set(item) != {
            "class",
            "parameter_name",
            "component",
            "field_name",
        }:
            return invalid("parameter_bindings", "Study binding uses its exact registered schema")
        if item["class"] != "qmb-atc-study-parameter-binding-v1":
            return invalid("parameter_bindings", "Study binding has its declared class")
        parsed = AlternativeParameterBinding.try_create(
            item["parameter_name"], item["component"], item["field_name"]
        )
        if is_refusal(parsed):
            return parsed
        bindings.append(parsed.value)
    try:
        rounding = RoundingMode(row["rounding"])
    except (ValueError, TypeError):
        return invalid("rounding", "Study names an exact registered rounding mode")
    plan = OperatorAlternativeStudyPlan.try_create(
        inputs,
        parameter_space=space.value,
        seed=row["seed"],
        direction=row["direction"],
        rounding=rounding,
        batch_size=row["batch_size"],
        generation_count=row["generation_count"],
        objective=parsed_objective.value,
        bindings=tuple(bindings),
    )
    if is_refusal(plan):
        return plan
    if plan.value.fingerprint != binding.study_fp1:
        return policy(
            "study_fp1", "Study computation reconstructs from the registered pinned ports"
        )
    return plan


def invoke_operator_study(
    *,
    runtime_root: object,
    context: object,
    mode: str,
    claimed_result: object = None,
    cancelled: object = None,
) -> Result[Mapping[str, object]]:
    binding = read_operator_study_binding(runtime_root=runtime_root, context=context)
    if is_refusal(binding):
        return binding
    if mode not in {"preflight", "execute", "verify"}:
        return invalid("mode", "Study uses one explicit invocation mode")
    if mode != "preflight" and cast(QmaBacktestContext, context).operator_descriptor_fp1 is None:
        return policy(
            "operator_descriptor_fp1", "Study execution and verification retain the preflight pin"
        )

    def operation(inputs: OperatorAlternativeInputs) -> Result[Mapping[str, object]]:
        plan = _plan(inputs, binding.value)
        if is_refusal(plan):
            return plan
        if mode == "preflight":
            return Ok(
                {
                    "study_fp1": plan.value.fingerprint.value,
                    "operational_fp1": plan.value.operational_fingerprint.value,
                    "generation_count": plan.value.generation_count,
                    "batch_size": plan.value.batch_size,
                    "operator_descriptor_fp1": binding.value.descriptor_fp1.value,
                }
            )
        result = (
            verify_operator_alternative_study(inputs, plan.value)
            if mode == "verify"
            else run_operator_alternative_study(inputs, plan.value, cancelled=cancelled)
        )
        if is_refusal(result):
            return result
        payload = result.value.identity()
        if mode == "verify" and claimed_result is not None:
            claimed = (
                fingerprint(cast(Mapping[str, object], claimed_result))
                if isinstance(claimed_result, Mapping)
                else None
            )
            actual = fingerprint(payload)
            if (
                claimed is None
                or is_refusal(claimed)
                or is_refusal(actual)
                or claimed.value != actual.value
            ):
                return policy(
                    "claimed_result", "Study claim equals the exact reopened history and witness"
                )
        return Ok(payload)

    return with_operator_alternative_inputs(binding.value.base, operation)


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result
