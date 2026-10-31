"""A cTrader connection reads with the Open API descriptor set QMX ships (tag 91), so he never
sets protocol files by hand."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from qmf.core import is_refusal

from qmx_broker.models import Connection
from qmx_broker.service import PROTOCOL_SET, ReadRefused, compiled

APP = "qmx/read/ctrader-app"


def row(**protocol: object) -> Connection:
    return Connection.model_validate({"id": "demo", "credential_ref": APP, **protocol})


def test_qmx_ships_one_copy_of_spotwares_tag_91_set_with_its_licence() -> None:
    assert hashlib.sha256(PROTOCOL_SET.read_bytes()).hexdigest() == (
        "044991dd5fd4ea9941289e76f1a7b65c15931d6ba4f39fab33fc24e5c3173eb2"
    )
    assert (PROTOCOL_SET.parent / "Spotware-LICENSE.txt").read_text().startswith("MIT License")
    assert not (Path(__file__).parent / "fixtures" / "tag91.pb").exists()


@pytest.mark.parametrize("protocol", [{}, {"protocol_tag": 91}])
def test_a_row_naming_no_protocol_file_compiles_the_shipped_set(
    protocol: dict[str, object],
) -> None:
    proto = compiled(row(**protocol))

    assert not is_refusal(proto.message_class("ProtoOATraderReq"))


@pytest.mark.parametrize(
    ("protocol", "line"),
    [
        (
            {"protocol_path": "D:/nowhere/openapi.pb", "protocol_tag": 91},
            "The cTrader protocol file D:/nowhere/openapi.pb that demo names does not exist; "
            "clear protocol_path and protocol_tag on demo to use the set QMX ships",
        ),
        (
            {"protocol_path": "D:/nowhere/openapi.pb"},
            "demo names protocol_path but no protocol_tag; set both, or clear both to use the "
            "set QMX ships",
        ),
        (
            {"protocol_tag": 92},
            "demo names protocol_tag 92 but no protocol_path; set both, or clear both to use the "
            "set QMX ships (tag 91)",
        ),
    ],
)
def test_a_missing_or_half_set_protocol_row_is_refused_by_name(
    protocol: dict[str, object], line: str
) -> None:
    with pytest.raises(ReadRefused) as refused:
        compiled(row(**protocol))

    assert (refused.value.code, str(refused.value)) == ("protocol_files", line)
