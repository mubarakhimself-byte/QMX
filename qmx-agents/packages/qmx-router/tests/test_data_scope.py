"""The run pass's data scope: the door refuses a pass that names no dataset."""

from __future__ import annotations

import base64
import hashlib
import hmac

from qmx_router.passes import Ask, PassAuthority, canonical

SECRET = b"data-scope-test-secret"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _authority() -> PassAuthority:
    return PassAuthority(secret=SECRET, clock=lambda: 1_000.0)


def test_a_pass_without_a_data_scope_is_refused_for_a_dataset() -> None:
    authority = _authority()
    _, bearer = authority.mint(run="run-1", placement="server")
    minted, refused = authority.check(bearer, Ask(data="dukascopy/EURUSD/bar-m1/-"))
    assert minted.data_scope == ()
    assert refused is not None
    assert refused.code == "data_scope"
    assert "no data scope" in refused.detail


def test_a_data_scope_covers_its_dataset_and_no_other() -> None:
    authority = _authority()
    _, bearer = authority.mint(
        run="run-1", placement="server", data_scope=("dukascopy/EURUSD/bar-m1/-",)
    )
    served, refused = authority.check(bearer, Ask(data="dukascopy/EURUSD/bar-m1/-"))
    assert refused is None
    assert served.data_scope == ("dukascopy/EURUSD/bar-m1/-",)
    _, other = authority.check(bearer, Ask(data="dukascopy/GBPUSD/bar-m1/-"))
    assert other is not None
    assert other.code == "data_scope"


def test_a_bearer_minted_before_the_field_verifies_with_no_scope() -> None:
    authority = _authority()
    minted, _ = authority.mint(run="run-0", placement="server")
    body = canonical(
        minted.id,
        minted.run,
        minted.attempt,
        minted.placement,
        minted.read_scope,
        minted.write_prefix,
        minted.key_scope,
        minted.model_scope,
        minted.issued_at,
        minted.expires_at,
        minted.handle,
        legacy=True,
    )
    mac = hmac.new(SECRET, body, hashlib.sha256).digest()
    legacy = f"qmx1.{_b64(body)}.{_b64(mac)}"
    parsed, refusal = authority.parse(legacy)
    assert refusal is None
    assert parsed.run == "run-0"
    assert parsed.data_scope == ()
    _, refused = authority.check(legacy, Ask(data="dukascopy/EURUSD/bar-m1/-"))
    assert refused is not None
    assert refused.code == "data_scope"
