"""Story 67.3 — T-H-01 rotate-while-held; running-daemon verbs need current token."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import cast

from qma.daemon.host_control import (
    HOST_CONTROL_FILE,
    LOCAL_OPERATOR_PRINCIPAL_ID,
    LOCAL_OPERATOR_ROTATED_EVENT,
    ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA,
    claim_rotate_control_existed_at_inspect_sha,
    encode_host_control_frame,
    host_control_call,
    host_control_fp1,
    load_local_operator,
    principal_count,
    read_host_control_bind,
    read_host_control_token,
)
from qma.daemon.host_control.local_operator import fold_local_operator_from_journal
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire import HUMAN_GATE_COMMANDS
from qmf.core import is_ok, is_refusal

_FIXTURE_TTL = "PT15M"


def _seed_configs(tmp_path: Path) -> dict[str, dict[str, object]]:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    return research_corpus_plugin_load_config(seed)


def _compose(tmp_path: Path, *, boot: str = "boot-67-3") -> DaemonProcess:
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id=boot,
        bind_port=0,
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_ok(result), result
    return result.value


def _raw_call(root: Path, verb: str, token: str, **fields: object) -> dict[str, object]:
    bound = read_host_control_bind(root)
    assert is_ok(bound)
    host, port = bound.value
    request: dict[str, object] = {"verb": verb, "host_control": token}
    request.update(fields)
    import socket

    with socket.create_connection((host, port), timeout=2.0) as sock:
        sock.sendall(encode_host_control_frame(request))
        header = sock.recv(4)
        size = int.from_bytes(header, "big")
        body = sock.recv(size)
    parsed: object = json.loads(body.decode("utf-8"))
    assert isinstance(parsed, dict)
    return cast("dict[str, object]", parsed)


def test_t_h_01_rotate_while_held(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path)
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            old = read_host_control_token(tmp_path)
            assert is_ok(old)
            old_token = old.value
            live_before = load_local_operator(process.sqlite)
            assert live_before is not None
            old_fp1 = live_before.host_control_fp1
            rows_before = process.journal.read_all()
            assert is_ok(rows_before)
            prior = list(rows_before.value)

            rotated = await asyncio.to_thread(host_control_call, tmp_path, "rotate-control")
            assert is_ok(rotated), rotated
            payload = rotated.value
            assert payload["ok"] is True
            body = payload["rotated"]
            assert isinstance(body, dict)
            fields = cast("dict[str, object]", body)
            assert fields["rotated"] is True
            assert fields["local_operator"] == "unchanged"
            dumped = json.dumps(dict(payload))
            assert old_token not in dumped

            new = read_host_control_token(tmp_path)
            assert is_ok(new)
            new_token = new.value
            assert new_token != old_token
            assert new_token not in dumped
            live_after = load_local_operator(process.sqlite)
            assert live_after is not None
            assert live_after.principal_id == LOCAL_OPERATOR_PRINCIPAL_ID
            assert live_after.principal_id == live_before.principal_id
            assert live_after.principal_class == live_before.principal_class
            assert live_after.host_control_fp1 != old_fp1
            assert live_after.host_control_fp1 == host_control_fp1(new_token)
            assert principal_count(process.sqlite) == 1
            assert process.local_operator is not None
            assert process.local_operator.host_control_fp1 == live_after.host_control_fp1

            rows_after = process.journal.read_all()
            assert is_ok(rows_after)
            assert list(rows_after.value[: len(prior)]) == prior
            rotated_rows = [
                row for row in rows_after.value if row["event"] == LOCAL_OPERATOR_ROTATED_EVENT
            ]
            assert rotated_rows
            rot_payload = rotated_rows[-1]["payload"]
            assert isinstance(rot_payload, dict)
            assert rot_payload["principal_id"] == LOCAL_OPERATOR_PRINCIPAL_ID
            assert rot_payload["host_control_fp1"] == live_after.host_control_fp1
            assert rot_payload["previous_host_control_fp1"] == old_fp1
            assert "superseded_by" not in rot_payload
            journal_dump = json.dumps(dict(rotated_rows[-1]))
            assert old_token not in journal_dump
            assert new_token not in journal_dump

            folded = fold_local_operator_from_journal(process.journal)
            assert folded is not None
            assert folded.principal_id == LOCAL_OPERATOR_PRINCIPAL_ID
            assert folded.host_control_fp1 == live_after.host_control_fp1

            stale = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "status",
                token=old_token,
            )
            assert is_ok(stale)
            stale_payload = stale.value
            assert stale_payload["ok"] is False

            status = await asyncio.to_thread(host_control_call, tmp_path, "status")
            assert is_ok(status)
            status_dump = json.dumps(dict(status.value))
            assert new_token not in status_dump
            assert old_token not in status_dump
            snapshot = status.value["status"]
            assert isinstance(snapshot, dict)
            assert snapshot["operator_established"] is True
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def test_rotate_control_does_not_recover_a_lost_file(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-67-3-lost")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            old = read_host_control_token(tmp_path)
            assert is_ok(old)
            live_before = load_local_operator(process.sqlite)
            assert live_before is not None
            fp1 = live_before.host_control_fp1
            (tmp_path / HOST_CONTROL_FILE).unlink()
            missing = await asyncio.to_thread(host_control_call, tmp_path, "rotate-control")
            assert is_refusal(missing)
            presented = await asyncio.to_thread(
                _raw_call,
                tmp_path,
                "rotate-control",
                old.value,
            )
            assert presented["ok"] is False
            assert not (tmp_path / HOST_CONTROL_FILE).exists()
            live_after = load_local_operator(process.sqlite)
            assert live_after is not None
            assert live_after.host_control_fp1 == fp1
            assert principal_count(process.sqlite) == 1
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def test_running_daemon_verbs_require_current_token(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-67-3-gate")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            current = read_host_control_token(tmp_path)
            assert is_ok(current)
            verbs: tuple[tuple[str, dict[str, object]], ...] = (
                ("status", {}),
                ("stop", {}),
                ("configure", {"target": "pairing-ttl", "duration": _FIXTURE_TTL}),
                ("rotate-control", {}),
            )
            for verb, fields in verbs:
                missing = await asyncio.to_thread(
                    _raw_call,
                    tmp_path,
                    verb,
                    "",
                    **fields,
                )
                assert missing["ok"] is False
                stale = await asyncio.to_thread(
                    _raw_call,
                    tmp_path,
                    verb,
                    "stale-token",
                    **fields,
                )
                assert stale["ok"] is False
            still = read_host_control_token(tmp_path)
            assert is_ok(still)
            assert still.value == current.value
            live = load_local_operator(process.sqlite)
            assert live is not None
            assert live.host_control_fp1 == host_control_fp1(current.value)
            assert process.is_closed is False
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def test_honesty_rotate_control_absent_at_inspect() -> None:
    assert ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_rotate_control_existed_at_inspect_sha(True))
    assert is_ok(claim_rotate_control_existed_at_inspect_sha(False))
    assert "rotate-control" not in HUMAN_GATE_COMMANDS
    assert "host.rotate-control" not in HUMAN_GATE_COMMANDS
    process_src = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "process.py"
    assert "POST /host/" not in process_src.read_text(encoding="utf-8")
