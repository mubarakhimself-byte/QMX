"""Two-process acceptance fixture: QMF archive -> QMN simulation -> QMA read.

Run seed and verify in separate Python processes against the same local root.
This intentionally uses synthetic data, no UI, HTTP, network or exchange SDK.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar

from qma.daemon import AuthoritativeJournal, PersistenceSubstrate, ProductSessionService
from qma.daemon.request_runtime.spot_tools import SpotQueryDoor, spot_query_descriptor
from qma.wire.invocation_envelope import ContributionRecord, InstanceRecord, compute_input_hash
from qmf.core import DataDrivenClock, Instant, Ok, Result, WriterId, is_ok, is_refusal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore
from qmn.venue.spot_paper import AccountScope, PaperPolicy, SpotPaperAccount
from qmn.venue.spot_recorded import RecordedSpotSource

MARKET = {
    "id": "BTCUSDT",
    "symbol": "BTC/USDT",
    "base": "BTC",
    "quote": "USDT",
    "spot": True,
    "active": True,
    "contract": False,
    "precision": {"amount": "0.001", "price": "0.01"},
    "limits": {"amount": {"min": "0.001", "max": "10"}, "cost": {"min": "10", "max": "1000000"}},
}
TICK = {
    "origin": "synthetic",
    "bid": "99.00",
    "ask": "100.00",
    "event_ns": 1000,
    "received_ns": 1000,
    "sequence": 1,
    "quantity": "0.100",
    "snapshot": True,
}
CONTRIBUTION = ContributionRecord("spot-evidence:qmn", "0.1.0", "enabled")
INSTANCE = InstanceRecord("inst:spot", 1)
NOW = "2026-10-04T00:00:00Z"


def require(condition: object, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


T = TypeVar("T")


def unwrap(result: Result[T]) -> T:
    if is_refusal(result):
        raise RuntimeError(str(result))
    return result.value


def account(root: Path, account_id: str, node: str, cap: str) -> SpotPaperAccount:
    return unwrap(
        SpotPaperAccount.open(
            root / "paper",
            scope=AccountScope("conn:recorded", "recorded:crypto", account_id, node),
            policy=PaperPolicy(f"policy:{account_id}", cap, "0.001", 100, 2, 10),
            market_payload=MARKET,
            precision_mode="TICK_SIZE",
            initial_balances={"USDT": "1000", "BTC": "1"},
        )
    )


def run(root: Path, phase: str) -> Mapping[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    a, b = account(root, "a", "singapore", "1000"), account(root, "b", "new-york", "15")
    substrate = unwrap(
        PersistenceSubstrate.open(root / "authority", machine="local", boot_epoch_id=phase)
    )
    base = 1_800_000_000_000_000_000 + (0 if phase == "seed" else 10000)
    clock = DataDrivenClock(
        boot_epoch_id=phase,
        wall_instants=tuple(Instant(base + i) for i in range(256)),
        monotonic_ns=tuple(range(256)),
    )
    journal = unwrap(AuthoritativeJournal.bind(substrate, clock=clock))
    sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
    if phase == "verify":
        unwrap(sessions.restore_from_journal())
    source = RecordedSpotSource(
        SourceObservationBoundary(EvidenceStore(root / "qmf")),
        WriterId("local", "recorded-spot", "source:synthetic-spot", "fixture-epoch"),
        "source:synthetic-spot",
        "recorded:crypto",
        a.market,
    )
    try:
        if phase == "seed":
            require(not (root / "receipts.json").exists(), "seed root must be fresh")
            first = unwrap(
                source.ingest(TICK, native_id="tick:1", revision="v1", writer_sequence=0)
            )
            saved = {
                "archive_ref": first.archive.fingerprint.value,
                "observation_ref": first.observation_fingerprint.value,
            }
            (root / "receipts.json").write_text(json.dumps(saved), encoding="utf-8")
            require(
                is_ok(source.replay_into(a, first.archive.fingerprint))
                and is_ok(source.replay_into(b, first.archive.fingerprint)),
                "both nodes need ready archived data",
            )
            require(is_ok(a.submit("buy-1", "buy", "0.200", "100.00", now_ns=1000)), "a must admit")
            require(
                is_refusal(b.submit("buy-1", "buy", "0.200", "100.00", now_ns=1000)),
                "b policy must refuse",
            )
            require(
                is_refusal(
                    SpotPaperAccount.open(
                        root / "paper",
                        scope=AccountScope("conn:recorded", "recorded:crypto", "a", "other-node"),
                        policy=a.policy,
                        market_payload=MARKET,
                        precision_mode="TICK_SIZE",
                        initial_balances={"USDT": "1000", "BTC": "1"},
                    )
                ),
                "duplicate node writer must refuse",
            )
            tick2 = {
                **TICK,
                "sequence": 2,
                "event_ns": 1001,
                "received_ns": 1001,
                "snapshot": False,
            }
            next_receipt = unwrap(
                source.ingest(tick2, native_id="tick:2", revision="v1", writer_sequence=1)
            )
            unwrap(source.replay_into(a, next_receipt.archive.fingerprint))
            unwrap(
                sessions.mint(
                    product_session_id="psess:spot",
                    profile="authoring",
                    principal="operator",
                    contribution={
                        "qualified_id": CONTRIBUTION.qualified_id,
                        "package_version": CONTRIBUTION.package_version,
                    },
                    instance_id=INSTANCE.instance_id,
                    config_revision=1,
                    as_of=NOW,
                    granted_ops=(),
                    scope_path=[{"kind": "desk", "id": "research"}],
                )
            )
            unwrap(
                sessions.host_grant(
                    "psess:spot",
                    grant_id="grant:spot",
                    op_id="qmn.spot.paper.query",
                    op_version=1,
                    effect_class="read",
                    parameter_ceiling={
                        "allow_keys": ["account_id", "provider_connection_id", "venue_id"]
                    },
                    expires_at="2026-12-31T00:00:00Z",
                )
            )
        else:
            require(a.query()["feed_status"] == "UNSYNCED", "restart must invalidate price")
            require(
                a.query()["orders"][0]["filled"] == "0.100", "restart must retain exactly one fill"
            )
            unwrap(a.cancel("buy-1"))
            unwrap(a.cancel("buy-1"))
            require(a.query()["balances"]["USDT"]["reserved"] == "0", "cancel must release once")
        saved: dict[str, Any] = json.loads((root / "receipts.json").read_text(encoding="utf-8"))
        calls: list[int] = []

        def read() -> Result[Mapping[str, object]]:
            actual = source.query(saved["archive_ref"])
            if is_refusal(actual):
                return actual
            require(
                actual.value.fingerprint.value == saved["observation_ref"],
                "source identity must match",
            )
            calls.append(1)
            return Ok(
                {
                    "paper": dict(a.query()),
                    "market_data": actual.value.to_row(),
                    "archive_ref": saved["archive_ref"],
                }
            )

        door = SpotQueryDoor(
            sessions, "conn:recorded", "recorded:crypto", "a", CONTRIBUTION, INSTANCE, read
        )
        payload = {
            "provider_connection_id": "conn:recorded",
            "account_id": "a",
            "venue_id": "recorded:crypto",
        }
        hashed = unwrap(compute_input_hash(payload, descriptor=spot_query_descriptor()))
        envelope = {
            "logical_invocation_id": f"inv:spot:{phase}",
            "attempt_id": 1,
            "op_id": "qmn.spot.paper.query",
            "op_version": 1,
            "contribution": {"qualified_id": CONTRIBUTION.qualified_id, "package_version": "0.1.0"},
            "instance_id": "inst:spot",
            "config_revision": 1,
            "grant_id": "grant:spot",
            "effect_class": "read",
            "idempotency_key": f"idem:{phase}",
            "reconcile_policy": "query-then-decide",
            "input_hash": hashed,
            "call_depth": 0,
            "caller_kind": "agent",
            "caller_session_ref": "psess:spot",
        }
        actual_read = unwrap(door.invoke("psess:spot", envelope=envelope, payload=payload, now=NOW))
        require(calls == [1], "the real callback must run exactly once")
        require(
            is_refusal(
                door.invoke(
                    "psess:spot", envelope=envelope, payload={**payload, "account_id": "b"}, now=NOW
                )
            ),
            "account retarget must refuse",
        )
        if phase == "verify":
            unwrap(
                sessions.revoke_grant(
                    "psess:spot",
                    grant_id="grant:spot",
                    principal="operator",
                    reason="fixture revoke",
                    revoked_at="2026-10-04T00:00:01Z",
                )
            )
            require(
                is_refusal(
                    door.invoke(
                        "psess:spot", envelope=envelope, payload=payload, now="2026-10-04T00:00:02Z"
                    )
                ),
                "revocation must deny callback",
            )
            require(calls == [1], "denials must not read the domain")
        return {
            "phase": phase,
            "simulation": True,
            "network_calls": 0,
            "operation": "qmn.spot.paper.query@1",
            "read": actual_read,
            "other_account": dict(b.query()),
            "callback_count": len(calls),
            "limitations": [
                "local shared-root writer ownership",
                "synthetic infrastructure",
                "no live exchange",
                "this library journey does not cover the separately tested paired CT40 startup",
                "no Book/BMS risk certification",
            ],
        }
    finally:
        a.close()
        b.close()
        journal.close()
        substrate.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("seed", "verify"))
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    report = run(args.root, args.phase)
    (args.root / f"{args.phase}-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "phase": args.phase,
                "simulation": True,
                "operation": report["operation"],
                "callback_count": report["callback_count"],
            }
        )
    )
