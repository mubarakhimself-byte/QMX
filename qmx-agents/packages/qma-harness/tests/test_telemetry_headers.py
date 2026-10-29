"""Every sender signs in to OpenObserve on this PC (design 06 section 9, plan review MUST 6): the
ingest credential the key store holds goes out as an `Authorization` header, to the loopback only,
and the CLI gets it in its own environment."""

from __future__ import annotations

from pathlib import Path

import pytest

from qma.harness.launch import telemetry_env
from qma.telemetry import INGEST_KEY, THIS_PC_ENDPOINT, configured, headers

INGEST = "Basic cWE6cGxhbnRlZA=="


def home_sending_to(tmp_path: Path, target: str) -> Path:
    (tmp_path / "settings.toml").write_text(f'[telemetry]\nsend_to = "{target}"\n', "utf-8")
    return tmp_path


def held(name: str) -> str | None:
    return INGEST if name == INGEST_KEY else None


def test_the_ingest_credential_goes_to_this_pcs_openobserve_and_nowhere_else(
    tmp_path: Path,
) -> None:
    assert headers(home_sending_to(tmp_path, "this-pc"), held) == {"Authorization": INGEST}
    assert headers(home_sending_to(tmp_path, "myserver"), held) == {}
    assert headers(home_sending_to(tmp_path, "off"), held) == {}
    assert headers(home_sending_to(tmp_path, "this-pc"), lambda _name: None) == {}


def test_a_key_store_that_fails_sends_no_header_and_raises_nothing(tmp_path: Path) -> None:
    def broken(_name: str) -> str | None:
        raise RuntimeError("no keyring backend")

    assert headers(home_sending_to(tmp_path, "this-pc"), broken) == {}


@pytest.mark.parametrize("target", ["this-pc", "off"])
def test_the_cli_gets_the_header_percent_encoded_in_its_own_environment(
    tmp_path: Path, target: str
) -> None:
    home = home_sending_to(tmp_path, target)
    env = telemetry_env(configured(home), headers(home, held))
    if target == "off":
        assert env == {}
        return
    assert env["OTEL_EXPORTER_OTLP_ENDPOINT"] == THIS_PC_ENDPOINT
    assert env["OTEL_EXPORTER_OTLP_HEADERS"] == "Authorization=Basic%20cWE6cGxhbnRlZA%3D%3D"
