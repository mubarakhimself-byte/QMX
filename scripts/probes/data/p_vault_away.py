"""P-VAULT-AWAY, the model-key half (W6, acceptance): with the PC switched off, a restarted server
opens its own model keys from its own key file and the relay serves a model call (AD-28, N5, F30).

Two scratch homes, `pc` and `server`, on one root under `D:/Temp`. The PC seals a model-provider row
for both machines and writes the sync document; the PC's objects are then dropped, so nothing on
the server can reach them. The server is built again from two files alone: its key file at
`<home>/.qmx/vault.key` and the sync document. It opens its own share and its relay answers a model
call from a stub upstream, which is the whole of this half. No real key is read: the value is the
lane's own, and no provider is called.

Then the key file is left out and the same lookup must raise `vault:unavailable:contabo` instead of
waiting for another host.

The W13 half adds a server-homed data connection. Its data key is installed on the PC, sealed for
the server, handed over in the sync document, and opened on the server from its own key file with
the PC's objects gone. The connection's health check then runs against a stub provider answer and
reads `ok` (AD-67).

**Pass:** the server opens the entry with the key in its own key file, the relay serves a model call
with it as the bearer, a missing key file raises `vault:unavailable:contabo`, and the server-homed
data connection's health check reads `ok` with the PC off.
**Fail:** the server cannot open without the PC, the relay makes no call, a missing key file
waits or fails without the incident code, or the data connection's health walk cannot run.

    uv run --no-sync python scripts/probes/data/p_vault_away.py
    uv run --no-sync python scripts/probes/data/p_vault_away.py --keep
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from email.utils import formatdate
from pathlib import Path
from typing import Final

import httpx

from common import Report

from qmx_broker.models import Broker, Connection
from qmx_broker.providers.http import Response
from qmx_broker.registry import probe_for, walk

from qmx_router.ids import SessionId
from qmx_router.profiles import ProfileName, parse_profiles
from qmx_router.relay import Relay, RelayUsage
from qmx_router.vault import (
    MemorySource,
    Vault,
    VaultKey,
    VaultStore,
    VaultUnavailable,
    key_file,
    read_machine_key,
    write_machine_key,
)

ROOT: Final = Path(os.environ.get("QMX_PROBE_SCRATCH", "D:/Temp/dr2c")) / "p-vault-away"
ENTRY: Final = "qmx/kimi"
DATA_REF: Final = "qmx/data/databento"
VALUE: Final = "lanes-only-value"
CHAT: Final = SessionId("6f1d2c3b-4a59-4e8d-9b7a-0c1d2e3f4a5b")
MISSING: Final = "vault:unavailable:contabo"
KIMI_ROW: Final[dict[str, object]] = {
    "base_url": "https://upstream.test/anthropic",
    "credential_ref": ENTRY,
    "tiers": {"opus": "kimi-k3", "sonnet": "kimi-k3", "haiku": "kimi-k2.6", "fable": "kimi-k3"},
}
STREAM: Final = b"".join(
    f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode()
    for event in (
        {
            "type": "message_start",
            "message": {"model": "kimi-k3", "usage": {"input_tokens": 12, "output_tokens": 1}},
        },
        {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "ok"}},
        {"type": "message_delta", "usage": {"output_tokens": 3}},
        {"type": "message_stop"},
    )
)


@dataclass
class Seen:
    """The stub upstream's memory of the model calls the relay made."""

    auth: list[str] = field(default_factory=list)

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.auth.append(request.headers.get("authorization", ""))
        return httpx.Response(200, content=STREAM, headers={"content-type": "text/event-stream"})


@dataclass
class Journal:
    rows: list[RelayUsage] = field(default_factory=list)

    def open(self, session: SessionId) -> Journal:
        return self

    def append(self, usage: RelayUsage) -> None:
        self.rows.append(usage)

    def close(self) -> None:
        return None


def server_lookup(home: Path, store: VaultStore) -> Callable[[str], str]:
    """What the server's relay reads a key through: its own store and its own key file, nothing
    else. A machine with no key file says so on the first call."""

    def lookup(reference: str) -> str:
        return store.open(reference, read_machine_key(home, "contabo"))

    return lookup


async def relay_call(lookup: Callable[[str], str], seen: Seen) -> tuple[int, str]:
    """One model call through the relay, against the stub upstream. The second value is the refusal
    text when the call did not happen, so a missing key is checked by its code."""
    journal = Journal()
    relay = await Relay(
        secrets=lookup,
        journal=journal.open,
        alert=_no_alert,
        profiles=lambda: parse_profiles({"kimi": KIMI_ROW}),
        transport=httpx.MockTransport(seen.handle),
    ).start()
    try:
        try:
            grant = await relay.grant(CHAT, ProfileName("kimi"))
        except Exception as error:  # a missing key is refused at the grant, which is the point
            return 0, f"{type(error).__name__}: {error}"
        body = json.dumps(
            {"model": "kimi-k3", "stream": True, "messages": [{"role": "user", "content": "hi"}]}
        ).encode()
        async def read() -> bytes:
            return body

        reply = await relay.handle(
            "POST",
            "/v1/messages",
            "",
            {"authorization": f"Bearer {grant.secret}", "content-type": "application/json"},
            read,
        )
        text = b"".join([chunk async for chunk in reply.body]).decode("utf-8", "replace")
        if reply.finish is not None:
            await reply.finish()
        return reply.status, text[:400]
    finally:
        await relay.close()


async def _no_alert(_chat: SessionId, _reason: str) -> None:
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    arguments = parser.parse_args(argv)
    report = Report("P-VAULT-AWAY")
    shutil.rmtree(ROOT, ignore_errors=True)
    pc_home, server_home, empty_home = ROOT / "pc", ROOT / "server", ROOT / "empty"
    pc_home.mkdir(parents=True)
    server_home.mkdir()
    empty_home.mkdir()
    try:
        server_key, pc_key = VaultKey.generate(), VaultKey.generate()
        written = write_machine_key(server_home, server_key)
        mode = oct(written.stat().st_mode & 0o777)
        report.numbers["key file"] = (
            f"{written.name} mode {mode}" if os.name == "posix" else f"{written.name} (mode 0600 on Ubuntu)"
        )
        if written != key_file(server_home):
            report.fail(f"the key is not where the plan names it: {written}")
        if os.name == "posix" and written.stat().st_mode & 0o777 != 0o600:
            report.fail(f"the key file's mode is {oct(written.stat().st_mode & 0o777)}, not 0600")

        pc = Vault(
            pc_key,
            MemorySource(values={ENTRY: VALUE}),
            machine="pc",
            peers={"contabo": VaultKey.from_public_bytes(server_key.public_bytes())},
        )
        entry = pc.install(ENTRY, VALUE)
        data_entry = pc.install(DATA_REF, json.dumps({"apiKey": VALUE}))
        report.numbers["sealed for"] = sorted(entry.sealed)
        report.numbers["data key sealed for"] = sorted(data_entry.sealed)
        if sorted(entry.sealed) != ["contabo", "pc"]:
            report.fail(f"the entry is sealed for {sorted(entry.sealed)}, not both machines")
        if sorted(data_entry.sealed) != ["contabo", "pc"]:
            report.fail(f"the data key is sealed for {sorted(data_entry.sealed)}, not both machines")
        (server_home / "vault-store.json").write_text(
            json.dumps(pc.sync_document()), encoding="utf-8"
        )
        del pc, entry, data_entry  # the PC is off from here on: the server has two files only

        store = VaultStore("contabo")
        store.sync(json.loads((server_home / "vault-store.json").read_text(encoding="utf-8")))
        key = read_machine_key(server_home, "contabo")
        opened = store.open(ENTRY, key)
        report.numbers["server opened its own entry"] = opened == VALUE
        if opened != VALUE:
            report.fail("the server did not open its own share")
        started = time.perf_counter()
        for _ in range(10):
            store.open(ENTRY, key)
        report.numbers["ten opens ms"] = round((time.perf_counter() - started) * 1000, 2)

        seen = Seen()
        status, detail = asyncio.run(relay_call(server_lookup(server_home, store), seen))
        report.numbers["relay status"] = status
        report.numbers["model calls"] = len(seen.auth)
        if status != 200:
            report.fail(f"the relay served no model call: status {status} {detail}")
        elif seen.auth != [f"Bearer {VALUE}"]:
            report.fail("the relay did not carry the server's own opened key to the provider")

        try:
            read_machine_key(empty_home, "contabo")
        except VaultUnavailable as missing:
            report.numbers["missing key code"] = str(missing)
            if str(missing) != MISSING:
                report.fail(f"the missing key names {missing}")
        else:
            report.fail("a server with no key file opened anyway")
        empty_store = VaultStore("contabo")
        empty_store.sync(json.loads((server_home / "vault-store.json").read_text("utf-8")))
        no_key = Seen()
        status, detail = asyncio.run(relay_call(server_lookup(empty_home, empty_store), no_key))
        report.numbers["relay with no key file"] = f"{status} {detail}"
        if status != 0 or not detail.startswith("GrantRefused"):
            report.fail(f"a server with no key file was not refused at the grant: {status} {detail}")
        elif no_key.auth:
            report.fail("a server with no key file still made a model call")
        elif "VaultUnavailable" not in detail:
            report.fail(f"the refusal does not name the missing key: {detail}")

        opened_data = json.loads(store.open(DATA_REF, key))
        if opened_data != {"apiKey": VALUE}:
            report.fail("the server did not open the data key its own key file sealed")

        def answer(_url: str, _headers: dict[str, str], _method: str) -> Response:
            return Response(
                200,
                {"Date": formatdate(usegmt=True), "Content-Type": "application/json"},
                b'{"datasets": []}',
            )

        data_provider = Broker(id="databento", name="Databento", adapter="databento", kind="data")
        data_connection = Connection(
            id="databento-history", credential_ref=DATA_REF, home="contabo"
        )
        data_probe = probe_for("databento")
        reading = walk(
            data_provider,
            data_connection,
            probe=None
            if data_probe is None
            else lambda p, c: data_probe(p, c, fetch=answer, secret=opened_data),
            now=time.time(),
        )
        report.numbers["server-homed data connection"] = (
            f"{reading.word} {reading.latency_ms} ms"
        )
        if reading.word != "ok":
            report.fail(
                f"the server-homed data connection read {reading.word} {reading.code}"
            )
    finally:
        if not arguments.keep:
            shutil.rmtree(ROOT, ignore_errors=True)
    return report.render()


if __name__ == "__main__":
    raise SystemExit(main())
