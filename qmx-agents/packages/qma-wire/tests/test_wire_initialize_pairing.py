"""Story 68.6 — initialize advertises pairing; browser session has no credential_ref."""

from __future__ import annotations

from pathlib import Path

from qma.core.plugins.credential import parse_credential_ref
from qma.wire import (
    CONNECT_TYPES_EXISTED_AT_INSPECT_SHA,
    DEFERRED_INITIALIZE_CAPABILITIES,
    LIST_MAILBOX_CAPABILITY_MINTED,
    PAIRING_CAPABILITY,
    PAIRING_INSPECT_SHA,
    PAIRING_RECORD_ID_PREFIX,
    WIRE_PROTOCOL_VERSION,
    GrantRecord,
    LiveProducerRegistry,
    WireConnection,
    WireEnvelope,
    advertise_pairing_capabilities,
    authenticate_pairing_record,
    claim_connect_types_absent_at_inspect_sha,
    claim_deferred_initialize_capabilities_minted,
    evaluate_pairing_capability,
    mint_tab_producer_id,
    negotiate_initialize,
    refuse_page_machine_principal,
    refuse_shared_live_producer_id,
)
from qma.wire.initialize import InitializeParams
from qmf.core.refusal import Ok, RefusalCategory, is_ok, is_refusal

_RECORD_ID = f"{PAIRING_RECORD_ID_PREFIX}{'ab' * 16}"
_INIT_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "wire" / "initialize.py"
_AUTH_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "wire" / "auth.py"


def test_initialize_advertises_pairing_and_strips_deferred() -> None:
    assert PAIRING_CAPABILITY == "pairing"
    assert LIST_MAILBOX_CAPABILITY_MINTED is False
    assert "list_mailbox" in DEFERRED_INITIALIZE_CAPABILITIES
    assert "cancel_job" in DEFERRED_INITIALIZE_CAPABILITIES
    assert "stage_artifact" in DEFERRED_INITIALIZE_CAPABILITIES
    assert "pack_ui_request" in DEFERRED_INITIALIZE_CAPABILITIES
    caps = advertise_pairing_capabilities(
        {"commands": True, "list_mailbox": True, "cancel_job": True}
    )
    assert caps[PAIRING_CAPABILITY] is True
    assert "list_mailbox" not in caps
    assert "cancel_job" not in caps

    params = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        capabilities={"commands": True},
        client_producer_id="tab:one",
    )
    assert isinstance(params, Ok)
    negotiated = negotiate_initialize(params.value, assign_producer_id="tab:one")
    assert isinstance(negotiated, Ok)
    assert negotiated.value.capabilities[PAIRING_CAPABILITY] is True
    for name in DEFERRED_INITIALIZE_CAPABILITIES:
        assert name not in negotiated.value.capabilities


def test_missing_pairing_is_typed_mismatch_shell_usable() -> None:
    refused = evaluate_pairing_capability({})
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["missing"] == PAIRING_CAPABILITY
    assert refused.context["shell_usable"] is True

    present = evaluate_pairing_capability({PAIRING_CAPABILITY: True})
    assert is_ok(present)

    conn = WireConnection()
    authed = conn.authenticate_pairing(_RECORD_ID)
    assert isinstance(authed, Ok)
    params = InitializeParams.try_create(protocol_version=WIRE_PROTOCOL_VERSION)
    assert isinstance(params, Ok)
    finished = conn.complete_initialize(
        params.value,
        assign_producer_id="tab:mismatch",
        advertise_pairing=False,
        server_capabilities={"commands": True},
    )
    assert isinstance(finished, Ok)
    assert conn.initialized is True
    assert conn.capability_mismatch is not None
    assert conn.capability_mismatch["shell_usable"] is True
    accepted = conn.accept_family_message("start_mission")
    assert isinstance(accepted, Ok)


def test_deferred_capability_mint_claim_fails() -> None:
    assert is_refusal(claim_deferred_initialize_capabilities_minted(True))
    assert is_ok(claim_deferred_initialize_capabilities_minted(False))


def test_browser_paired_session_has_no_credential_ref() -> None:
    conn = WireConnection()
    authed = conn.authenticate_pairing(_RECORD_ID)
    assert isinstance(authed, Ok)
    assert conn.authenticated is True
    assert conn.pairing_record_id == _RECORD_ID
    assert conn.credential_ref is None
    assert conn.principal_class is not None
    assert conn.principal_class.value == "operator"

    session = authenticate_pairing_record(_RECORD_ID)
    assert is_ok(session)
    assert session.value.credential_ref is None
    assert session.value.pairing_record_id == _RECORD_ID
    assert session.value.principal_class.value == "operator"

    cred_bind = conn.authenticate("cred://models/openai", principal_class="operator")
    assert is_refusal(cred_bind)
    assert "does not populate credential_ref" in str(cred_bind.context["reason"])

    init_text = _INIT_SRC.read_text(encoding="utf-8")
    auth_text = _AUTH_SRC.read_text(encoding="utf-8")
    pairing_fn = init_text.split("def authenticate_pairing(")[1].split("def authorize_command(")[0]
    record_fn = auth_text.split("def authenticate_pairing_record(")[1].split(
        "def assert_no_secret_on_wire_surface("
    )[0]
    assert "parse_credential_ref(" not in pairing_fn
    assert "parse_credential_ref(" not in record_fn
    # parse_credential_ref would accept a proof-like string; pairing must not call it.
    parsed = parse_credential_ref("abcDEF012-_~")
    assert str(parsed) == "abcDEF012-_~"


def test_page_machine_principal_is_policy_rejection() -> None:
    refused = refuse_page_machine_principal("machine")
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    conn = WireConnection()
    page = conn.authenticate_pairing(_RECORD_ID, principal_class="machine")
    assert is_refusal(page)
    assert page.context["field"] == "principal_class"
    operator = refuse_page_machine_principal("operator")
    assert is_ok(operator)


def test_live_producer_registry_reload_reuses_clone_mints() -> None:
    registry = LiveProducerRegistry()
    first = registry.assign("tab:shared", connection_token="conn-a")
    assert first == "tab:shared"
    assert registry.is_live("tab:shared") is True
    shared = refuse_shared_live_producer_id(
        "tab:shared",
        live_producers=registry,
        connection_token="conn-b",
    )
    assert is_refusal(shared)
    assert "sharing a live producer_id" in str(shared.context["reason"])

    clone = registry.assign("tab:shared", connection_token="conn-b")
    assert clone != "tab:shared"
    assert clone.startswith("tab:")
    assert registry.owner("tab:shared") == "conn-a"
    assert registry.owner(clone) == "conn-b"

    registry.release("tab:shared", connection_token="conn-a")
    reload_id = registry.assign("tab:shared", connection_token="conn-reload")
    assert reload_id == "tab:shared"

    minted = mint_tab_producer_id()
    assert minted.startswith("tab:")
    assert minted != mint_tab_producer_id()


def test_complete_initialize_clone_does_not_share_live_producer() -> None:
    registry = LiveProducerRegistry()
    original = WireConnection()
    assert isinstance(original.authenticate_pairing(_RECORD_ID), Ok)
    params = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        client_producer_id="tab:copied",
    )
    assert isinstance(params, Ok)
    first = original.complete_initialize(
        params.value,
        live_producers=registry,
        connection_token="conn-a",
    )
    assert isinstance(first, Ok)
    assert original.producer_id == "tab:copied"
    assert original.capabilities[PAIRING_CAPABILITY] is True

    clone = WireConnection()
    assert isinstance(clone.authenticate_pairing(_RECORD_ID), Ok)
    second = clone.complete_initialize(
        params.value,
        live_producers=registry,
        connection_token="conn-b",
    )
    assert isinstance(second, Ok)
    assert clone.producer_id != original.producer_id
    assert clone.initialized is True


def test_connect_types_existed_at_inspect_sha() -> None:
    assert CONNECT_TYPES_EXISTED_AT_INSPECT_SHA is True
    assert PAIRING_INSPECT_SHA == "34c148be"
    assert is_refusal(claim_connect_types_absent_at_inspect_sha(True))
    assert is_ok(claim_connect_types_absent_at_inspect_sha(False))
    assert WireEnvelope.__name__ == "WireEnvelope"
    assert GrantRecord.__name__ == "GrantRecord"
