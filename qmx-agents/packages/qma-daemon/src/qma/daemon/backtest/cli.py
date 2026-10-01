"""Production QMB door: spawn a real ``qmb`` CLI process (Story 36.2 / 36.5).

Agent → QMA backtest tool → Backtesting Service → this transport → ``qmb``
CLI → QMB. MCP is later. This module never imports the ``qmb`` package.

``RecordingQmbDoorTransport`` is not production and must not be presented as
a working integration. Acceptance tests that claim the door works spawn
``qmb`` or the documented test double written by ``write_qmb_cli_test_double``.
``JobHandle.cancel`` maps onto QMB abort; QMB writes the ``aborted`` ledger
line and QMA does not.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Final, Literal, cast

from qma.core.ports.cancel_authority import PRODUCTION_DOOR_MAPS_CANCEL_TO_QMB_ABORT
from qma.core.ports.qmb import (
    QMB_CLI_PROGRAM,
    QMB_OCCUPANCY_QUERY,
    QMB_ROUTE,
    QMB_WORLD_REPLAY,
    QmbAbortReceipt,
    QmbDoorInvocation,
    QmbDoorKind,
    QmbDoorReceipt,
    occupancy_from_invocation,
    refuse_qmb_import_edge,
    refuse_venue_account_backtest,
)
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "QMB_CLI_TEST_DOUBLE_SOURCE",
    "CliQmbDoorTransport",
    "SpawnedQmbProcess",
    "cli_qmb_test_double_argv0",
    "write_qmb_cli_test_double",
]


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


QMB_CLI_TEST_DOUBLE_SOURCE: Final[str] = '''\
"""Documented QMB CLI test double (Story 36.2 / 36.5; NFR-W05).

Spawned by CliQmbDoorTransport as a real process. Not production and not
RecordingQmbDoorTransport. Writes a JSON receipt when QMA_QMB_RECEIPT_PATH
is set. Query argv ``analysis project`` prints canonical saved-view JSON.
Hang mode waits for QMA_QMB_CANCEL_PATH then writes an aborted QMB ledger
line — QMA never writes that file.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def _aborted_line(job_id: str) -> dict[str, object]:
    return {
        "role": "aborted",
        "state": "aborted",
        "writer": "qmb",
        "job_id": job_id,
        "cause": "cancel",
    }


def main() -> int:
    argv = sys.argv[1:]
    job_id = os.environ.get("QMA_QMB_JOB_ID", "")
    cancel_path = os.environ.get("QMA_QMB_CANCEL_PATH")
    ledger_path = os.environ.get("QMA_QMB_LEDGER_PATH")
    hang = os.environ.get("QMA_QMB_HANG") == "1"

    def write_aborted() -> None:
        if ledger_path:
            Path(ledger_path).write_text(
                json.dumps(_aborted_line(job_id)),
                encoding="utf-8",
            )

    if hang:
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            if cancel_path and Path(cancel_path).is_file():
                write_aborted()
                return 1
            time.sleep(0.05)
        write_aborted()
        return 1

    if argv[:2] == ["analysis", "project"]:
        view = {
            "as_of": {"kind": "registry-as-of", "value_ns": 0},
            "method": "projection",
            "predicate": {},
            "source_ct29": os.environ.get("QMA_QMB_SOURCE_CT29", "ct29:stream"),
            "source_ct32": os.environ.get(
                "QMA_QMB_SOURCE_CT32",
                "fp1:sha256:" + ("c" * 64),
            ),
        }
        sys.stdout.write(json.dumps(view, separators=(",", ":")))
        sys.stdout.flush()

    payload = {
        "argv": argv,
        "program": Path(sys.argv[0]).name,
        "world": os.environ.get("QMA_QMB_WORLD", ""),
        "job_id": job_id,
        "attempt_id": os.environ.get("QMA_QMB_ATTEMPT_ID", ""),
        "experiment_spec_fp1": os.environ.get("QMA_QMB_EXPERIMENT_SPEC_FP1", ""),
        "evidence_ref": os.environ.get("QMA_QMB_EVIDENCE_REF", ""),
        "split_manifest_fp1": os.environ.get("QMA_QMB_SPLIT_MANIFEST_FP1", ""),
        "pid": os.getpid(),
    }
    out = os.environ.get("QMA_QMB_RECEIPT_PATH")
    if out:
        Path(out).write_text(json.dumps(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_qmb_cli_test_double(path: Path) -> Path:
    """Write the documented spawnable ``qmb`` CLI stand-in to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(QMB_CLI_TEST_DOUBLE_SOURCE, encoding="utf-8")
    return path


def cli_qmb_test_double_argv0(path: Path) -> tuple[str, ...]:
    """``argv0`` that makes ``CliQmbDoorTransport`` spawn the documented double."""
    written = write_qmb_cli_test_double(path)
    return (sys.executable, str(written))


@dataclass(frozen=True, slots=True)
class SpawnedQmbProcess:
    """One placed ``qmb`` CLI process. QMB owns the run; QMA holds the pid."""

    job_id: str
    pid: int
    argv: tuple[str, ...]
    command: tuple[str, ...]


def _payload_str(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _door_env(
    invocation: QmbDoorInvocation,
    *,
    receipt_path: str | None,
    cancel_path: str | None,
    ledger_path: str | None,
    hang: bool,
) -> dict[str, str]:
    env = {str(key): str(value) for key, value in os.environ.items()}
    payload = dict(invocation.payload)
    identity_env_keys = (
        "QMA_QMB_JOB_ID",
        "QMA_QMB_ATTEMPT_ID",
        "QMA_QMB_EXPERIMENT_SPEC_FP1",
        "QMA_QMB_EVIDENCE_REF",
        "QMA_QMB_SPLIT_MANIFEST_FP1",
        "QMA_QMB_ENVIRONMENT_REF",
        "QMA_QMB_OCCUPANCY_KEY",
    )
    for key in identity_env_keys:
        env.pop(key, None)
    env.pop("QMA_QMB_PREFLIGHT", None)
    env.pop("QMA_QMB_VERIFY", None)
    env.pop("QMA_QMB_VERIFY_CLAIM_FILE", None)
    env.pop("QMA_QMB_VERIFY_DURABLE", None)
    env["QMA_QMB_DOOR"] = "cli"
    payload.setdefault("operator_descriptor_fp1", None)
    env["QMA_QMB_WORLD"] = str(payload.get("world", QMB_WORLD_REPLAY))
    env["QMA_QMB_DOOR_PAYLOAD"] = json.dumps(payload, separators=(",", ":"))
    for key, env_key in (
        ("job_id", "QMA_QMB_JOB_ID"),
        ("experiment_spec_fp1", "QMA_QMB_EXPERIMENT_SPEC_FP1"),
        ("evidence_ref", "QMA_QMB_EVIDENCE_REF"),
        ("split_manifest_fp1", "QMA_QMB_SPLIT_MANIFEST_FP1"),
        ("environment_ref", "QMA_QMB_ENVIRONMENT_REF"),
        ("occupancy_key", "QMA_QMB_OCCUPANCY_KEY"),
        ("source_ct32", "QMA_QMB_SOURCE_CT32"),
        ("source_ct29", "QMA_QMB_SOURCE_CT29"),
    ):
        value = _payload_str(payload, key)
        if value is not None:
            env[env_key] = value
    attempt_id = payload.get("attempt_id")
    if isinstance(attempt_id, int) and not isinstance(attempt_id, bool) and attempt_id > 0:
        env["QMA_QMB_ATTEMPT_ID"] = str(attempt_id)
    if receipt_path:
        env["QMA_QMB_RECEIPT_PATH"] = receipt_path
    if cancel_path:
        env["QMA_QMB_CANCEL_PATH"] = cancel_path
    if ledger_path:
        env["QMA_QMB_LEDGER_PATH"] = ledger_path
    if hang:
        env["QMA_QMB_HANG"] = "1"
    return env


def _supports_runtime_preflight(argv0: tuple[str, ...]) -> bool:
    """Only the production QMB executable implements the internal preflight."""
    if argv0 == (QMB_CLI_PROGRAM,):
        return True
    return len(argv0) == 1 and Path(argv0[0]).name == Path(QMB_CLI_PROGRAM).name


def _runtime_preflight(
    command: tuple[str, ...], env: Mapping[str, str], payload: Mapping[str, object]
) -> Result[Mapping[str, object]]:
    """Resolve the trusted QMB descriptor before starting the actual run child."""
    try:
        completed = subprocess.run(
            list(command),
            env=dict(env),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return policy_rejection(
            "qmb_preflight",
            "the QMB operator descriptor is resolved before process placement",
            error=str(exc),
        )
    if completed.returncode != 0:
        return policy_rejection(
            "qmb_preflight",
            "the trusted QMB operator descriptor preflight succeeds",
            returncode=completed.returncode,
            stderr=completed.stderr[-1000:],
        )
    try:
        raw = json.loads(completed.stdout, object_pairs_hook=_unique_json_object)
    except ValueError, TypeError:
        return invalid_input("qmb_preflight", "QMB preflight returns one JSON object")
    base_keys = {
        "class",
        "format_version",
        "job_id",
        "attempt_id",
        "environment_ref",
        "occupancy_key",
        "experiment_spec_fp1",
        "evidence_ref",
        "split_manifest_fp1",
        "composition_class",
        "mints_ct32",
        "operator_descriptor_fp1",
    }
    if not isinstance(raw, Mapping):
        return invalid_input("qmb_preflight", "QMB preflight uses the exact result schema")
    result = cast(Mapping[str, object], raw)
    composition = result.get("composition_class")
    if not isinstance(composition, str):
        return invalid_input("qmb_preflight", "QMB composition class is supported text")
    study_keys: set[str] = {
        "study_fp1",
        "operational_fp1",
        "generation_count",
        "batch_size",
    }
    expected_keys: set[str] = base_keys | (
        study_keys if composition == "alternative-study" else set[str]()
    )
    if set(result) != expected_keys:
        return invalid_input("qmb_preflight", "QMB preflight uses the exact result schema")
    if (
        result.get("class") != "qmb-runtime-preflight-v1"
        or type(result.get("format_version")) is not int
        or result.get("format_version") != 1
    ):
        return invalid_input("qmb_preflight", "QMB preflight uses the supported result class")
    for key in (
        "job_id",
        "attempt_id",
        "environment_ref",
        "occupancy_key",
        "experiment_spec_fp1",
        "evidence_ref",
        "split_manifest_fp1",
    ):
        expected = payload.get(key)
        actual = result.get(key)
        if type(actual) is not type(expected) or actual != expected:
            return policy_rejection(
                "qmb_preflight",
                "preflight output is bound to this QMA placement",
                mismatch_field=key,
            )
    if type(result.get("mints_ct32")) is not bool:
        return invalid_input("qmb_preflight", "QMB result mode is an exact boolean")
    expected_mode = {"book": True, "alternative": False, "alternative-study": False}.get(
        composition
    )
    if expected_mode is None or result.get("mints_ct32") is not expected_mode:
        return invalid_input("qmb_preflight", "QMB result mode matches the selected composition")
    command_name = payload.get("command")
    if command_name == "optimize.run" and composition != "alternative-study":
        return policy_rejection(
            "composition_class", "optimize.run preflight resolves the registered Study adapter"
        )
    if composition == "alternative-study":
        for key in ("study_fp1", "operational_fp1"):
            value = result.get(key)
            if (
                not isinstance(value, str)
                or re.fullmatch(r"fp1:sha256:[0-9a-f]{64}", value) is None
            ):
                return invalid_input(key, "Study preflight pins its exact plan fingerprints")
        for key in ("generation_count", "batch_size"):
            value = result.get(key)
            if type(value) is not int or value < 1:
                return invalid_input(key, "Study preflight pins positive exact counts")
    descriptor_fp = result.get("operator_descriptor_fp1")
    if (
        not isinstance(descriptor_fp, str)
        or re.fullmatch(r"fp1:sha256:[0-9a-f]{64}", descriptor_fp) is None
    ):
        return invalid_input(
            "qmb_preflight", "QMB preflight pins a canonical descriptor fingerprint"
        )
    return Ok(result)


def _decode_terminal_result(raw: str) -> Result[Mapping[str, object]]:
    """Decode a verifier response already matched to a validated child claim."""
    try:
        value = json.loads(raw, object_pairs_hook=_unique_json_object)
    except ValueError, TypeError:
        return invalid_input("qmb_terminal_result", "QMB verifier response is strict JSON")
    if not isinstance(value, Mapping):
        return invalid_input("qmb_terminal_result", "QMB verifier response is an object")
    return Ok(dict(cast(Mapping[str, object], value)))


@dataclass
class CliQmbDoorTransport:
    """Production QMB door. Spawns a ``qmb`` CLI process and never imports ``qmb``.

    Production ``argv0`` is ``("qmb",)``. Tests that claim the door works pass
    ``cli_qmb_test_double_argv0`` so this class still subprocess-spawns.
    """

    argv0: tuple[str, ...] = (QMB_CLI_PROGRAM,)
    receipt_path: str | None = None
    cancel_path: str | None = None
    ledger_path: str | None = None
    hang: bool = False
    query_timeout: float = 10.0
    production: Literal[True] = True
    spawns_qmb_process: Literal[True] = True
    maps_cancel_to_qmb_abort: Literal[True] = PRODUCTION_DOOR_MAPS_CANCEL_TO_QMB_ABORT
    _processes: dict[str, subprocess.Popen[bytes] | subprocess.Popen[str]] = field(
        default_factory=dict[str, subprocess.Popen[bytes] | subprocess.Popen[str]]
    )
    _spawned: list[SpawnedQmbProcess] = field(default_factory=list[SpawnedQmbProcess])
    _abort_invocations: list[str] = field(default_factory=list[str])
    _cancel_paths: dict[str, str] = field(default_factory=dict[str, str])
    _stdout_by_job: dict[str, str] = field(default_factory=dict[str, str])
    _invocations_by_job: dict[str, QmbDoorInvocation] = field(
        default_factory=dict[str, QmbDoorInvocation]
    )
    _verified_stdout_by_job: dict[str, str] = field(default_factory=dict[str, str])
    _preflight_by_job: dict[str, Mapping[str, object]] = field(
        default_factory=dict[str, Mapping[str, object]]
    )
    _preflight_payload_by_job: dict[str, Mapping[str, object]] = field(
        default_factory=dict[str, Mapping[str, object]]
    )
    _wait_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _verify_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def abort_invocations(self) -> tuple[str, ...]:
        return tuple(self._abort_invocations)

    @property
    def spawned(self) -> tuple[SpawnedQmbProcess, ...]:
        return tuple(self._spawned)

    @property
    def spawned_pids(self) -> tuple[int, ...]:
        return tuple(row.pid for row in self._spawned)

    def command_for(self, invocation: QmbDoorInvocation) -> tuple[str, ...]:
        """Argv placed on the OS. Prefix is the CLI binary; suffix is door argv."""
        prefix = tuple(self.argv0) if self.argv0 else (QMB_CLI_PROGRAM,)
        return (*prefix, *invocation.argv)

    def _cancel_path_for(self, job_id: str) -> str:
        existing = self._cancel_paths.get(job_id)
        if existing is not None:
            return existing
        if self.cancel_path:
            return self.cancel_path
        safe = job_id.replace(":", "_").replace("/", "_")
        if self.receipt_path:
            return f"{self.receipt_path}.{safe}.cancel"
        return f"{safe}.qmb.cancel"

    def preflight(self, invocation: QmbDoorInvocation) -> Result[Mapping[str, object] | None]:
        """Resolve and cache the trusted runtime mode without placing a child."""
        if invocation.import_edge or invocation.program != QMB_CLI_PROGRAM:
            return refuse_qmb_import_edge(given=invocation.program)
        payload = dict(invocation.payload)
        if payload.get("occupancy") != "run":
            return policy_rejection("occupancy", "operator preflight applies only to runs")
        job_id = payload.get("job_id")
        if not isinstance(job_id, str) or not job_id:
            return invalid_input("job_id", "operator preflight requires the exact QMA job id")
        cached = self._preflight_by_job.get(job_id)
        if cached is not None and self._preflight_payload_by_job.get(job_id) == payload:
            return Ok(cached)
        if not _supports_runtime_preflight(self.argv0):
            return Ok(None)
        env = _door_env(
            invocation,
            receipt_path=self.receipt_path,
            cancel_path=self._cancel_path_for(job_id),
            ledger_path=self.ledger_path,
            hang=False,
        )
        env["QMA_QMB_PREFLIGHT"] = "1"
        checked = _runtime_preflight(self.command_for(invocation), env, payload)
        if is_refusal(checked):
            return checked
        self._preflight_payload_by_job[job_id] = dict(payload)
        self._preflight_by_job[job_id] = checked.value
        return Ok(checked.value)

    def abort(self, job_id: str) -> Result[QmbAbortReceipt]:
        """Map JobHandle.cancel onto QMB abort. QMB writes the aborted ledger line."""
        proc = self._processes.get(job_id)
        if proc is None:
            return invalid_input(
                "job_id",
                "JobHandle.cancel maps to QMB abort only for a spawned qmb process",
                given=job_id,
            )
        self._abort_invocations.append(job_id)
        cancel_path = self._cancel_path_for(job_id)
        Path(cancel_path).write_text("JobHandle.cancel", encoding="utf-8")
        if proc.poll() is None:
            # Cooperative cancel first: the child writes the aborted ledger
            # when it sees cancel_path. SIGINT/terminate before that race
            # kills the hang loop on Linux and the ledger never appears.
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                if sys.platform != "win32":
                    try:
                        os.kill(int(proc.pid), signal.SIGINT)
                    except OSError:
                        proc.terminate()
                else:
                    proc.terminate()
                try:
                    proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=2.0)
        return Ok(
            QmbAbortReceipt(
                job_id=job_id,
                mapped_from="JobHandle.cancel",
            )
        )

    def submit(self, invocation: QmbDoorInvocation) -> Result[QmbDoorReceipt]:
        if invocation.import_edge or invocation.program != QMB_CLI_PROGRAM:
            return refuse_qmb_import_edge(given=invocation.program)
        if invocation.kind is QmbDoorKind.MCP:
            return policy_rejection(
                "door",
                "the QMB door ships CLI first; MCP is later (DEC-0276; FR-W08)",
                given=invocation.kind.value,
            )
        payload = dict(invocation.payload)
        if payload.get("import_edge") is True:
            return refuse_qmb_import_edge()
        world = payload.get("world", QMB_WORLD_REPLAY)
        if world != QMB_WORLD_REPLAY:
            return refuse_venue_account_backtest(field="world", given=world)
        if payload.get("recorded") is not True:
            return refuse_venue_account_backtest(field="recorded", given=payload.get("recorded"))
        attempt_id = payload.get("attempt_id")
        if isinstance(attempt_id, bool) or not isinstance(attempt_id, int) or attempt_id < 1:
            return invalid_input("attempt_id", "QMB door invocation requires a positive attempt id")
        job_id = payload.get("job_id")
        environment_ref = payload.get("environment_ref")
        occupancy_key = payload.get("occupancy_key")
        if not isinstance(job_id, str) or not job_id:
            return invalid_input("job_id", "QMB door invocation requires a job id")
        if not isinstance(environment_ref, str) or not environment_ref:
            return invalid_input("environment_ref", "QMB door invocation requires environment_ref")
        if not isinstance(occupancy_key, str) or not occupancy_key:
            occupancy_key = environment_ref
        classified = occupancy_from_invocation(invocation)
        is_query = classified.occupancy == QMB_OCCUPANCY_QUERY
        command = self.command_for(invocation)
        cancel_path = self._cancel_path_for(job_id)
        self._cancel_paths[job_id] = cancel_path
        env = _door_env(
            invocation,
            receipt_path=self.receipt_path,
            cancel_path=cancel_path,
            ledger_path=self.ledger_path,
            hang=self.hang and not is_query,
        )
        if not is_query:
            checked = self.preflight(invocation)
            if is_refusal(checked):
                return checked
            if checked.value is not None:
                selected = checked.value
                self._preflight_by_job[job_id] = selected
                payload = {
                    **payload,
                    "mints_ct32": selected["mints_ct32"],
                    "operator_descriptor_fp1": selected["operator_descriptor_fp1"],
                }
                invocation = replace(invocation, payload=payload)
                env = _door_env(
                    invocation,
                    receipt_path=self.receipt_path,
                    cancel_path=cancel_path,
                    ledger_path=self.ledger_path,
                    hang=self.hang,
                )
        stdout = subprocess.PIPE
        try:
            proc: subprocess.Popen[bytes] | subprocess.Popen[str]
            if sys.platform == "win32" and is_query:
                proc = subprocess.Popen(
                    list(command),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            elif sys.platform == "win32":
                proc = subprocess.Popen(
                    list(command),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            elif is_query:
                proc = subprocess.Popen(
                    list(command),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    start_new_session=True,
                    close_fds=True,
                )
            else:
                proc = subprocess.Popen(
                    list(command),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                )
        except OSError as exc:
            return policy_rejection(
                "qmb_cli",
                "could not spawn the qmb CLI process; the door is a runtime "
                "interaction, not an import (CT-47; DEC-0276)",
                program=command[0],
                argv=list(command[1:]),
                error=str(exc),
            )
        captured = ""
        if is_query:
            try:
                out, _err = proc.communicate(timeout=self.query_timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=self.query_timeout)
                return policy_rejection(
                    "qmb_cli",
                    "qmb query CLI timed out; queries wait and persist refs (FR-W11; FR-W24)",
                    job_id=job_id,
                    occupancy=QMB_OCCUPANCY_QUERY,
                )
            captured = out if isinstance(out, str) else (out.decode("utf-8") if out else "")
            self._stdout_by_job[job_id] = captured
        pid = int(proc.pid)
        self._processes[job_id] = proc
        self._invocations_by_job[job_id] = invocation
        self._spawned.append(
            SpawnedQmbProcess(
                job_id=job_id,
                pid=pid,
                argv=tuple(invocation.argv),
                command=command,
            )
        )
        return Ok(
            QmbDoorReceipt(
                job_id=job_id,
                environment_ref=environment_ref,
                occupancy_key=occupancy_key,
                door=invocation.kind,
                program=invocation.program,
                argv=invocation.argv,
                world=QMB_WORLD_REPLAY,
                route=QMB_ROUTE,
                import_edge=False,
                occupancy=classified.occupancy,
                mints_ct32=(
                    cast(bool, payload["mints_ct32"])
                    if type(payload.get("mints_ct32")) is bool
                    else classified.mints_ct32
                ),
                mints_experiment_spec=False,
                stdout=captured,
            )
        )

    def wait(self, job_id: str, *, timeout: float = 10.0) -> int | None:
        """Wait for a spawned ``qmb`` process and retain its bounded result stream."""
        with self._wait_lock:
            proc = self._processes.get(job_id)
            if proc is None:
                return None
            if job_id in self._stdout_by_job and proc.returncode is not None:
                return int(proc.returncode)
            out, _err = proc.communicate(timeout=timeout)
            self._stdout_by_job[job_id] = (
                out if isinstance(out, str) else (out.decode("utf-8") if out else "")
            )
            return int(proc.returncode) if proc.returncode is not None else None

    def terminal_result(self, job_id: str) -> Result[Mapping[str, object]]:
        """Read a QMB result only after a second CLI reopens its durable record."""
        verified = self._verified_stdout_by_job.get(job_id)
        if verified is not None:
            return _decode_terminal_result(verified)
        raw = self._stdout_by_job.get(job_id)
        if not isinstance(raw, str) or not raw.strip():
            return invalid_input(
                "qmb_terminal_result",
                "successful process completion requires a QMB durable-result response",
                job_id=job_id,
            )
        try:
            value = json.loads(raw, object_pairs_hook=_unique_json_object)
        except ValueError, TypeError:
            return invalid_input("qmb_terminal_result", "QMB terminal response is strict JSON")
        if not isinstance(value, Mapping):
            return invalid_input("qmb_terminal_result", "QMB terminal response is an object")
        result: dict[str, object] = dict(cast(Mapping[str, object], value))
        book_required = {
            "class",
            "ct32_fp1",
            "evidence_ref",
            "run_fp1",
            "job_id",
            "attempt_id",
            "experiment_spec_fp1",
            "split_manifest_fp1",
            "operator_descriptor_fp1",
            "terminal_line_fp1",
        }
        alternative_required = {
            "class",
            "format_version",
            "job_id",
            "attempt_id",
            "experiment_spec_fp1",
            "evidence_ref",
            "split_manifest_fp1",
            "operator_binding_fp1",
            "operator_binding",
            "composition_class",
            "composition_fp1",
            "policy_pair_identity",
            "source_fp1",
            "split_fp1",
            "split_role",
            "registry_fp1",
            "interpreter_registration_fp1",
            "run_receipt_fp1",
            "terminal_artifact_fp1",
            "journal_writer",
            "journal_stream",
            "journal_refs",
            "final_measures",
            "final_accounting_state_fp1",
        }
        study_required = {
            "class",
            "format_version",
            "study_fp1",
            "operational_fp1",
            "generation_run",
            "terminal_artifact_fp1s",
            "occurrence_event_fp1",
        }
        result_class = result.get("class")
        required = (
            alternative_required
            if result_class == "qmb-alternative-result-v1"
            else study_required
            if result_class == "qmb-operator-alternative-study-result-v1"
            else book_required
        )
        if set(result) != required or result_class not in {
            "qmb-recorded-replay-result-v1",
            "qmb-alternative-result-v1",
            "qmb-operator-alternative-study-result-v1",
        }:
            return invalid_input(
                "qmb_terminal_result",
                "QMB result has the exact durable result schema for its composition",
                missing=sorted(required.difference(result)),
                extra=sorted(set(result).difference(required)),
            )
        if result_class == "qmb-alternative-result-v1" and (
            type(result.get("format_version")) is not int
            or result.get("format_version") != 1
            or result.get("composition_class") != "alternative"
            or not isinstance(result.get("operator_binding"), Mapping)
            or not isinstance(result.get("journal_refs"), list)
            or not isinstance(result.get("final_measures"), list)
        ):
            return invalid_input("qmb_terminal_result", "ATC result has its exact typed shape")
        if result_class == "qmb-operator-alternative-study-result-v1":
            generation_run = result.get("generation_run")
            if (
                type(result.get("format_version")) is not int
                or result.get("format_version") != 1
                or not isinstance(generation_run, Mapping)
                or not isinstance(result.get("terminal_artifact_fp1s"), list)
            ):
                return invalid_input(
                    "qmb_terminal_result", "Study result has its exact typed history shape"
                )
            history = cast(Mapping[str, object], generation_run)
            if set(history) != {
                "class",
                "completed_generations",
                "generation_count",
                "study_fp",
                "writes_evidence",
            }:
                return invalid_input(
                    "generation_run", "Study history uses the exact generation-run identity"
                )
            generations = history.get("completed_generations")
            generation_total = history.get("generation_count")
            if (
                history.get("class") != "qmb-study-generation-run"
                or type(generation_total) is not int
                or not isinstance(generations, list)
                or history.get("writes_evidence") is not False
            ):
                return invalid_input(
                    "generation_run", "Study result contains a complete fixed generation history"
                )
            generation_list = cast(list[object], generations)
            if generation_total < 1 or len(generation_list) != generation_total:
                return invalid_input(
                    "generation_run", "Study result contains its complete generation count"
                )
            artifact_refs = cast(list[object], result["terminal_artifact_fp1s"])
            if not artifact_refs or any(
                not isinstance(item, str) or re.fullmatch(r"fp1:sha256:[0-9a-f]{64}", item) is None
                for item in artifact_refs
            ):
                return invalid_input(
                    "terminal_artifact_fp1s", "Study result lists canonical terminal artifacts"
                )
            for index, generation in enumerate(generation_list):
                if not isinstance(generation, list) or not generation:
                    return invalid_input(
                        "completed_generations",
                        "each completed generation has read-back trials",
                        generation=index,
                    )
                for ask, trial in enumerate(cast(list[object], generation)):
                    if not isinstance(trial, Mapping):
                        return invalid_input(
                            "completed_generations", "each read-back trial is an identity object"
                        )
                    trial_row = cast(Mapping[str, object], trial)
                    objective_den = trial_row.get("objective_den")
                    if (
                        set(trial_row)
                        != {
                            "class",
                            "generation_index",
                            "ask_index",
                            "parameters",
                            "objective_num",
                            "objective_den",
                        }
                        or trial_row.get("class") != "qmb-prior-trial"
                        or type(trial_row.get("generation_index")) is not int
                        or trial_row.get("generation_index") != index
                        or type(trial_row.get("ask_index")) is not int
                        or trial_row.get("ask_index") != ask
                        or not isinstance(trial_row.get("parameters"), Mapping)
                        or type(trial_row.get("objective_num")) is not int
                        or type(objective_den) is not int
                        or objective_den <= 0
                    ):
                        return invalid_input(
                            "completed_generations", "trial identity and order are canonical"
                        )
        fingerprint_fields = (
            (
                "operator_binding_fp1",
                "composition_fp1",
                "source_fp1",
                "split_fp1",
                "registry_fp1",
                "interpreter_registration_fp1",
                "run_receipt_fp1",
                "terminal_artifact_fp1",
                "final_accounting_state_fp1",
            )
            if result_class == "qmb-alternative-result-v1"
            else (
                "study_fp1",
                "operational_fp1",
                "occurrence_event_fp1",
                "terminal_artifact_fp1s",
            )
            if result_class == "qmb-operator-alternative-study-result-v1"
            else (
                "ct32_fp1",
                "run_fp1",
                "terminal_line_fp1",
                "operator_descriptor_fp1",
            )
        )
        for field_name in (
            "evidence_ref",
            "experiment_spec_fp1",
            "split_manifest_fp1",
            *fingerprint_fields,
        ):
            if field_name == "terminal_artifact_fp1s":
                continue
            field_value = result.get(field_name)
            if (
                not isinstance(field_value, str)
                or len(field_value) != 75
                or not field_value.startswith("fp1:sha256:")
                or any(char not in "0123456789abcdef" for char in field_value[11:])
            ):
                return invalid_input(field_name, "terminal result carries canonical fingerprints")
        if (
            isinstance(result.get("attempt_id"), bool)
            or not isinstance(result.get("attempt_id"), int)
            or cast(int, result.get("attempt_id")) < 1
            or not isinstance(result.get("job_id"), str)
            or not result["job_id"]
        ):
            return invalid_input("job_id", "terminal result binds a positive attempt and job")
        # The test double has no operator descriptor or domain store. Its
        # responses remain unit-test controls; production binaries always take
        # the read-only preflight path and must pass an independent reopen.
        if job_id not in self._preflight_by_job:
            return Ok(result)
        with self._verify_lock:
            verified = self._verified_stdout_by_job.get(job_id)
            if verified is None:
                verified_result = self._reopen_terminal_record(job_id, result)
                if is_refusal(verified_result):
                    return verified_result
                self._verified_stdout_by_job[job_id] = json.dumps(
                    dict(verified_result.value), separators=(",", ":")
                )
                verified = self._verified_stdout_by_job[job_id]
        return _decode_terminal_result(verified)

    def verify_persisted_result(
        self, job_id: str, invocation: QmbDoorInvocation
    ) -> Result[Mapping[str, object]]:
        """Run QMB verify-only from the durable expected invocation after restart."""
        return self._reopen_terminal_record(job_id, None, invocation=invocation)

    def _reopen_terminal_record(
        self,
        job_id: str,
        claimed: Mapping[str, object] | None,
        *,
        invocation: QmbDoorInvocation | None = None,
    ) -> Result[Mapping[str, object]]:
        invocation = invocation or self._invocations_by_job.get(job_id)
        if invocation is None:
            return invalid_input(
                "qmb_terminal_result", "terminal verification retains the exact invocation"
            )
        env = _door_env(
            invocation,
            receipt_path=self.receipt_path,
            cancel_path=self._cancel_path_for(job_id),
            ledger_path=self.ledger_path,
            hang=False,
        )
        env["QMA_QMB_VERIFY"] = "1"
        if claimed is None:
            env["QMA_QMB_VERIFY_DURABLE"] = "1"
        command = self.command_for(invocation)
        try:
            with tempfile.TemporaryDirectory(prefix="qma-qmb-terminal-verify-") as raw:
                if claimed is not None:
                    claim_path = Path(raw) / "claimed-result.json"
                    claim_path.write_text(
                        json.dumps(dict(claimed), separators=(",", ":")), encoding="utf-8"
                    )
                    env["QMA_QMB_VERIFY_CLAIM_FILE"] = str(claim_path)
                completed = subprocess.run(
                    list(command),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=30.0,
                    check=False,
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return invalid_input(
                "qmb_terminal_result", "QMB durable verification completed", error=str(exc)
            )
        if completed.returncode != 0:
            return invalid_input(
                "qmb_terminal_result",
                "QMB verify-only invocation reopened the exact durable result",
                exit_code=completed.returncode,
            )
        parsed = _decode_terminal_result(completed.stdout)
        if is_refusal(parsed):
            return parsed
        if claimed is not None and dict(parsed.value) != dict(claimed):
            return policy_rejection(
                "qmb_terminal_result", "reopened result equals the original child response"
            )
        return parsed

    def close(self, *, timeout: float = 5.0) -> None:
        """Reap spawned CLI processes. Does not write QMB or Experiment ledgers."""
        for job_id, proc in list(self._processes.items()):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=timeout)
            self._processes.pop(job_id, None)
