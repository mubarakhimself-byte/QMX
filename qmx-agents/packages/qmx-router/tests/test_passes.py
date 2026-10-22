"""E25: every way a run pass is refused, and the one way it is not.

The pass is the only credential a remote attempt carries, so each refusal is a fact a router
depends on. One test per code, each asking through `PassAuthority.check`, plus the round trip and
the two clocks: the deadline and the owner's end.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from qmx_router.passes import (
    Ask,
    PassAuthority,
    Refusal,
    RevocationList,
    bearer_of,
)


class Clock:
    def __init__(self, at: float = 1_800_000_000.0) -> None:
        self.at = at

    def __call__(self) -> float:
        return self.at

    def tick(self, seconds: float) -> None:
        self.at += seconds


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def authority(clock: Clock) -> PassAuthority:
    return PassAuthority(secret=b"k" * 32, clock=clock)


def _token(authority: PassAuthority) -> str:
    _, bearer = authority.mint(
        run="run-1",
        placement="contabo",
        attempt=2,
        read_scope=("runs", "vault"),
        write_prefix="runs/run-1",
        key_scope=("qmx/openrouter",),
        model_scope=("claude/haiku",),
    )
    return bearer


def _code(authority: PassAuthority, token: str, ask: Ask) -> str:
    _, refusal = authority.check(token, ask)
    assert refusal is not None
    return refusal.code


def test_a_minted_pass_covers_exactly_its_scopes(authority: PassAuthority) -> None:
    token = _token(authority)
    _, refusal = authority.check(
        token,
        Ask(
            run="run-1",
            attempt=2,
            placement="contabo",
            read="runs/run-1/journal.jsonl",
            write="runs/run-1/out.json",
            key="qmx/openrouter",
            model="claude/haiku",
        ),
    )
    assert refusal is None


def test_no_bearer_is_absent(authority: PassAuthority) -> None:
    assert _code(authority, "", Ask()) == "absent"


def test_a_bearer_of_another_shape_is_malformed(authority: PassAuthority) -> None:
    assert _code(authority, "not-a-pass", Ask()) == "malformed"
    assert _code(authority, "qmx1.only-two", Ask()) == "malformed"


def test_another_authoritys_pass_fails_the_mac(authority: PassAuthority) -> None:
    other = PassAuthority(secret=b"z" * 32)
    assert _code(authority, _token(other), Ask()) == "bad_mac"


def test_a_revoked_pass_is_refused(authority: PassAuthority) -> None:
    token = _token(authority)
    minted, _ = authority.parse(token)
    authority.revocations.revoke(minted.id)
    assert _code(authority, token, Ask()) == "revoked"


def test_an_owners_end_expires_every_pass_of_the_run(authority: PassAuthority) -> None:
    token = _token(authority)
    authority.end_run("run-1")
    assert _code(authority, token, Ask(run="run-1")) == "owner_ended"


def test_a_pass_past_its_deadline_is_expired(authority: PassAuthority, clock: Clock) -> None:
    token = _token(authority)
    clock.tick(12 * 3600 + 1)
    assert _code(authority, token, Ask()) == "expired"


def test_another_placement_is_refused(authority: PassAuthority) -> None:
    assert _code(authority, _token(authority), Ask(placement="pc")) == "wrong_placement"


def test_another_attempt_is_refused(authority: PassAuthority) -> None:
    assert _code(authority, _token(authority), Ask(attempt=3)) == "wrong_attempt"


def test_another_run_is_refused(authority: PassAuthority) -> None:
    assert _code(authority, _token(authority), Ask(run="run-2")) == "wrong_run"


def test_a_read_outside_the_scope_is_refused(authority: PassAuthority) -> None:
    assert _code(authority, _token(authority), Ask(read="secrets")) == "read_scope"


def test_a_write_outside_the_prefix_is_refused(authority: PassAuthority) -> None:
    assert _code(authority, _token(authority), Ask(write="runs/run-2/x")) == "write_scope"
    # `runs/run-10` is not under `runs/run-1`: a bare prefix match would allow it.
    assert _code(authority, _token(authority), Ask(write="runs/run-10/x")) == "write_scope"


def test_a_key_outside_the_scope_is_refused(authority: PassAuthority) -> None:
    assert _code(authority, _token(authority), Ask(key="qmx/chatgpt")) == "key_scope"


def test_a_model_outside_the_scope_is_refused(authority: PassAuthority) -> None:
    assert _code(authority, _token(authority), Ask(model="claude/opus")) == "model_scope"


def test_a_helpers_pass_names_its_handle(authority: PassAuthority) -> None:
    _, bearer = authority.mint(run="run-1", placement="pc", model_scope=("*",), handle="h-1234")
    minted, refusal = authority.check(bearer, Ask(handle="h-1234"))
    assert refusal is None
    assert minted.owner == "h-1234"
    assert _code(authority, bearer, Ask(handle="h-9999")) == "handle_mismatch"


def test_a_wildcard_scope_is_not_a_cap(authority: PassAuthority) -> None:
    _, bearer = authority.mint(run="r", placement="pc", key_scope=("*",), model_scope=("*",))
    assert authority.check(bearer, Ask(key="qmx/anything", model="any/model"))[1] is None


def test_refusals_lists_every_failed_scope(authority: PassAuthority) -> None:
    token = _token(authority)
    minted, _ = authority.parse(token)
    found = authority.refusals(
        minted, Ask(run="run-2", attempt=9, placement="pc", model="claude/opus")
    )
    assert [refusal.code for refusal in found] == [
        "wrong_run",
        "wrong_attempt",
        "wrong_placement",
        "model_scope",
    ]


def test_the_revocation_list_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "revoked.json"
    first = RevocationList(path)
    first.revoke("p-1")
    first.end_run("run-1")
    again = RevocationList(path)
    assert again.holds("p-1") is True
    assert again.passes() == ("p-1",)
    assert again.runs() == ("run-1",)


def test_a_bearer_header_is_read_in_either_spelling() -> None:
    assert bearer_of("Bearer qmx1.a.b") == "qmx1.a.b"
    assert bearer_of("qmx1.a.b") == "qmx1.a.b"
    assert bearer_of("  ") == ""


def test_a_refusal_names_the_value_it_compared() -> None:
    refusal = Refusal("wrong_placement", "pass names contabo, not pc")
    assert str(refusal) == "wrong_placement: pass names contabo, not pc"
