"""``check(document, context)``: layers A to F, then the compile a passing document gets."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import is_refusal

from qml.check.layers import check_layers
from qml.check.result import (
    LAYERS,
    CheckResult,
    Verdict,
    checker_version,
    entries_snapshot,
    group,
    problem_set,
    records_snapshot,
)
from qml.unit.parse import Problem, ProblemKind, parse

if TYPE_CHECKING:
    from qml.compile import CompileContext, CompiledUnit

__all__ = ["check", "check_and_compile"]


def _document_fingerprint(document: object) -> str | None:
    made = fingerprint(document)
    return None if is_refusal(made) else made.value.value


def check_and_compile(
    document: object, context: CompileContext, previous_problem_set: str | None = None
) -> tuple[CheckResult, CompiledUnit | None]:
    """The check result, and the compiled unit when every layer passed and it compiled.

    A document that passes A to F is compiled, so the result carries its compiled
    fingerprint; what only the compiler refuses (a combiner or a stream the compiler format
    does not run yet) comes back as ``not_compiled`` errors.
    """
    from qml.compile import CompiledUnit, compile_unit  # noqa: PLC0415 - compile imports qml.check

    parsed = parse(document)
    errors: list[Problem] = list(parsed.problems)
    warnings: list[Problem] = []
    layers: tuple[str, ...] = ("A",)
    compiled: CompiledUnit | None = None
    if parsed.unit is None:
        warnings.append(
            Problem(
                ProblemKind.LAYER_SKIPPED,
                ("",),
                "layers B to F did not run, because the document's shape does not hold",
                "fix the shape problems first",
                "A",
            )
        )
    else:
        layers = LAYERS
        found = check_layers(
            parsed.unit, entries=context.entries, sources=context.sources, records=context.records
        )
        errors += found.errors
        warnings += found.warnings
        if not errors:
            built = compile_unit(document, context)
            if isinstance(built, CompiledUnit):
                compiled = built
            else:
                errors += [
                    Problem(
                        ProblemKind.NOT_COMPILED,
                        (p.where,),
                        f"{p.kind}: {p.message}"[:300],
                        "the compiler format does not run this yet; write it another way",
                        "compile",
                    )
                    for p in built
                ]
    grouped_errors, grouped_warnings = group(errors), group(warnings)
    current = problem_set(grouped_errors, grouped_warnings)
    result = CheckResult(
        verdict=Verdict.FAIL if grouped_errors else Verdict.PASS,
        errors=grouped_errors,
        warnings=grouped_warnings,
        layers_run=layers,
        document_fingerprint=_document_fingerprint(document),
        checker_version=checker_version(),
        entries_snapshot=entries_snapshot(context.entries, context.sources),
        records_snapshot=records_snapshot(context.records),
        problem_set=current,
        no_progress=bool(grouped_errors) and previous_problem_set == current,
        compiled_fingerprint=None if compiled is None else compiled.compiled_fingerprint.value,
    )
    return result, compiled


def check(
    document: object, context: CompileContext, previous_problem_set: str | None = None
) -> CheckResult:
    """Every problem of every layer that can run, counts first (AD-110)."""
    return check_and_compile(document, context, previous_problem_set)[0]
