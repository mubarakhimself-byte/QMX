"""Existing session/grant machinery must guard the real injected read callback."""

from collections.abc import Mapping
from pathlib import Path

from qma.daemon.request_runtime.spot_tools import SpotQueryDoor, spot_query_descriptor
from qma.wire.invocation_envelope import ContributionRecord, InstanceRecord, compute_input_hash
from qmf.core import Ok, Result, is_ok, is_refusal
from test_product_session_grants import (
    _envelope,  # pyright: ignore[reportPrivateUsage] - existing authority fixture
    _grant_kwargs,  # pyright: ignore[reportPrivateUsage] - existing authority fixture
    _mint_kwargs,  # pyright: ignore[reportPrivateUsage] - existing authority fixture
    _open,  # pyright: ignore[reportPrivateUsage] - actual journal/sqlite fixture
)


def test_query_dispatch_account_scope_and_revocation(tmp_path: Path) -> None:
    from qma.daemon import ProductSessionService

    substrate, journal = _open(tmp_path)
    try:
        sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
        assert is_ok(sessions.mint(**_mint_kwargs()))
        assert is_ok(
            sessions.host_grant(
                "psess:desk-1",
                **_grant_kwargs(
                    op_id="qmn.spot.paper.query",
                    parameter_ceiling={
                        "allow_keys": ["account_id", "provider_connection_id", "venue_id"]
                    },
                ),
            )
        )
        descriptor = spot_query_descriptor()
        payload = {
            "account_id": "a",
            "provider_connection_id": "conn:recorded",
            "venue_id": "recorded:crypto",
        }
        hashed = compute_input_hash(payload, descriptor=descriptor)
        assert is_ok(hashed)
        calls: list[int] = []

        def query() -> Result[Mapping[str, object]]:
            calls.append(1)
            return Ok({"simulation": True, "account_id": "a", "balance": "1000"})

        door = SpotQueryDoor(
            sessions,
            "conn:recorded",
            "recorded:crypto",
            "a",
            ContributionRecord("analysis-backtest:qmb", "0.1.0", "enabled"),
            InstanceRecord("inst:1", 4),
            query,
        )
        env = _envelope(op_id=descriptor.op_id, input_hash=hashed.value, caller_kind="agent")
        result = door.invoke(
            "psess:desk-1", envelope=env, payload=payload, now="2026-10-04T00:00:00Z"
        )
        assert is_ok(result) and result.value["simulation"] is True and calls == [1]
        wrong = door.invoke(
            "psess:desk-1",
            envelope=env,
            payload={**payload, "account_id": "b"},
            now="2026-10-04T00:00:00Z",
        )
        assert is_refusal(wrong) and calls == [1]
        for field, value in (("venue_id", "other:venue"), ("provider_connection_id", "conn:other")):
            outside = door.invoke(
                "psess:desk-1",
                envelope=env,
                payload={**payload, field: value},
                now="2026-10-04T00:00:00Z",
            )
            assert is_refusal(outside) and calls == [1]
        revoked = sessions.revoke_grant(
            "psess:desk-1",
            grant_id="grant:1",
            principal="operator",
            reason="spot query revoke test",
            revoked_at="2026-10-04T00:00:01Z",
        )
        assert is_ok(revoked)
        result = door.invoke(
            "psess:desk-1", envelope=env, payload=payload, now="2026-10-04T00:00:02Z"
        )
        assert is_refusal(result) and calls == [1]
    finally:
        journal.close()
        substrate.close()
