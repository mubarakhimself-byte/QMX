"""Story 67.2 — first operator mint, sole TTL writer, missing-TTL refuse."""

from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path
from typing import cast

from qma.core.refusals.variants import CredentialOutOfScope
from qma.daemon.host_control import (
    DEC_0429_SUPERSEDED_BY,
    DEC_0440_SUPERSEDED_BY,
    HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA,
    HOST_CONTROL_FILE,
    LOCAL_OPERATOR_ESTABLISHED_EVENT,
    LOCAL_OPERATOR_EXISTED_AT_INSPECT_SHA,
    LOCAL_OPERATOR_FOLD_ID,
    LOCAL_OPERATOR_NEW_SQLITE_CLASS,
    LOCAL_OPERATOR_PRINCIPAL_ID,
    LOCAL_OPERATOR_STORE,
    LOCAL_OPERATOR_STORE_CLASS,
    LOCAL_OPERATOR_TABLE,
    claim_host_configure_existed_at_inspect_sha,
    claim_local_operator_existed_at_inspect_sha,
    encode_host_control_frame,
    host_control_call,
    load_local_operator,
    principal_count,
    read_host_control_bind,
    read_host_control_token,
)
from qma.daemon.journal import (
    CLOSED_PROJECTIONS,
    DEFINITION_STORE_MEMBERS,
    PAIRING_SESSION_TTL_KEY,
    PAIRING_SESSION_TTL_REGISTRY_KEY,
    PAIRING_TTL_CONFIGURED_EVENT,
    VARIABLE_SET_EVENT,
    GovernedVariableRegistry,
    claim_pairing_ttl_ct40_writable_at_inspect_sha,
    v1_fold_contract,
)
from qma.daemon.journal.stores import StoreClass
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import RefusalCategory

_FIXTURE_TTL = "PT15M"


def _forged_status(root: Path) -> dict[str, object]:
    bound = read_host_control_bind(root)
    assert is_ok(bound)
    host, port = bound.value
    request = {
        "verb": "status",
        "host_control": "cred://models/openai",
        "credential_ref": "cred://telemetry/export",
    }
    with socket.create_connection((host, port), timeout=2.0) as sock:
        sock.sendall(encode_host_control_frame(request))
        header = sock.recv(4)
        size = int.from_bytes(header, "big")
        body = sock.recv(size)
    parsed: object = json.loads(body.decode("utf-8"))
    assert isinstance(parsed, dict)
    return cast("dict[str, object]", parsed)


def _seed_configs(tmp_path: Path) -> dict[str, dict[str, object]]:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    return research_corpus_plugin_load_config(seed)


def _compose(tmp_path: Path, *, boot: str = "boot-67-2") -> DaemonProcess:
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id=boot,
        bind_port=0,
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_ok(result), result
    return result.value


def test_empty_root_mints_local_operator_and_host_control(tmp_path: Path) -> None:
    process = _compose(tmp_path)
    try:
        live = load_local_operator(process.sqlite)
        assert live is not None
        assert live.principal_id == LOCAL_OPERATOR_PRINCIPAL_ID
        assert live.principal_class == "operator"
        assert live.host_control_fp1.startswith("fp1:sha256:")
        assert process.local_operator is not None
        assert process.local_operator.minted is True
        assert principal_count(process.sqlite) == 1
        token = read_host_control_token(tmp_path)
        assert is_ok(token)
        assert (tmp_path / HOST_CONTROL_FILE).is_file()
        rows = process.journal.read_all()
        assert is_ok(rows)
        events = [row["event"] for row in rows.value]
        assert LOCAL_OPERATOR_ESTABLISHED_EVENT in events
        established = next(
            row for row in rows.value if row["event"] == LOCAL_OPERATOR_ESTABLISHED_EVENT
        )
        payload = established["payload"]
        assert isinstance(payload, dict)
        assert "superseded_by" not in payload
        assert payload["host_control_fp1"] == live.host_control_fp1
        assert token.value not in json.dumps(dict(established))
        snapshot = process.host_status_snapshot()
        assert snapshot["operator_established"] is True
        assert snapshot["ttl"] == "unset"
        assert LOCAL_OPERATOR_STORE in CLOSED_PROJECTIONS
        assert LOCAL_OPERATOR_STORE not in DEFINITION_STORE_MEMBERS
        assert len(DEFINITION_STORE_MEMBERS) == 16
        assert LOCAL_OPERATOR_NEW_SQLITE_CLASS is False
        assert StoreClass.JOURNAL_DERIVED_PROJECTION.value == LOCAL_OPERATOR_STORE_CLASS
        contract = v1_fold_contract(LOCAL_OPERATOR_FOLD_ID)
        assert contract is not None
        assert contract.source_stream == "local_operator.*"
        assert contract.ordering_key == "journal_seq"
        assert contract.knowledge_time_bound == "as_of_recorded_at"
        assert contract.equal_instant_disposition == "ascending_journal_seq"
        assert DEC_0429_SUPERSEDED_BY is None
        assert DEC_0440_SUPERSEDED_BY is None
        tables = process.sqlite_table_names()
        assert LOCAL_OPERATOR_TABLE in tables
    finally:
        process.close()


def test_missing_token_existing_principal_does_not_remint(tmp_path: Path) -> None:
    first = _compose(tmp_path, boot="boot-67-2-a")
    token = read_host_control_token(tmp_path)
    assert is_ok(token)
    live = load_local_operator(first.sqlite)
    assert live is not None
    principal_fp = live.host_control_fp1
    first.close()
    (tmp_path / HOST_CONTROL_FILE).unlink()
    second = _compose(tmp_path, boot="boot-67-2-b")
    try:
        again = load_local_operator(second.sqlite)
        assert again is not None
        assert again.principal_id == LOCAL_OPERATOR_PRINCIPAL_ID
        assert again.host_control_fp1 == principal_fp
        assert again.minted is False
        assert principal_count(second.sqlite) == 1
        assert not (tmp_path / HOST_CONTROL_FILE).exists()
        missing = read_host_control_token(tmp_path)
        assert is_refusal(missing)
    finally:
        second.close()


def test_configure_pairing_ttl_is_sole_writer_and_missing_ttl_refuses_issue(
    tmp_path: Path,
) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-67-2-ttl")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            missing = process.refuse_pair_issue()
            assert is_refusal(missing)
            assert missing.category is RefusalCategory.POLICY_REJECTION
            assert missing.context["ttl"] == "unset"

            other = process.variables.variable_set(
                "rlm.depth_cap",
                1,
                principal_class="operator",
                journal=process.journal,
            )
            assert is_ok(other), other

            ct40 = process.variables.variable_set(
                PAIRING_SESSION_TTL_REGISTRY_KEY,
                _FIXTURE_TTL,
                principal_class="operator",
                journal=process.journal,
            )
            assert is_refusal(ct40)
            assert "pairing.session_ttl" in str(ct40.context.get("reason", ""))
            machine = process.variables.variable_set(
                PAIRING_SESSION_TTL_KEY,
                _FIXTURE_TTL,
                principal_class="machine",
                journal=process.journal,
            )
            assert is_refusal(machine)

            written = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "configure",
                fields={"target": "pairing-ttl", "duration": _FIXTURE_TTL},
            )
            assert is_ok(written), written
            payload = written.value
            assert payload["ok"] is True
            configured = payload["configured"]
            assert isinstance(configured, dict)
            assert configured["registry_key"] == PAIRING_SESSION_TTL_REGISTRY_KEY
            assert configured["ttl"] == "set"
            assert process.host_status_snapshot()["ttl"] == "set"
            assert is_ok(process.refuse_pair_issue())

            rows = process.journal.read_all()
            assert is_ok(rows)
            ttl_events = [row for row in rows.value if row["event"] == PAIRING_TTL_CONFIGURED_EVENT]
            assert ttl_events
            ttl_payload = ttl_events[-1]["payload"]
            assert isinstance(ttl_payload, dict)
            assert ttl_payload["duration"] == _FIXTURE_TTL
            assert ttl_payload["writer"] == "host.configure.pairing-ttl"

            paired = await asyncio.to_thread(host_control_call, tmp_path, "pair")
            assert is_ok(paired)
            pair_payload = paired.value
            assert pair_payload["ok"] is False
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def test_forged_credential_ref_is_out_of_scope(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-67-2-cred")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            parsed = await asyncio.to_thread(_forged_status, tmp_path)
            assert parsed["ok"] is False
            refusal = parsed["refusal"]
            assert isinstance(refusal, dict)
            body = cast("dict[str, object]", refusal)
            context_raw: object = body["context"]
            assert isinstance(context_raw, dict)
            context = cast("dict[str, object]", context_raw)
            assert context["variant"] == CredentialOutOfScope.VARIANT
            assert str(context["credential_ref"]).startswith("cred://")
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_host_control_verbs_refuse_when_token_missing(tmp_path: Path) -> None:
    async def _run() -> None:
        first = _compose(tmp_path, boot="boot-67-2-miss-a")
        first.close()
        (tmp_path / HOST_CONTROL_FILE).unlink()
        process = _compose(tmp_path, boot="boot-67-2-miss-b")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            assert process.host_control is not None
            assert process.host_control.bound is not None
            missing = read_host_control_token(tmp_path)
            assert is_refusal(missing)
            status = await asyncio.to_thread(host_control_call, tmp_path, "status")
            assert is_refusal(status)
            live = load_local_operator(process.sqlite)
            assert live is not None
            assert process.local_operator is not None
            assert process.local_operator.minted is False
            assert principal_count(process.sqlite) == 1
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def test_honesty_local_operator_and_configure_absent_at_inspect() -> None:
    assert LOCAL_OPERATOR_EXISTED_AT_INSPECT_SHA is False
    assert HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_local_operator_existed_at_inspect_sha(True))
    assert is_ok(claim_local_operator_existed_at_inspect_sha(False))
    assert is_refusal(claim_host_configure_existed_at_inspect_sha(True))
    assert is_ok(claim_host_configure_existed_at_inspect_sha(False))
    assert is_refusal(claim_pairing_ttl_ct40_writable_at_inspect_sha(True))
    assert is_ok(claim_pairing_ttl_ct40_writable_at_inspect_sha(False))


def test_variable_registry_other_keys_keep_story_42_4(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-67-2-var")
    try:
        registry = GovernedVariableRegistry.with_builtins()
        row = registry.get(PAIRING_SESSION_TTL_KEY)
        assert is_ok(row)
        assert row.value.default is None
        refused = registry.variable_set(
            PAIRING_SESSION_TTL_KEY,
            _FIXTURE_TTL,
            principal_class="operator",
            journal=process.journal,
        )
        assert is_refusal(refused)
        allowed = registry.variable_set(
            "rlm.depth_cap",
            1,
            principal_class="operator",
            journal=process.journal,
        )
        assert is_ok(allowed)
        assert allowed.value.journal.record.event == VARIABLE_SET_EVENT
        variables = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "qma"
            / "daemon"
            / "journal"
            / "variables.py"
        )
        text = variables.read_text(encoding="utf-8")
        assert _FIXTURE_TTL not in text
        channel = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "qma"
            / "daemon"
            / "host_control"
            / "channel.py"
        )
        assert _FIXTURE_TTL not in channel.read_text(encoding="utf-8")
        process_src = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "process.py"
        process_text = process_src.read_text(encoding="utf-8")
        assert _FIXTURE_TTL not in process_text
        assert "POST /host/" not in process_text
    finally:
        process.close()
