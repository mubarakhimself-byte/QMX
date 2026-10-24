"""A remote attempt's run pass reaches the server's data read and nothing else (AD-70, Lib AD-28).

The principal door admits a verified, unexpired, unrevoked pass on `POST /api/data/read` only,
and the read takes its scope from that pass. The local bearer keeps today's rule.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_control.server import BearerGate
from qmx_router.passes import PassAuthority, RevocationList
from test_market_data import FEB, JAN, _committed, _door  # pyright: ignore[reportPrivateUsage]

from qmx_host.door import PrincipalDoor
from qmx_host.market_data import Placement, market_router

LOCAL = "local-token"
"""The host's gate token for this test."""
SERIES = "dukascopy/EURUSD/bar-m1/-"
OTHER = "dukascopy/GBPUSD/bar-m1/-"


def door_app(tmp_path: Path, passes: PassAuthority) -> FastAPI:
    door = _door(tmp_path, placement=Placement.SERVER)
    _committed(tmp_path, door)
    app = FastAPI()
    app.include_router(market_router(door))
    app.add_middleware(BearerGate, token=LOCAL)
    app.add_middleware(PrincipalDoor, chat_routes=[], bearer=LOCAL, passes=passes)
    return app


def authority(tmp_path: Path) -> PassAuthority:
    return PassAuthority(revocations=RevocationList(tmp_path / "revoked.json"))


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def read(series: str, scope: list[str] | None = None) -> dict[str, object]:
    body: dict[str, object] = {"series": series, "start_ns": JAN, "end_ns": FEB}
    return body if scope is None else body | {"data_scope": scope}


def test_a_forged_or_revoked_pass_gets_401_on_the_data_read(tmp_path: Path) -> None:
    passes = authority(tmp_path)
    _, forged = authority(tmp_path / "elsewhere").mint(
        run="run-1", placement="contabo", data_scope=(SERIES,)
    )
    revoked, token = passes.mint(run="run-1", placement="contabo", data_scope=(SERIES,))
    passes.revocations.revoke(revoked.id)

    with TestClient(door_app(tmp_path, passes)) as rest:
        forged_answer = rest.post("/api/data/read", json=read(SERIES), headers=bearer(forged))
        revoked_answer = rest.post("/api/data/read", json=read(SERIES), headers=bearer(token))

    assert forged_answer.status_code == 401
    assert forged_answer.json()["error"]["code"] == "run_pass_refused"
    assert revoked_answer.status_code == 401
    assert revoked_answer.json()["error"]["message"].startswith("revoked: ")


def test_a_valid_pass_reads_only_its_own_scope_even_when_the_body_asks_for_more(
    tmp_path: Path,
) -> None:
    passes = authority(tmp_path)
    _, token = passes.mint(run="run-1", placement="contabo", data_scope=(SERIES,))

    with TestClient(door_app(tmp_path, passes)) as rest:
        own = rest.post("/api/data/read", json=read(SERIES), headers=bearer(token))
        wider = rest.post(
            "/api/data/read", json=read(SERIES, [SERIES, OTHER]), headers=bearer(token)
        )
        outside = rest.post("/api/data/read", json=read(OTHER), headers=bearer(token))
        aimed = rest.post(
            "/api/data/read", json=read(SERIES) | {"into": "elsewhere"}, headers=bearer(token)
        )

    assert own.status_code == 200
    assert (own.json()["series"], own.json()["rows"]) == (SERIES, 4)
    assert wider.status_code == 403
    assert wider.json()["detail"]["context"]["field"] == "data_scope"
    assert wider.json()["detail"]["context"]["wider"] == [OTHER]
    assert outside.status_code == 400
    assert outside.json()["detail"]["context"]["field"] == "data_scope"
    assert (aimed.status_code, aimed.json()["detail"]["context"]["field"]) == (403, "into")


def test_a_valid_pass_gets_401_on_any_other_route(tmp_path: Path) -> None:
    passes = authority(tmp_path)
    _, token = passes.mint(run="run-1", placement="contabo", data_scope=(SERIES,))

    with TestClient(door_app(tmp_path, passes)) as rest:
        listed = rest.get("/api/data/instruments", headers=bearer(token))
        committed = rest.post(
            "/api/data/commit", json={"staged": [], "staging": "x"}, headers=bearer(token)
        )

    assert (listed.status_code, committed.status_code) == (401, 401)


def test_the_local_bearer_still_reads_with_the_body_scope(tmp_path: Path) -> None:
    passes = authority(tmp_path)

    with TestClient(door_app(tmp_path, passes)) as rest:
        scoped = rest.post("/api/data/read", json=read(SERIES, [SERIES]), headers=bearer(LOCAL))
        unscoped = rest.post("/api/data/read", json=read(SERIES), headers=bearer(LOCAL))
        nobody = rest.post("/api/data/read", json=read(SERIES, [SERIES]))

    assert (scoped.status_code, scoped.json()["rows"]) == (200, 4)
    assert unscoped.status_code == 400
    assert unscoped.json()["detail"]["context"]["field"] == "data_scope"
    assert nobody.status_code == 401
