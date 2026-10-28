"""The storage kinds of the connect dialog (design 06 section 9): another drive or folder, Google
Drive, Cloudflare R2, his server over SFTP, and any other storage rclone reaches.

A folder needs no rclone, so it connects offline (I1). Every rclone kind runs rclone's own
question loop (`config create <remote> <type> --non-interactive --all`): QMX answers what it
knows, and each question it cannot answer becomes one card built from the question's parsed
fields only. Every answer reaches rclone as `RCLONE_RESULT` in that one call's environment, and
an `IsPassword` answer comes from the key route and is obscured first, so no answer is ever in a
command line. A sign-in (Google Drive, or any kind rclone signs in to with a browser) is its own
long job, `rclone authorize <type> --auth-no-open-browser`, whose card shows rclone's
`127.0.0.1` link; QMX never opens a browser.

A remote QMX makes is named `qmx_<id>` and carries `description = qmx-pending <place>` until its
loop ends, then `qmx <place>`, so a rerun after a kill finds it and a half-made one is made anew.
The test writes, reads and removes one small file under `QMX-backup/`. The row is written last:
`via`, `can = ["keep"]`, and the folder's `path` or the remote's `remote`, `type` and `root`
(copies go to `<path or root>/QMX-backup/<home_id>/`, or to `<root>/<home_id>/` when the path or
root is itself named `QMX-backup`). A name another place holds, and a second row on the same
folder or the same remote type and root, are refused before anything is written.
"""

from __future__ import annotations

import json
import re
import secrets
import shutil
import threading
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path, PurePath
from typing import Any, Final, cast

from qmx_home.backup.plan import FOLDER, proposal
from qmx_home.files import plain

from qmx_host.connect import Card, Kind, Rows, Run, Step, placement, same_folder, write_row
from qmx_host.jobs import Progress, Stopped

CROCKFORD: Final = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
LINK: Final = re.compile(r"http://127\.0\.0\.1:\d+/auth\?state=[A-Za-z0-9_-]+")
TOKEN: Final = re.compile(r"--->\s*(\{.*?\})\s*<---End paste", re.DOTALL)
TYPE: Final = re.compile(r"[a-z][a-z0-9]*")
LINK_WAIT_S: Final = 30.0
"""How long a sign-in job may take to show rclone's link before the card says it did not; a
bound on one rclone start, not a limit on him."""
ALWAYS: Final[Mapping[str, str]] = {"config_is_local": "false", "config_fs_advanced": "false"}
"""Answers QMX gives every loop: never a browser rclone opens itself, and no advanced options."""
DRIVE_CLIENT: Final = (
    "Google Drive needs a Google Cloud client of type Desktop app until QMX ships its own. Making "
    'one takes about ten minutes in the Google Cloud console; set it to "In production", or Google '
    "ends the sign-in after 7 days. Paste its client id and secret here, or connect another drive "
    "or your server instead."
)


def mint() -> str:
    """A new place id: 26 characters, ordered by time (a ULID drawn from a UUIDv7)."""
    value = uuid.uuid7().int
    return "".join(CROCKFORD[(value >> (5 * i)) & 31] for i in reversed(range(26)))


def remote_name(ident: str) -> str:
    """A remote QMX made, named so rclone's per-remote variables reach it."""
    return f"qmx_{ident.lower()}"


def holder(root: str) -> str:
    """The folder under a storage's root where `<home_id>/` folders go."""
    trimmed = root.strip().rstrip("/\\")
    if PurePath(trimmed or ".").name.casefold() == FOLDER.casefold():
        return trimmed
    return f"{trimmed}/{FOLDER}" if trimmed else FOLDER


def _rows(run: Run) -> Rows:
    control = run.world.control
    return {} if control is None else placement(control)


def _taken(
    place: str, rows: Rows, same: Callable[[Mapping[str, object]], bool], where: str
) -> str | None:
    """Refuse a name another place holds, and a second row on the same target."""
    for name, row in rows.items():
        if name != place and same(row):
            return (
                f"the storage {name} already keeps copies at {where}; use {name}, or choose "
                "another folder there"
            )
    held = rows.get(place)
    if held is not None and not same(held):
        return (
            f"the name {place} is taken by another place in Settings; choose another name for "
            f"the storage at {where}"
        )
    return None


# Another drive or folder.


def _path(run: Run) -> Path | None:
    typed = run.fields().get("path")
    if typed:
        return Path(typed)
    held = _rows(run).get(run.place, {})
    found = held.get("path")
    return Path(found) if held.get("via") == "folder" and isinstance(found, str) else None


def _same_path(path: Path) -> Callable[[Mapping[str, object]], bool]:
    def same(row: Mapping[str, object]) -> bool:
        found = row.get("path")
        return (
            row.get("via") == "folder" and isinstance(found, str) and same_folder(Path(found), path)
        )

    return same


def _folder_refusal(run: Run) -> str | None:
    path = _path(run)
    if path is None:
        return None
    if not path.is_absolute():
        return (
            f"{run.place}: {path} is not a full folder path; name one such as E:\\ or "
            "E:\\QMX-backup"
        )
    root = run.world.layout.root.resolve()
    if path.resolve().is_relative_to(root):
        return (
            f"{run.place}: {plain(path)} is inside the QMX folder {plain(root)}, so a copy there "
            "is lost with the folder; choose a folder on another drive"
        )
    return _taken(run.place, _rows(run), _same_path(path), plain(path))


def _folder_card(run: Run) -> Card:
    offered = proposal(run.world.layout)
    examples = [] if offered is None else [{"Value": str(offered.path), "Help": offered.line}]
    return Card(
        "folder",
        f"{run.place}: choose the drive or folder where QMX keeps copies of your work",
        (
            {
                "Name": "path",
                "Help": "A drive or a folder on one, such as E:\\",
                "Examples": examples,
                "Type": "string",
            },
        ),
    )


def _folder_checked(run: Run) -> Card | None:
    path = _path(run)
    if path is None:
        return _folder_card(run)
    refused = _folder_refusal(run)
    if refused is not None:
        raise Stopped(refused)
    if not path.is_dir():
        raise Stopped(
            f"{run.place}: {plain(path)} is not there (is its drive plugged in?); plug it in or "
            "choose another folder"
        )
    run.facts["path"] = path
    if (
        PurePath(path.resolve()).drive.casefold()
        == PurePath(run.world.layout.root.resolve()).drive.casefold()
    ):
        run.say(
            f"{run.place}: {plain(path)} is on the same drive as your QMX folder, so a copy there "
            "is lost with that drive; another drive keeps it safer"
        )
    else:
        run.say(f"{run.place}: {plain(path)} is on another drive")
    return None


def _folder_connected(run: Run) -> bool:
    path = run.facts.get("path")
    held = _rows(run).get(run.place)
    found = held is not None and isinstance(path, Path) and _same_path(path)(held)
    if found:
        run.facts["before"] = True
    return found


def _folder_test(run: Run) -> Card | None:
    path = cast("Path", run.facts["path"])
    box = path / FOLDER if path.name.casefold() != FOLDER.casefold() else path
    made = not box.exists()
    body = secrets.token_bytes(64)
    try:
        free = shutil.disk_usage(path).free
        box.mkdir(exist_ok=True)
        probe = box / f".qmx-test-{secrets.token_hex(4)}"
        probe.write_bytes(body)
        back = probe.read_bytes()
        probe.unlink()
        if made:
            box.rmdir()
    except OSError as error:
        raise Stopped(
            f"{run.place}: {plain(path)} could not be written ({error.strerror}); check the drive "
            "and that QMX may write there"
        ) from None
    if back != body:
        raise Stopped(
            f"{run.place}: {plain(path)} gave back other bytes than it took; check the drive"
        )
    run.say(
        f"{run.place}: {plain(path)} took a small file, gave it back and let it go; "
        f"{_gb(free)} free"
    )
    return None


def _folder_row(run: Run) -> Card | None:
    path = cast("Path", run.facts["path"])
    ident = mint()
    row = {"id": ident, "via": "folder", "can": ["keep"], "path": str(path)}
    _write(run, row, lambda rows: _taken(run.place, rows, _same_path(path), plain(path)))
    return None


def _folder_source(run: Run) -> dict[str, object]:
    return {"kind": "folder", "path": str(run.facts["path"])}


# The rclone kinds.


class Loop:
    """What one rclone kind adds to the shared steps: the remote's type, what QMX answers and
    prefills, the fields his first card asks, a key it needs, and the extra row fields."""

    def __init__(
        self,
        kind: str,
        name: str,
        *,
        type_: str | None,
        asks: tuple[tuple[str, str, bool], ...],
        answers: Callable[[Mapping[str, str]], Mapping[str, str]] = lambda _f: {},
        prefill: Callable[[Mapping[str, str]], Mapping[str, str]] = lambda _f: {},
        key: tuple[str, str, str] | None = None,
        row: Callable[[Mapping[str, str]], Mapping[str, object]] = lambda _f: {},
        intro: str = "",
        client: Callable[[Mapping[str, str]], Mapping[str, str]] = lambda _f: {},
    ) -> None:
        self.kind = kind
        self.name = name
        self.type = type_
        self.asks = asks
        """His first card's fields: (name, help, required)."""
        self.answers = answers
        self.prefill = prefill
        self.key = key
        """(option, key name with `{place}`, the card's line) for a key the conf never holds."""
        self.row = row
        self.intro = intro
        self.client = client
        """The variables a sign-in hands `rclone authorize`."""

    def type_of(self, fields: Mapping[str, str]) -> str:
        return self.type or fields.get("type", "")

    def reference(self, place: str) -> str | None:
        return None if self.key is None else self.key[1].format(place=place)


def _loop_of(run: Run) -> Loop:
    return LOOPS[run.kind.id]


def _given(run: Run) -> dict[str, str]:
    """His first card's answers, or the row's when the place is already connected."""
    fields = run.fields()
    held = _rows(run).get(run.place, {})
    if held.get("via") == "rclone":
        for name in ("type", "root", "client_id", "client_secret"):
            value = held.get(name)
            if isinstance(value, str) and name not in fields:
                fields[name] = value
    return fields


def _asked_all(run: Run) -> bool:
    loop = _loop_of(run)
    fields = _given(run)
    return all(fields.get(name) for name, _help, required in loop.asks if required)


def _fields_card(run: Run) -> Card | None:
    loop = _loop_of(run)
    refused = _rclone_refusal(run)
    if refused is not None:
        raise Stopped(refused)
    if _asked_all(run):
        return None
    return Card(
        "fields",
        loop.intro or f"{run.place}: tell QMX where the {loop.name} storage is",
        tuple(
            {"Name": name, "Help": text, "Examples": [], "Type": "string"}
            for name, text, _r in loop.asks
        ),
    )


def _target(run: Run) -> tuple[str, str]:
    fields = _given(run)
    return _loop_of(run).type_of(fields), fields.get("root") or FOLDER


def _same_remote(kind: str, root: str) -> Callable[[Mapping[str, object]], bool]:
    def same(row: Mapping[str, object]) -> bool:
        return row.get("via") == "rclone" and row.get("type") == kind and row.get("root") == root

    return same


def _rclone_refusal(run: Run) -> str | None:
    loop = _loop_of(run)
    fields = _given(run)
    kind = loop.type_of(fields)
    if not kind:
        return None
    if not TYPE.fullmatch(kind):
        return (
            f"{run.place}: {kind!r} is not an rclone storage type; use one rclone names, such as s3"
        )
    root = fields.get("root") or FOLDER
    return _taken(run.place, _rows(run), _same_remote(kind, root), f"{kind}:{root}")


def _rclone_found(run: Run) -> bool:
    return run.world.rclone.found() is not None


def _rclone_get(run: Run) -> Card | None:
    binary = run.world.rclone.binary()
    run.say(f"{run.place}: rclone is ready at {plain(binary)}")
    return None


def _key_set(run: Run) -> bool:
    reference = _loop_of(run).reference(run.place)
    return reference is None or run.world.keys.read(reference) is not None


def _key_card(run: Run) -> Card | None:
    loop = _loop_of(run)
    assert loop.key is not None  # noqa: S101 - _key_set passes for a kind with no key
    return Card("secret", f"{run.place}: {loop.key[2]}", key=loop.key[1].format(place=run.place))


def _secrets(run: Run, remote: str) -> dict[str, str]:
    loop = _loop_of(run)
    reference = loop.reference(run.place)
    if loop.key is None or reference is None:
        return {}
    return run.world.rclone.secrets_for(remote, loop.key[0], reference)


def _ours(run: Run) -> tuple[str, bool] | None:
    """The remote QMX made for this place, and whether its loop ended."""
    ran = run.world.rclone.run(["config", "dump"])
    if ran.code:
        raise Stopped(f"{run.place}: the storages' settings on this PC {ran.line}")
    if ran.line:
        run.say(ran.line)
    remotes = cast("dict[str, Any]", json.loads(ran.out or "{}"))
    for name, options in remotes.items():
        described = cast("dict[str, Any]", options).get("description")
        if described == f"qmx {run.place}":
            return name, True
        if described == f"qmx-pending {run.place}":
            return name, False
    return None


def _remote_made(run: Run) -> bool:
    ours = _ours(run)
    run.facts["ours"] = ours
    if ours is not None and ours[1]:
        run.facts["remote"] = ours[0]
        return True
    return False


def _remote_loop(run: Run) -> Card | None:
    rclone = run.world.rclone
    signing = run.world.jobs.get(str(run.memory.get("sign_in", "")))
    if signing is not None and signing.state == "running":
        return _sign_in_card(run, str(run.memory.get("link", "")), signing.id)
    ours = cast("tuple[str, bool] | None", run.facts.get("ours"))
    asked = cast("dict[str, Any] | None", run.memory.get("question"))
    state = run.answer.get("state")
    if (
        ours is not None
        and asked is not None
        and isinstance(state, str)
        and state == asked["state"]
    ):
        value, password = _answer_of(run, cast("dict[str, Any]", asked["option"]))
        if value is None:
            return _question(run, state, cast("dict[str, Any]", asked["option"]), "")
        ran = rclone.run(
            _update(ours[0], state), answer=value, password=password, secrets=_secrets(run, ours[0])
        )
        return _walk(run, ours[0], ran)
    if ours is not None:
        rclone.run(["config", "delete", ours[0]])
    name = remote_name(run.memory.setdefault("id", mint()))
    fields = _given(run)
    loop = _loop_of(run)
    prefill = [f"{k}={v}" for k, v in loop.prefill(fields).items()]
    ran = rclone.run(
        [
            "config",
            "create",
            name,
            loop.type_of(fields),
            "--non-interactive",
            "--all",
            f"description=qmx-pending {run.place}",
            *prefill,
        ],
        secrets=_secrets(run, name),
    )
    return _walk(run, name, ran)


def _update(name: str, state: str) -> list[str]:
    return ["config", "update", name, "--continue", "--non-interactive", "--state", state]


def _answer_of(run: Run, option: Mapping[str, Any]) -> tuple[str | None, bool]:
    """His answer to the pending question: a key read from the key store for a password, the
    question's own default for an empty answer."""
    if option.get("IsPassword"):
        expected = _secret_name(run.place, str(option.get("Name")))
        if run.answer.get("key") != expected:
            return None, True
        return run.world.keys.read(expected), True
    result = run.answer.get("result")
    if isinstance(result, str) and result != "":
        return result, False
    return str(option.get("DefaultStr") or ""), False


def _secret_name(place: str, option: str) -> str:
    return f"qmx/connect/{place}/{option}"


def _automatic(run: Run, option: Mapping[str, Any]) -> str | None:
    name = str(option.get("Name"))
    fields = _given(run)
    loop = _loop_of(run)
    known = {**ALWAYS, **loop.prefill(fields), **loop.answers(fields)}
    return known.get(name)


def _walk(run: Run, name: str, ran: Any) -> Card | None:
    """Follow rclone's loop from `ran` until it ends or asks what only he can answer."""
    rclone = run.world.rclone
    while True:
        if ran.code:
            raise Stopped(
                f"{run.place}: rclone did not take the storage's settings; the storage {ran.line}"
            )
        out = cast("dict[str, Any]", json.loads(ran.out) if ran.out.strip() else {})
        state = str(out.get("State") or "")
        if not state:
            rclone.run(
                ["config", "update", name, f"description=qmx {run.place}", "--non-interactive"]
            )
            run.memory.pop("question", None)
            run.facts["remote"] = name
            run.say(f"{run.place}: its settings are kept on this PC, protected, in rclone.conf")
            return None
        option = cast("dict[str, Any]", out.get("Option") or {})
        if option.get("Name") == "config_token":
            return _sign_in(run, name, state)
        automatic = _automatic(run, option)
        if automatic is not None:
            ran = rclone.run(
                _update(name, state),
                answer=automatic,
                password=bool(option.get("IsPassword")),
                secrets=_secrets(run, name),
            )
            continue
        run.memory["question"] = {"state": state, "option": option}
        return _question(run, state, option, str(out.get("Error") or ""))


def _question(run: Run, state: str, option: Mapping[str, Any], error: str) -> Card:
    asked = str(option.get("Name", ""))
    examples = cast("list[dict[str, Any]]", option.get("Examples") or [])
    shown = {
        "Name": asked,
        "Help": str(option.get("Help", "")),
        "Examples": [
            {"Value": str(e.get("Value", "")), "Help": str(e.get("Help", ""))} for e in examples
        ],
        "Type": str(option.get("Type", "")),
    }
    again = " rclone did not accept the last answer; check it and answer again." if error else ""
    if option.get("IsPassword"):
        key = _secret_name(run.place, asked)
        return Card(
            "secret",
            f"{run.place}: rclone asks for {asked}. Write it to the key {key}, then answer "
            f"with that key; it never leaves this PC.{again}",
            (shown,),
            state=state,
            key=key,
        )
    return Card("question", f"{run.place}: rclone asks for {asked}.{again}", (shown,), state=state)


def _sign_in(run: Run, name: str, state: str) -> Card:
    world = run.world
    loop = _loop_of(run)
    running = world.jobs.get(str(run.memory.get("sign_in", "")))
    if running is not None and running.state == "running":
        return _sign_in_card(run, str(run.memory.get("link", "")), running.id)
    shown = threading.Event()
    found: dict[str, str] = {}
    stop = threading.Event()
    kind = loop.type_of(_given(run))
    client = loop.client(_given(run))

    def watch(message: str) -> None:
        link = LINK.search(message)
        if link is not None and "link" not in found:
            found["link"] = link.group(0)
            shown.set()

    def work(progress: Progress) -> Mapping[str, object]:
        progress("waiting for you to sign in")
        try:
            ran = world.rclone.run(
                ["authorize", kind, "--auth-no-open-browser"],
                secrets=client,
                watch=watch,
                cancel=stop,
            )
        finally:
            shown.set()
        if stop.is_set():
            raise Stopped(f"{run.place}: the sign-in was stopped; nothing was connected")
        token = TOKEN.search(ran.out)
        if ran.code or token is None:
            raise Stopped(
                f"{run.place}: the sign-in did not finish; the storage "
                f"{ran.line or 'gave no sign-in'}"
            )
        progress("keeping the sign-in")
        signed = world.rclone.run(_update(name, state), answer=token.group(1))
        more = _walk(run, name, signed)
        if more is not None:
            return {
                "line": f"{run.place}: signed in; rclone has one more question",
                "needs": more.document(),
            }
        return {"line": f"{run.place}: signed in"}

    started = world.jobs.start(f"sign-in:{run.place}", work)
    world.cancels[started.job.id] = stop
    run.memory["sign_in"] = started.job.id
    shown.wait(LINK_WAIT_S)
    link = found.get("link", "")
    if not link:
        stop.set()
        raise Stopped(f"{run.place}: rclone did not show its sign-in link; try again")
    run.memory["link"] = link
    return _sign_in_card(run, link, started.job.id)


def _sign_in_card(run: Run, link: str, job: str) -> Card:
    return Card(
        "sign-in",
        f"{run.place}: open this link on this PC and sign in to {_loop_of(run).name}; QMX carries "
        "on when you are done. Then answer this card again.",
        link=link,
        job=job,
    )


def _rclone_connected(run: Run) -> bool:
    kind, root = _target(run)
    remote = run.facts.get("remote")
    held = _rows(run).get(run.place)
    found = held is not None and _same_remote(kind, root)(held) and held.get("remote") == remote
    if found:
        run.facts["before"] = True
    return found


def _rclone_test(run: Run) -> Card | None:
    rclone = run.world.rclone
    remote = cast("str", run.facts["remote"])
    _kind, root = _target(run)
    given = _secrets(run, remote)
    about = rclone.run(["about", f"{remote}:{root}", "--json"], secrets=given)
    free = (
        cast("dict[str, Any]", json.loads(about.out)).get("free")
        if about.code == 0 and about.out.strip()
        else None
    )
    probe = f"{remote}:{holder(root)}/.qmx-test-{secrets.token_hex(4)}"
    local = run.world.layout.cache / f"connect-test-{secrets.token_hex(4)}"
    local.parent.mkdir(parents=True, exist_ok=True)
    body = secrets.token_hex(32)
    local.write_text(body, encoding="utf-8")
    try:
        put = rclone.run(["copyto", str(local), probe], secrets=given)
        back = rclone.run(["cat", probe], secrets=given) if put.code == 0 else put
        gone = rclone.run(["deletefile", probe], secrets=given) if put.code == 0 else put
    finally:
        local.unlink(missing_ok=True)
    for ran in (put, back, gone):
        if ran.code:
            raise Stopped(f"{run.place}: the storage {ran.line}")
    if back.out != body:
        raise Stopped(f"{run.place}: the storage gave back other bytes than it took; check it")
    room = f"; {_gb(int(free))} free" if isinstance(free, int) else ""
    run.say(
        f"{run.place}: the storage took a small file under {holder(root)}, gave it back and let "
        f"it go{room}"
    )
    return None


def _rclone_row(run: Run) -> Card | None:
    loop = _loop_of(run)
    fields = _given(run)
    kind, root = _target(run)
    held = _rows(run).get(run.place, {})
    ident = str(run.memory.get("id") or held.get("id") or mint())
    row: dict[str, object] = {
        "id": ident,
        "via": "rclone",
        "can": ["keep"],
        "remote": run.facts["remote"],
        "type": kind,
        "root": root,
        **loop.row(fields),
    }
    reference = loop.reference(run.place)
    if reference is not None:
        row["credential_ref"] = reference
    _write(
        run, row, lambda rows: _taken(run.place, rows, _same_remote(kind, root), f"{kind}:{root}")
    )
    return None


def _rclone_source(run: Run) -> dict[str, object]:
    _kind, root = _target(run)
    return {"kind": "rclone", "remote": run.facts["remote"], "path": root}


# Shared by every storage kind.


def _write(run: Run, row: Mapping[str, object], refusal: Callable[[Rows], str | None]) -> None:
    control = run.world.control
    if control is None:
        return
    held = placement(control).get(run.place)
    if held is not None and held.get("id"):
        row = {**row, "id": held["id"]}
    wrote = write_row(control, run.place, row, refusal)
    run.facts["id"] = row["id"]
    run.say(
        f"{run.place}: added to your storages"
        if wrote
        else f"{run.place}: already in your storages"
    )


def _sync_started(run: Run) -> bool:
    return bool(run.facts.get("before"))


def _first_sync(run: Run) -> Card | None:
    start = run.world.first_sync
    if start is None:
        return None
    run.say(f"{run.place}: {start(str(run.facts['id']))}")
    return None


def _never(_run: Run) -> bool:
    return False


def _gb(count: int) -> str:
    return f"{count / (1 << 30):.1f} GB"


FOLDER_KIND: Final = Kind(
    "folder",
    "Another drive or folder",
    ("keep",),
    False,
    (
        Step("folder", "his", _never, _folder_checked),
        Step("test", "qmx", _folder_connected, _folder_test),
        Step("row", "qmx", _folder_connected, _folder_row),
        Step("first-sync", "qmx", _sync_started, _first_sync),
    ),
    source=_folder_source,
    refusal=_folder_refusal,
)


def _rclone_kind(loop: Loop) -> Kind:
    key = (Step("key", "his", _key_set, _key_card),) if loop.key is not None else ()
    return Kind(
        loop.kind,
        loop.name,
        ("keep",),
        True,
        (
            Step("storage", "his", _never, _fields_card),
            *key,
            Step("rclone", "qmx", _rclone_found, _rclone_get),
            Step("remote", "his", _remote_made, _remote_loop),
            Step("test", "qmx", _rclone_connected, _rclone_test),
            Step("row", "qmx", _rclone_connected, _rclone_row),
            Step("first-sync", "qmx", _sync_started, _first_sync),
        ),
        source=_rclone_source,
        refusal=_rclone_refusal,
    )


ROOT: Final = (
    "root",
    "The folder on that storage where QMX keeps copies; QMX-backup by default",
    False,
)
LOOPS: Final[Mapping[str, Loop]] = {
    loop.kind: loop
    for loop in (
        Loop(
            "drive",
            "Google Drive",
            type_="drive",
            asks=(
                (
                    "client_id",
                    "Your Desktop app client's id, ending in .apps.googleusercontent.com",
                    True,
                ),
                ("client_secret", "Your Desktop app client's secret", True),
                ROOT,
            ),
            answers=lambda f: {
                "client_id": f.get("client_id", ""),
                "client_secret": f.get("client_secret", ""),
                "scope": "drive.file",
                "service_account_file": "",
                "config_change_team_drive": "false",
            },
            row=lambda f: {
                "client_id": f.get("client_id", ""),
                "client_secret": f.get("client_secret", ""),
            },
            intro=DRIVE_CLIENT,
            client=lambda f: {
                "RCLONE_DRIVE_CLIENT_ID": f.get("client_id", ""),
                "RCLONE_DRIVE_CLIENT_SECRET": f.get("client_secret", ""),
            },
        ),
        Loop(
            "r2",
            "Cloudflare R2",
            type_="s3",
            asks=(("root", "Your R2 bucket's name, and a folder in it if you like", True),),
            answers=lambda _f: {"secret_access_key": ""},
            prefill=lambda _f: {
                "provider": "Cloudflare",
                "env_auth": "false",
                "no_check_bucket": "true",
            },
            key=(
                "secret_access_key",
                "qmx/r2-{place}",
                "paste your R2 secret access key through the key route; it is kept in Credential "
                "Manager, reaches rclone only while it runs, and never leaves this PC",
            ),
        ),
        Loop(
            "sftp",
            "your server",
            type_="sftp",
            asks=(
                ("host", "The server's name or address, such as myserver", True),
                ("user", "The user QMX signs in as there", False),
                (
                    "key_file",
                    "A key file in your QMX folder's keys/, if the server uses one",
                    False,
                ),
                ("root", "The folder on the server where QMX keeps copies, such as /srv/qmx", True),
            ),
            prefill=lambda f: {k: f[k] for k in ("host", "user", "key_file") if f.get(k)},
        ),
        Loop(
            "rclone",
            "another storage",
            type_=None,
            asks=(("type", "The rclone storage type, such as onedrive, b2 or local", True), ROOT),
        ),
    )
}
STORAGE: Final = (FOLDER_KIND, *(_rclone_kind(loop) for loop in LOOPS.values()))
"""The storage kinds, in the order the dialog offers them."""
