"""Versioned ATC evaluator phases preserve the uncertainty boundary on restart."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from qmb._refuse import invalid
from qmb.execution.alternative_terminal import AlternativeTerminalStore
from qmb.host.operator_alternative_study import run_operator_alternative_study
from qmf.core import Result, canonical_bytes, is_refusal
from test_operator_alternative_study import (
    _inputs as _study_inputs,  # pyright: ignore[reportPrivateUsage]
)
from test_operator_alternative_study import (  # pyright: ignore[reportPrivateUsage]
    _LocalStudyInterpreter,  # pyright: ignore[reportPrivateUsage]
)
from test_operator_alternative_study import (
    _ok as _study_ok,  # pyright: ignore[reportPrivateUsage]
)
from test_operator_alternative_study import (
    _plan as _study_plan,  # pyright: ignore[reportPrivateUsage]
)


def test_legacy_reserved_intent_without_phase_protocol_stays_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, _ = _study_inputs(tmp_path)
    plan = _study_plan(inputs)
    original_start = AlternativeTerminalStore.start_trial

    def stop_before_start(self: AlternativeTerminalStore, **_kwargs: object) -> Result[None]:
        return invalid("injected", "leave a durable reservation with no evaluator-start row")

    monkeypatch.setattr(AlternativeTerminalStore, "start_trial", stop_before_start)
    assert is_refusal(run_operator_alternative_study(inputs, plan))
    pending = _study_ok(inputs.terminal_store.pending_trials())
    assert len(pending) == 1
    assert next(iter(pending.values()))["phase_protocol"] == 1

    rows = [
        json.loads(line)
        for line in inputs.terminal_store.path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 1
    rows[0].pop("phase_protocol")
    encoded = canonical_bytes(rows[0])
    assert not is_refusal(encoded)
    inputs.terminal_store.path.write_bytes(encoded.value + b"\n")

    monkeypatch.setattr(AlternativeTerminalStore, "start_trial", original_start)
    registration = next(iter(inputs.registry.registrations.values()))
    interpreter = cast("_LocalStudyInterpreter", registration.interpreter)
    restart = run_operator_alternative_study(inputs, plan)
    assert is_refusal(restart)
    assert interpreter.calls == 0
    pending_after = _study_ok(inputs.terminal_store.pending_trials())
    assert len(pending_after) == 1
    assert next(iter(pending_after.values())).get("phase_protocol") is None
