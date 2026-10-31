"""The write-only key route (UI handoff section 26 gap 3): a `qmx/` name is written, any other
name is refused and touches nothing, the list names which keys are set and never a value."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_connect import BEARER, Store, app_of, qmx_folder, world

from qmx_host.connect import KINDS, Connect

VALUE = "planted-key-value-5521"


def client(tmp_path: Path, keys: Store) -> TestClient:
    return TestClient(app_of(Connect(world(qmx_folder(tmp_path / "QMX"), keys=keys), KINDS)))


def test_a_qmx_name_is_written_and_listed_and_no_value_is_ever_answered(tmp_path: Path) -> None:
    keys = Store()
    with client(tmp_path, keys) as rest:
        written = [
            rest.put(f"/api/keys/{name}", json={"value": VALUE}, headers=BEARER)
            for name in ("qmx/ctrader-client-id", "qmx/r2-lane")
        ]
        listed = rest.get("/api/keys", headers=BEARER)
    assert [w.status_code for w in written] == [204, 204]
    assert all(w.content == b"" for w in written)
    assert listed.json() == {"set": ["qmx/ctrader-client-id", "qmx/r2-lane"]}
    assert VALUE not in listed.text
    assert keys.values == {"qmx/ctrader-client-id": VALUE, "qmx/r2-lane": VALUE}


@pytest.mark.parametrize(
    "name",
    [
        "git:https://github.com",
        "qmx",
        "qmx/../windows",
        "qmx/rclone-config",
        "qmx/control-token",
        "qmx/read/ctrader-app",
        "qmx/token/ctrader-app",
    ],
)
def test_a_name_outside_qmx_or_one_qmx_keeps_itself_answers_400_and_touches_nothing(
    tmp_path: Path, name: str
) -> None:
    keys = Store()
    keys.values[name] = "held before"
    with client(tmp_path, keys) as rest:
        answer = rest.put(f"/api/keys/{name}", json={"value": VALUE}, headers=BEARER)
    assert answer.status_code == 400
    assert "nothing was written" in answer.json()["detail"]
    assert keys.values == {name: "held before"}


def test_a_declared_key_he_typed_elsewhere_is_listed_and_an_empty_value_is_refused(
    tmp_path: Path,
) -> None:
    keys = Store()
    keys.values["qmx/ctrader-client-secret"] = VALUE
    with client(tmp_path, keys) as rest:
        empty = rest.put("/api/keys/qmx/e2b", json={"value": ""}, headers=BEARER)
        listed = rest.get("/api/keys", headers=BEARER).json()
    assert empty.status_code == 422
    assert listed == {"set": ["qmx/ctrader-client-secret"]}


def test_both_key_routes_need_the_bearer(tmp_path: Path) -> None:
    keys = Store()
    with client(tmp_path, keys) as rest:
        answers = [
            rest.put("/api/keys/qmx/r2-lane", json={"value": VALUE}).status_code,
            rest.get("/api/keys").status_code,
        ]
    assert answers == [401, 401]
    assert keys.values == {}
