"""Story 44.2 — OpenCodex local-proxy custody and Credential Broker egress."""

from __future__ import annotations

import pytest
from qma.core.barriers import (
    ALLOWED_CREDENTIAL_REF_PREFIXES,
    OUT_OF_SCOPE_CREDENTIAL_REF_PREFIXES,
    CredentialAllowlistError,
    assert_allowlist_not_widenable,
    is_credential_ref_allowed,
)
from qma.core.plugins import (
    assert_no_secret_in_hook_payloads,
    build_hook_result,
)
from qma.core.ports.model import (
    AUTH_MODE_NONE,
    OPENCODEX_ADAPTER,
    DeploymentRecord,
    is_local_proxy_deployment,
)
from qma.core.vocabulary.enums import ModelClass
from qma.core.vocabulary.registry import VocabularyError
from qmf.core import is_ok, is_refusal


def test_core_identifies_local_proxy_deployments() -> None:
    record = DeploymentRecord(
        deployment_id="opencodex-workhorse",
        model_class=ModelClass.WORKHORSE_GENERAL,
        adapter=OPENCODEX_ADAPTER,
        auth_mode=AUTH_MODE_NONE,
    )
    assert is_local_proxy_deployment(record)
    broker_record = DeploymentRecord(
        deployment_id="broker-owned",
        model_class=ModelClass.WORKHORSE_GENERAL,
        credential_ref="cred://models/openai",
    )
    assert not is_local_proxy_deployment(broker_record)


def test_core_rejects_wrong_auth_mode() -> None:
    with pytest.raises(VocabularyError):
        DeploymentRecord(
            deployment_id="bad-auth",
            model_class=ModelClass.FAST_CHEAP,
            adapter=OPENCODEX_ADAPTER,
            auth_mode="api_key",
            bind_host="127.0.0.1",
        )


def test_credential_allowlist_is_code_declared_and_default_deny() -> None:
    assert is_credential_ref_allowed("cred://models/openai")
    assert is_credential_ref_allowed("cred://compute/sandbox-a")
    assert is_credential_ref_allowed("cred://corpus/docs")
    assert is_credential_ref_allowed("cred://telemetry/otlp")
    assert not is_credential_ref_allowed("cred://venue/ctrader")
    assert not is_credential_ref_allowed("cred://broker/icmarkets")
    assert not is_credential_ref_allowed("cred://exchange/binance")
    assert not is_credential_ref_allowed("cred://trading-node/vps")
    assert not is_credential_ref_allowed("cred://platform-registry/promo")
    assert not is_credential_ref_allowed("cred://unknown/x")

    assert OUT_OF_SCOPE_CREDENTIAL_REF_PREFIXES
    assert_allowlist_not_widenable()
    with pytest.raises(CredentialAllowlistError):
        assert_allowlist_not_widenable(ALLOWED_CREDENTIAL_REF_PREFIXES | {"cred://venue/"})


def test_hook_payloads_exclude_secrets_by_schema() -> None:
    assert is_ok(
        assert_no_secret_in_hook_payloads(
            updated_input={"credential_ref": "cred://models/openai"},
            injected_context={"note": "ok"},
        )
    )
    refused = assert_no_secret_in_hook_payloads(
        updated_output={"api_key": "literally-secret"},
    )
    assert is_refusal(refused)

    with pytest.raises(VocabularyError):
        build_hook_result("allow", updated_input={"secret": "nope"})

    ok = build_hook_result(
        "allow",
        updated_input={"credential_ref": "cred://models/openai"},
        injected_context={"hint": "ref-only"},
    )
    assert ok.updated_input is not None
    assert "secret" not in ok.updated_input
