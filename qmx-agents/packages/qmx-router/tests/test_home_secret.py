"""The run-pass secret is the home's: it survives a restart and is shared by the paired machines
(engine AD-28, Library AD-12, wrap-up seam C)."""

from __future__ import annotations

import time
from pathlib import Path

from qmx_router.passes import DEFAULT_TTL_S, Ask, PassAuthority


def bearer(authority: PassAuthority) -> str:
    return authority.mint(run="run-1", placement="contabo")[1]


def code_of(authority: PassAuthority, token: str) -> str | None:
    refused = authority.check(token, Ask())[1]
    return None if refused is None else refused.code


def paired(home: Path, key: str) -> Path:
    (home / "vault").mkdir(parents=True, exist_ok=True)
    (home / "vault" / "pairing-key").write_text(f"{key}\n", encoding="utf-8")
    return home


def test_a_pass_minted_before_a_restart_verifies_after_it(tmp_path: Path) -> None:
    token = bearer(PassAuthority.for_home(tmp_path))
    restarted = PassAuthority.for_home(tmp_path)
    assert code_of(restarted, token) is None
    assert len((tmp_path / "vault" / "run-pass-key").read_bytes()) == 32


def test_the_paired_machines_of_one_home_verify_each_others_passes(tmp_path: Path) -> None:
    pc = PassAuthority.for_home(paired(tmp_path / "pc", "same-key"))
    server = PassAuthority.for_home(paired(tmp_path / "server", "same-key"))
    stranger = PassAuthority.for_home(paired(tmp_path / "other", "other-key"))
    token = bearer(pc)
    assert (code_of(server, token), code_of(stranger, token)) == (None, "bad_mac")


def test_the_outgoing_secret_is_accepted_for_one_pass_lifetime(tmp_path: Path) -> None:
    now = [time.time()]
    clock = lambda: now[0]  # noqa: E731
    unpaired = PassAuthority.for_home(tmp_path, clock=clock)
    old = bearer(unpaired)
    paired(tmp_path, "new-key")
    # The pairing key's own file time anchors the window, so the clock follows it.
    now[0] = (tmp_path / "vault" / "pairing-key").stat().st_mtime + 60
    after = PassAuthority.for_home(tmp_path, clock=clock)
    fresh = bearer(after)
    assert (code_of(unpaired, old), code_of(after, fresh)) == (None, None)
    now[0] += DEFAULT_TTL_S
    assert code_of(PassAuthority.for_home(tmp_path, clock=clock), old) == "bad_mac"
    assert code_of(PassAuthority.for_home(paired(tmp_path / "peer", "new-key")), fresh) is None
