"""Run passes (AD-41): the thing a remote attempt carries instead of a key.

A pass is one signed row that names what its bearer may do, scoped to one run, one attempt and
one placement. It is not a credential: it holds no key, no token and no account. The router reads
it as a bearer token on every request it accepts over the tailnet.

The scopes are the whole model, so they sit in one frozen type rather than in a bag of checks:

- `read_scope`   path prefixes the bearer may read (a vault entry, a journal path, `facts`)
- `write_prefix` the one path prefix it may write under
- `key_scope`    the keyring names it may ask the relay for, or `*`
- `model_scope`  the models it may call, or `*`
- `placement`    the machine it was minted for; a pass does not travel
- `handle`       the `cli` helper that owns it, empty for a run's own tools (AD-41)

Expiry has two clocks. A wall-clock deadline covers a crash, and `owner_ended` covers the honest
case: the run finished, so its passes are refused at once even if the deadline is minutes away.

Revocation is a list the routers read, not a call they make: `RevocationList` is a small file that
a router re-reads when its mtime moves, so a revoked pass stops working on a machine the PC
cannot reach right now.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Final, Literal, cast

type Code = Literal[
    "absent",
    "malformed",
    "bad_mac",
    "revoked",
    "owner_ended",
    "expired",
    "wrong_placement",
    "wrong_attempt",
    "wrong_run",
    "read_scope",
    "write_scope",
    "key_scope",
    "model_scope",
    "handle_mismatch",
]
"""Every way a pass is refused. E25 drives one request per code."""

ANY: Final = "*"
"""The wildcard in `key_scope` and `model_scope`. It is a scope, not a cap."""
DEFAULT_TTL_S: Final = 12 * 3600.0
"""A pass that outlives its run by a night still expires. The owner's end is the real clock."""
PREFIX: Final = "qmx1"
"""The wire form's version tag. A pass names its own format, so an old router refuses it whole."""
MAX_TOKEN: Final = 4096
"""A bearer longer than this is not one of ours; refusing early keeps parse cost bounded."""


@dataclass(frozen=True)
class Pass:
    """One run pass. Field names are the wire names; nothing else is carried."""

    id: str
    run: str
    attempt: int
    placement: str
    read_scope: tuple[str, ...]
    write_prefix: str
    key_scope: tuple[str, ...]
    model_scope: tuple[str, ...]
    issued_at: float
    expires_at: float
    handle: str = ""
    data_scope: tuple[str, ...] = ()

    @property
    def owner(self) -> str:
        """The journal owner: the helper's handle when it has one, else the run."""
        return self.handle or self.run


@dataclass(frozen=True)
class Ask:
    """One request a bearer wants a pass to cover. Empty fields are not asked about, which is why
    `attempt` defaults to 0 and not 1: 1 is an attempt number, and every pass would fail it."""

    run: str = ""
    attempt: int = 0
    placement: str = ""
    read: str = ""
    write: str = ""
    key: str = ""
    model: str = ""
    handle: str = ""
    data: str = ""


@dataclass(frozen=True)
class Refusal:
    """The first check that failed, and the value it compared against."""

    code: Code
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


def canonical(
    pass_id: str,
    run: str,
    attempt: int,
    placement: str,
    read_scope: tuple[str, ...],
    write_prefix: str,
    key_scope: tuple[str, ...],
    model_scope: tuple[str, ...],
    issued_at: float,
    expires_at: float,
    handle: str,
    data_scope: tuple[str, ...] = (),
    *,
    legacy: bool = False,
) -> bytes:
    """The bytes the MAC covers, in one fixed order. JSON with sorted keys and no spaces, so a
    pass minted on one Python and checked on another signs the same bytes. `legacy` leaves
    `data_scope` out, which is how a bearer minted before that field existed was signed: the
    router still reads it, and the door refuses it for holding no data scope."""
    fields: dict[str, object] = {
        "id": pass_id,
        "run": run,
        "attempt": attempt,
        "placement": placement,
        "read_scope": list(read_scope),
        "write_prefix": write_prefix,
        "key_scope": list(key_scope),
        "model_scope": list(model_scope),
        "issued_at": issued_at,
        "expires_at": expires_at,
        "handle": handle,
    }
    if not legacy:
        fields["data_scope"] = list(data_scope)
    return json.dumps(fields, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class RevocationList:
    """The list the routers read. In memory when `path` is None, else a JSON file a second
    process can rewrite: `passes` are ids, `runs` are run ids whose passes all ended."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._passes: set[str] = set()
        self._runs: set[str] = set()
        self._stamp = (-1.0, -1)
        self._load()

    def _load(self) -> None:
        path = self.path
        if path is None:
            return
        try:
            stat = path.stat()
        except OSError:
            return
        stamp = (stat.st_mtime, stat.st_size)
        if stamp == self._stamp:
            return
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except OSError, ValueError:
            return
        self._passes = {str(item) for item in document.get("passes", [])}
        self._runs = {str(item) for item in document.get("runs", [])}
        self._stamp = stamp

    def _save(self) -> None:
        path = self.path
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"passes": sorted(self._passes), "runs": sorted(self._runs)}),
            encoding="utf-8",
        )
        os.replace(temporary, path)

    def revoke(self, pass_id: str) -> None:
        self._passes.add(pass_id)
        self._save()

    def end_run(self, run_id: str) -> None:
        """Every pass of `run_id`, and every pass later minted for it, is refused from now on."""
        self._runs.add(run_id)
        self._save()

    def passes(self) -> tuple[str, ...]:
        self._load()
        return tuple(sorted(self._passes))

    def runs(self) -> tuple[str, ...]:
        self._load()
        return tuple(sorted(self._runs))

    def holds(self, pass_id: str) -> bool:
        """True when this pass id was revoked. A run's end is not a revocation: it reads
        `owner_ended`, which is the honest name for it in a journal."""
        self._load()
        return pass_id in self._passes


@dataclass
class PassAuthority:
    """Mints and checks passes for one host. The secret never leaves this object and is printed
    as a fingerprint only; a second site verifies by asking the minting site, or by holding the
    same secret from the vault (AD-41)."""

    secret: bytes = field(default_factory=lambda: os.urandom(32))
    revocations: RevocationList = field(default_factory=RevocationList)
    clock: Callable[[], float] = time.time

    def _now(self) -> float:
        return float(self.clock())

    def fingerprint(self) -> str:
        return hashlib.sha256(self.secret).hexdigest()[:16]

    def mint(
        self,
        *,
        run: str,
        placement: str,
        attempt: int = 1,
        read_scope: tuple[str, ...] = (),
        write_prefix: str = "",
        key_scope: tuple[str, ...] = (),
        model_scope: tuple[str, ...] = (),
        data_scope: tuple[str, ...] = (),
        handle: str = "",
        ttl_s: float = DEFAULT_TTL_S,
        pass_id: str = "",
    ) -> tuple[Pass, str]:
        """One pass and its bearer. The id is random when the caller does not name one, so two
        passes of one run stay distinguishable in a journal."""
        now = self._now()
        minted = Pass(
            id=pass_id or _b64(os.urandom(12)),
            run=run,
            attempt=int(attempt),
            placement=placement,
            read_scope=tuple(read_scope),
            write_prefix=write_prefix,
            key_scope=tuple(key_scope),
            model_scope=tuple(model_scope),
            issued_at=now,
            expires_at=now + float(ttl_s),
            handle=handle,
            data_scope=tuple(str(item) for item in data_scope),
        )
        return minted, self.bearer(minted)

    def bearer(self, minted: Pass) -> str:
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
            minted.data_scope,
        )
        mac = hmac.new(self.secret, body, hashlib.sha256).digest()
        return f"{PREFIX}.{_b64(body)}.{_b64(mac)}"

    def parse(self, token: str) -> tuple[Pass, Refusal | None]:
        """The pass a bearer names, or the refusal its first failing check gives. Parsing is a
        boundary: every field is type-checked here, and nothing downstream trusts the token."""
        if not token:
            return _blank(), Refusal("absent", "no bearer was presented")
        if len(token) > MAX_TOKEN:
            return _blank(), Refusal("malformed", f"a bearer longer than {MAX_TOKEN} bytes")
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != PREFIX:
            return _blank(), Refusal("malformed", f"not a {PREFIX} bearer")
        try:
            body = _unb64(parts[1])
            mac = _unb64(parts[2])
            document = json.loads(body)
        except ValueError, TypeError, json.JSONDecodeError:
            return _blank(), Refusal("malformed", "the bearer does not decode")
        if not isinstance(document, dict):
            return _blank(), Refusal("malformed", "the bearer is not an object")
        data = cast("dict[str, Any]", document)
        wanted = hmac.new(self.secret, body, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, wanted):
            # A pass minted before `data_scope` existed signed the same fields without it. It
            # still verifies, and it carries no data scope, so the door refuses it by name.
            stripped = {key: value for key, value in data.items() if key != "data_scope"}
            legacy = json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")
            if not hmac.compare_digest(mac, hmac.new(self.secret, legacy, hashlib.sha256).digest()):
                return _blank(), Refusal("bad_mac", "the bearer was not signed by this router")
        try:
            minted = Pass(
                id=str(data["id"]),
                run=str(data["run"]),
                attempt=int(data["attempt"]),
                placement=str(data["placement"]),
                read_scope=tuple(str(item) for item in data["read_scope"]),
                write_prefix=str(data["write_prefix"]),
                key_scope=tuple(str(item) for item in data["key_scope"]),
                model_scope=tuple(str(item) for item in data["model_scope"]),
                issued_at=float(data["issued_at"]),
                expires_at=float(data["expires_at"]),
                handle=str(data.get("handle", "")),
                data_scope=tuple(str(item) for item in data.get("data_scope", ())),
            )
        except KeyError, TypeError, ValueError:
            return _blank(), Refusal("malformed", "the bearer is missing a scope")
        return minted, None

    def check(self, token: str, ask: Ask) -> tuple[Pass, Refusal | None]:
        """Parse and then run every scope check in one fixed order. The first refusal is the
        answer; a caller that wants the whole list uses `refusals`."""
        minted, refused = self.parse(token)
        if refused is not None:
            return minted, refused
        for refusal in self.refusals(minted, ask):
            return minted, refusal
        return minted, None

    def refusals(self, minted: Pass, ask: Ask) -> tuple[Refusal, ...]:
        """Every check that fails, in the order a router reports them. A list rather than one
        refusal, because E25 asks each scope separately and a lane reads them all."""
        now = self._now()
        found: list[Refusal] = []
        if self.revocations.holds(minted.id):
            found.append(Refusal("revoked", f"pass {minted.id} was revoked"))
        if minted.run in self.revocations.runs():
            found.append(Refusal("owner_ended", f"run {minted.run} ended"))
        if now >= minted.expires_at:
            found.append(Refusal("expired", f"expired at {minted.expires_at:.0f}, now {now:.0f}"))
        if ask.run and ask.run != minted.run:
            found.append(Refusal("wrong_run", f"pass names {minted.run}, not {ask.run}"))
        if ask.attempt and ask.attempt != minted.attempt:
            found.append(
                Refusal("wrong_attempt", f"pass names attempt {minted.attempt}, not {ask.attempt}")
            )
        if ask.placement and ask.placement != minted.placement:
            found.append(
                Refusal(
                    "wrong_placement",
                    f"pass names {minted.placement}, not {ask.placement}",
                )
            )
        if ask.handle and ask.handle != minted.handle:
            found.append(
                Refusal(
                    "handle_mismatch",
                    f"pass names helper {minted.handle or 'none'}, not {ask.handle}",
                )
            )
        if ask.read and not _readable(minted.read_scope, ask.read):
            found.append(Refusal("read_scope", f"{minted.read_scope} does not cover {ask.read}"))
        if ask.write and not _under(minted.write_prefix, ask.write):
            found.append(
                Refusal("write_scope", f"{minted.write_prefix!r} does not cover {ask.write}")
            )
        if ask.key and not _scoped(minted.key_scope, ask.key):
            found.append(Refusal("key_scope", f"{minted.key_scope} does not cover {ask.key}"))
        if ask.model and not _scoped(minted.model_scope, ask.model):
            found.append(Refusal("model_scope", f"{minted.model_scope} does not cover {ask.model}"))
        if ask.data and not _scoped(minted.data_scope, ask.data):
            found.append(
                Refusal(
                    "data_scope",
                    f"{minted.data_scope or 'no data scope'} does not cover {ask.data}",
                )
            )
        return tuple(found)

    def end_run(self, run_id: str) -> None:
        """The run finished or was stopped: its passes are refused before their deadline."""
        self.revocations.end_run(run_id)


def bearer_of(value: str) -> str:
    """The token out of an `Authorization` header value, or `""`. One spelling, because a pass
    that arrives as `Bearer qmx1.x.y` and one that arrives bare are the same pass."""
    text = value.strip()
    if text.lower().startswith("bearer "):
        return text[7:].strip()
    return text


def _blank() -> Pass:
    return Pass(
        id="",
        run="",
        attempt=0,
        placement="",
        read_scope=(),
        write_prefix="",
        key_scope=(),
        model_scope=(),
        issued_at=0.0,
        expires_at=0.0,
        data_scope=(),
    )


def _readable(scope: tuple[str, ...], path: str) -> bool:
    return any(prefix == "" or _under(prefix, path) for prefix in scope)


def _under(prefix: str, path: str) -> bool:
    """`prefix` covers `path` when they are equal or `path` continues it past a separator. A bare
    `starts with` would let `runs/1` cover `runs/10`, so the separator is part of the rule."""
    if prefix == "":
        return True
    if path == prefix:
        return True
    return path.startswith(prefix.rstrip("/") + "/")


def _scoped(scope: tuple[str, ...], name: str) -> bool:
    return ANY in scope or name in scope


def with_handle(minted: Pass, handle: str) -> Pass:
    """The same pass, owned by a helper's handle. Used where a grant is handed to a `cli` helper:
    the pass is re-minted rather than edited, because its MAC covers the handle (AD-41)."""
    return replace(minted, handle=handle)
