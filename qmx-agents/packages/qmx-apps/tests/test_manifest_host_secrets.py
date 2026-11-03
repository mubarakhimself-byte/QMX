"""No app manifest may name a secret the host made for itself, on any role (C-27). The bearer
acts as the operator, so an app that declared `qmx/control-token` could promote a unit to live.
Credential Manager and NTFS ignore letter case, so every spelling of a host name is refused, and
a name that is not plain ASCII `qmx/<word>` never reaches the case check at all."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from qma.harness import QmxHome
from qmx_host.host import Role, control_for  # pyright: ignore[reportMissingTypeStubs]

from qmx_apps.errors import AppError
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import Supervisor

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
BEARER = "is the host's own control bearer, which acts as the operator; no app may declare it."
NOT_A_NAME = "Secrets must reference qmx/* Credential Manager services."


def app_naming(tmp_path: Path, service: str, *, app_id: str = "exchange-status") -> Path:
    source = tmp_path / "asker"
    shutil.copytree(EXAMPLE, source, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    manifest = source / "app.toml"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace('id = "exchange-status"', f'id = "{app_id}"', 1)
    text = text.replace(
        "[capabilities]\n", "[capabilities]\nsecrets = { ASKED = '''" + service + "''' }\n", 1
    )
    manifest.write_text(text, encoding="utf-8")
    return source


def refusal(tmp_path: Path, service: str) -> tuple[str, str, list[object]]:
    owner = Supervisor(tmp_path / "home")
    try:
        with pytest.raises(AppError) as refused:
            owner.install(app_naming(tmp_path, service), trust="first_party")
        return refused.value.code, str(refused.value), list(owner.list())
    finally:
        owner.close()


@pytest.mark.parametrize(
    ("service", "sentence"),
    [
        ("qmx/control-token", f"qmx/control-token {BEARER}"),
        ("qmx/CONTROL-TOKEN", f"qmx/CONTROL-TOKEN {BEARER}"),
        ("qmx/Control-Token", f"qmx/Control-Token {BEARER}"),
        (
            "qmx/pairing-key",
            "qmx/pairing-key is the host's own pairing key, which signs every run pass; no app "
            "may declare it.",
        ),
        (
            "qmx/Run-Pass-Key",
            "qmx/Run-Pass-Key is the host's own run pass key; no app may declare it.",
        ),
        ("qmx/chatgpt", "qmx/chatgpt is the host's own ChatGPT sign-in; no app may declare it."),
        (
            "qmx/ChatGPT-3",
            "qmx/ChatGPT-3 is the host's own ChatGPT sign-in; no app may declare it.",
        ),
        (
            "qmx/rclone-config",
            "qmx/rclone-config is the host's own backup configuration password; no app may "
            "declare it.",
        ),
        (
            "qmx/OpenObserve-Root",
            "qmx/OpenObserve-Root is the host's own deep-logs root password; no app may declare "
            "it.",
        ),
        (
            "qmx/openobserve-ingest",
            "qmx/openobserve-ingest is the host's own deep-logs sign-in; no app may declare it.",
        ),
        (
            "qmx/openobserve-agent",
            "qmx/openobserve-agent is the host's own deep-logs sign-in; no app may declare it.",
        ),
    ],
)
def test_an_app_naming_a_host_secret_in_any_case_is_refused_and_never_installed(
    tmp_path: Path, service: str, sentence: str
) -> None:
    assert refusal(tmp_path, service) == ("invalid_definition", sentence, [])


@pytest.mark.parametrize(
    "service",
    [
        "QMX/control-token",
        "Qmx/CONTROL-TOKEN",
        " qmx/control-token",
        "qmx/control-token ",
        "qmx/control-token\n",
        "qmx/control-token\t",
        "qmx/control-to\N{KELVIN SIGN}en",
        "qmx/c\N{CYRILLIC SMALL LETTER O}ntrol-token",
        "qmx/control\N{FULLWIDTH HYPHEN-MINUS}token",
        "qmx/control\N{ZERO WIDTH SPACE}-token",
        "qmx/control-token/",
        "qmx//control-token",
        "qmx/../control-token",
        "qmx\\control-token",
        "qmx/connect/control-token",
        "qmx/pairing-key.previous",
        "qmx/",
    ],
)
def test_a_look_alike_or_a_path_of_a_host_name_is_refused_as_no_qmx_name(
    tmp_path: Path, service: str
) -> None:
    assert refusal(tmp_path, service) == ("invalid_definition", NOT_A_NAME, [])


def test_the_trading_node_is_refused_the_bearer_too(tmp_path: Path) -> None:
    with pytest.raises(AppError) as refused:
        Definition.load(app_naming(tmp_path, "qmx/control-token", app_id="trading-node"))

    assert (refused.value.code, str(refused.value)) == (
        "invalid_definition",
        f"qmx/control-token {BEARER}",
    )


@pytest.mark.parametrize("role", ["pc", "node", "server"])
def test_every_role_refuses_the_bearer_at_install(tmp_path: Path, role: Role) -> None:
    control = control_for(role, QmxHome(tmp_path / "folder" / "data"))
    try:
        with pytest.raises(AppError) as refused:
            control.app_runtime().install(
                app_naming(tmp_path, "qmx/CONTROL-TOKEN"), trust="first_party"
            )
        listed = control.app_runtime().list()
    finally:
        control.close()

    assert (refused.value.code, str(refused.value), listed) == (
        "invalid_definition",
        f"qmx/CONTROL-TOKEN {BEARER}",
        [],
    )


@pytest.mark.parametrize(
    "service", ["qmx/exchange-status-key", "qmx/control-tokens", "qmx/chatgpt5", "qmx/rclone"]
)
def test_an_apps_own_key_beside_a_host_name_still_loads(tmp_path: Path, service: str) -> None:
    loaded = Definition.load(app_naming(tmp_path, service))

    assert loaded.manifest.capabilities.secrets == {"ASKED": service}
