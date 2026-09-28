"""Story 67.4 — C1 recover-control; SCN-0030 positives and negatives."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import cast

from qma.daemon.host_control import (
    HOST_CONTROL_BIND_NAME,
    HOST_CONTROL_FILE,
    LOCAL_OPERATOR_PRINCIPAL_ID,
    LOCAL_OPERATOR_RECOVERED_EVENT,
    RECOVER_CONTROL_EXISTED_AT_INSPECT_SHA,
    caller_owns_daemon_root,
    claim_recover_control_existed_at_inspect_sha,
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
from qma.daemon.process import (
    DAEMON_RECOVER_FLAG,
    DaemonProcess,
    run_recover_entry,
    supervised_recover_argv,
)
from qma.wire import HUMAN_GATE_COMMANDS
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import RefusalCategory


def _seed_configs(tmp_path: Path) -> dict[str, dict[str, object]]:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    return research_corpus_plugin_load_config(seed)


def _compose(tmp_path: Path, *, boot: str = "boot-67-4", bootstrap: bool = True) -> DaemonProcess:
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id=boot,
        bind_port=0,
        plugin_load_configs=_seed_configs(tmp_path),
        bootstrap=bootstrap,
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


def _bootstrap_and_stop(tmp_path: Path, *, boot: str) -> tuple[str, str, list[object]]:
    process = _compose(tmp_path, boot=boot)
    try:
        token = read_host_control_token(tmp_path)
        assert is_ok(token)
        live = load_local_operator(process.sqlite)
        assert live is not None
        rows = process.journal.read_all()
        assert is_ok(rows)
        prior = list(rows.value)
        fp1 = live.host_control_fp1
        old_token = token.value
    finally:
        process.close()
    (tmp_path / HOST_CONTROL_FILE).unlink()
    bind = tmp_path / HOST_CONTROL_BIND_NAME
    if bind.is_file():
        bind.unlink()
    return old_token, fp1, prior


def test_t_h_02_recover_control_one_shot_does_not_bind(tmp_path: Path) -> None:
    old_token, old_fp1, prior = _bootstrap_and_stop(tmp_path, boot="boot-67-4-a")
    recovered = run_recover_entry(
        tmp_path,
        machine="test-host",
        boot_epoch_id="boot-67-4-recover",
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_ok(recovered), recovered
    payload = dict(recovered.value)
    assert payload["recovered"] is True
    assert payload["local_operator"] == "unchanged"
    assert payload["bound_8765"] is False
    assert payload["writer"] == "host.recover-control"
    dumped = json.dumps(payload)
    assert old_token not in dumped
    new = read_host_control_token(tmp_path)
    assert is_ok(new)
    new_token = new.value
    assert new_token != old_token
    assert new_token not in dumped
    assert not (tmp_path / HOST_CONTROL_BIND_NAME).exists()
    assert caller_owns_daemon_root(tmp_path) is True

    started = _compose(tmp_path, boot="boot-67-4-start")
    try:
        live = load_local_operator(started.sqlite)
        assert live is not None
        assert live.principal_id == LOCAL_OPERATOR_PRINCIPAL_ID
        assert live.host_control_fp1 == host_control_fp1(new_token)
        assert live.host_control_fp1 != old_fp1
        assert principal_count(started.sqlite) == 1
        rows = started.journal.read_all()
        assert is_ok(rows)
        assert list(rows.value[: len(prior)]) == prior
        recovered_rows = [
            row for row in rows.value if row["event"] == LOCAL_OPERATOR_RECOVERED_EVENT
        ]
        assert recovered_rows
        rec_payload = recovered_rows[-1]["payload"]
        assert isinstance(rec_payload, dict)
        assert rec_payload["principal_id"] == LOCAL_OPERATOR_PRINCIPAL_ID
        assert rec_payload["host_control_fp1"] == live.host_control_fp1
        assert rec_payload["previous_host_control_fp1"] == old_fp1
        assert "superseded_by" not in rec_payload
        journal_dump = json.dumps(dict(recovered_rows[-1]))
        assert old_token not in journal_dump
        assert new_token not in journal_dump
        folded = fold_local_operator_from_journal(started.journal)
        assert folded is not None
        assert folded.host_control_fp1 == live.host_control_fp1
        assert started.local_operator is not None
        assert started.local_operator.minted is False
        assert started.bound is None
        assert started.host_control is None
    finally:
        started.close()


def test_recover_control_negative_a_other_os_user(tmp_path: Path) -> None:
    old_token, old_fp1, prior = _bootstrap_and_stop(tmp_path, boot="boot-67-4-neg-a")
    refused = run_recover_entry(
        tmp_path,
        machine="test-host",
        boot_epoch_id="boot-67-4-stranger",
        plugin_load_configs=_seed_configs(tmp_path),
        owns_root=False,
    )
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "QMA_DAEMON_ROOT"
    assert not (tmp_path / HOST_CONTROL_FILE).exists()
    check = _compose(tmp_path, boot="boot-67-4-neg-a-check")
    try:
        live = load_local_operator(check.sqlite)
        assert live is not None
        assert live.host_control_fp1 == old_fp1
        assert principal_count(check.sqlite) == 1
        rows = check.journal.read_all()
        assert is_ok(rows)
        assert list(rows.value) == prior
        _ = old_token
    finally:
        check.close()


def test_recover_control_negative_b_file_still_readable(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-67-4-neg-b")
    process.close()
    held = read_host_control_token(tmp_path)
    assert is_ok(held)
    live_before = None
    check = _compose(tmp_path, boot="boot-67-4-neg-b-hold")
    try:
        live_before = load_local_operator(check.sqlite)
        assert live_before is not None
        fp1 = live_before.host_control_fp1
    finally:
        check.close()
    refused = run_recover_entry(
        tmp_path,
        machine="test-host",
        boot_epoch_id="boot-67-4-readable",
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "recover-control"
    still = read_host_control_token(tmp_path)
    assert is_ok(still)
    assert still.value == held.value
    after = _compose(tmp_path, boot="boot-67-4-neg-b-after")
    try:
        live = load_local_operator(after.sqlite)
        assert live is not None
        assert live.host_control_fp1 == fp1
        assert principal_count(after.sqlite) == 1
    finally:
        after.close()


def test_recover_control_negative_c_live_daemon(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-67-4-neg-c")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            held = read_host_control_token(tmp_path)
            assert is_ok(held)
            (tmp_path / HOST_CONTROL_FILE).unlink()
            refused = process.recover_control()
            assert is_refusal(refused)
            assert refused.context["field"] == "recover-control"
            assert "live" in str(refused.context.get("reason", ""))
            assert process.bound is not None
            assert process.host_control is not None
            live = load_local_operator(process.sqlite)
            assert live is not None
            assert principal_count(process.sqlite) == 1
            assert not (tmp_path / HOST_CONTROL_FILE).exists()
            presented = await asyncio.to_thread(
                _raw_call,
                tmp_path,
                "recover-control",
                held.value,
            )
            assert presented["ok"] is False
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def test_recover_then_start_old_fingerprint_dead(tmp_path: Path) -> None:
    old_token, old_fp1, _prior = _bootstrap_and_stop(tmp_path, boot="boot-67-4-dead")
    recovered = run_recover_entry(
        tmp_path,
        machine="test-host",
        boot_epoch_id="boot-67-4-dead-recover",
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_ok(recovered), recovered
    assert recovered.value["previous_host_control_fp1"] == old_fp1

    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-67-4-dead-start")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            stale = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "status",
                token=old_token,
            )
            assert is_ok(stale)
            assert stale.value["ok"] is False
            status = await asyncio.to_thread(host_control_call, tmp_path, "status")
            assert is_ok(status)
            assert status.value["ok"] is True
            live = load_local_operator(process.sqlite)
            assert live is not None
            assert live.host_control_fp1 != old_fp1
            assert principal_count(process.sqlite) == 1
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def test_recover_does_not_remint_principal_or_bind_ct40(tmp_path: Path) -> None:
    _old_token, old_fp1, _prior = _bootstrap_and_stop(tmp_path, boot="boot-67-4-noremint")
    process = _compose(tmp_path, boot="boot-67-4-noremint-run", bootstrap=False)
    try:
        assert process.bound is None
        assert process.host_control is None
        recovered = process.recover_control()
        assert is_ok(recovered), recovered
        assert recovered.value["bound_8765"] is False
        assert process.bound is None
        assert process.host_control is None
        live = load_local_operator(process.sqlite)
        assert live is not None
        assert live.principal_id == LOCAL_OPERATOR_PRINCIPAL_ID
        assert live.host_control_fp1 != old_fp1
        assert process.local_operator is not None
        assert process.local_operator.minted is False
        assert principal_count(process.sqlite) == 1
        source = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "process.py"
        text = source.read_text(encoding="utf-8")
        assert "POST /host/" not in text
        main_src = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "__main__.py"
        main_text = main_src.read_text(encoding="utf-8")
        assert "process.serve()" in main_text
        assert "run_recover_entry" in main_text
    finally:
        process.close()


def test_honesty_recover_control_absent_at_inspect() -> None:
    assert RECOVER_CONTROL_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_recover_control_existed_at_inspect_sha(True))
    assert is_ok(claim_recover_control_existed_at_inspect_sha(False))
    assert "recover-control" not in HUMAN_GATE_COMMANDS
    assert "host.recover-control" not in HUMAN_GATE_COMMANDS
    argv = supervised_recover_argv("python")
    assert argv[-1] == DAEMON_RECOVER_FLAG
    assert argv[-3:-1] == ("-m", "qma.daemon")
