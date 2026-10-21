"""The purge drill: one operator purge tombstones a secret on the Hub, the PC and the bucket
(LIB4 lane 4, Library AD-6).

Run from `qmx-agents/` with the agents venv:

    uv run --no-sync python ../scripts/live/server/purge_drill.py

A note's body holds a secret that redaction does not recognise (engine AD-37 refuses token-shaped
values at put, so a purge is still the operator's answer for the rest). The blob is planted on the
Hub, mirrored to a PC replica and copied to the bucket; the operator purges it through the Hub;
then:

- the Hub's bytes are gone, its tombstone names the reason, and `refs/purges/<hex>` moved;
- the bucket's bytes are gone and its tombstone is beside them;
- the PC replica applies the same tombstone on its next sync, and the object reads `blob_purged`;
- an agent's purge is refused.

Writes `<LIB4_EVIDENCE>/<LIB4_LOG_PREFIX>lib4-purge.log` and exits 1 when a check failed.
"""

from __future__ import annotations

import shutil
import time
from collections.abc import Sequence
from typing import Final, cast

from e67_claims import (
    HOMES,
    SERVER_DIR,
    Log,
    health,
    prepare_server,
    ssh,
    start_hub,
    stop_hub,
    write_home,
)

LANE: Final = "purge"
BUCKET: Final = f"{SERVER_DIR}/{LANE}/bucket"
SECRET: Final = b"the vault code is 4411"


def main(argv: Sequence[str] | None = None) -> int:
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_hub.replicate import StorePeer, sync  # noqa: PLC0415
    from qmx_library.client import HubClient, OwnerTable  # noqa: PLC0415
    from qmx_library.port import Draft, LibraryRefused  # noqa: PLC0415
    from qmx_library.principal import Principal  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    log = Log("lib4-purge")
    hub_url = ""
    try:
        log.say(f"lane purge at {time.strftime('%Y-%m-%dT%H:%M:%S')}")
        prepare_server(LANE)
        ssh(f"install -d -m 0755 {BUCKET}/blobs && chown -R prbs:prbs {SERVER_DIR}/{LANE}")
        hub_url, key = start_hub(LANE, extra=f"--bucket {BUCKET}")
        write_home(HOMES / f"lib4-{LANE}", hub_url, key)
        log.check(health(hub_url, key).get("ok") is True, f"hub answers at {hub_url}")
        client = HubClient(hub_url, key, "operator")

        done = client.put(
            Draft("note", "planted", title="planted", blobs={"body.md": SECRET}),
            on="main",
            expected_head=None,
        )
        view = client.get(done.object_id, blobs="fetch")
        blobs = cast(dict[str, dict[str, str]], view["blobs"])
        blob_id = blobs["body.md"]["blob_id"]
        log.say(f"planted {blob_id} on the hub")
        ssh(f"cp {bucket_source(blob_id)} {BUCKET}/blobs/ && chown -R prbs:prbs {BUCKET}")
        bucket_blob = f"{BUCKET}/blobs/{blob_id.removeprefix('sha256:')}"
        log.check(
            ssh(f"test -e {bucket_blob} && echo there || echo gone") == "there",
            "the bucket holds a copy of the secret",
        )

        local = HOMES / f"lib4-{LANE}" / "pc"
        shutil.rmtree(local, ignore_errors=True)
        with Store.open(local, redactor=redact, name="pc", role="replica") as pc:
            first = sync(StorePeer(pc), client, OwnerTable("server"))
            log.check(first.ok, "the PC replica synced the hub's refs and objects")
            log.check(pc.has_blob(blob_id), "the secret reached the PC replica")

            purged = client.purge(blob_id, "a vault code")
            log.say(f"purged as {purged.ref}")
            log.check(
                ssh(f"test -e {bucket_source(blob_id)} && echo there || echo gone") == "gone",
                "the hub's bytes are gone",
            )
            log.check(
                ssh(f"test -e {bucket_blob} && echo there || echo gone") == "gone",
                "the bucket's bytes are gone",
            )
            log.check(
                ssh(
                    f"test -e {BUCKET}/tombstones/"
                    f"{blob_id.removeprefix('sha256:')}.json && echo there || echo gone"
                )
                == "there",
                "the bucket's tombstone is beside where the bytes were",
            )
            refs = {row.ref for row in client.refs()}
            log.check(
                f"refs/purges/{blob_id.removeprefix('sha256:')}" in refs,
                "the purge is a ref move the replicas follow",
            )

            second = sync(StorePeer(pc), client, OwnerTable("server"))
            log.check(second.ok, "the PC replica synced again")
            log.check(pc.purged(blob_id), "the PC replica applied the tombstone")
            log.check(not pc.has_blob(blob_id), "the PC's bytes are gone")
            log.check(
                pc.get(Principal("operator"), done.object_id, blobs="fetch").purged
                == frozenset({"body.md"}),
                "the object that named the blob reads blob_purged",
            )

            agent = HubClient(hub_url, key, "agent:alice")
            refused = False
            try:
                agent.purge(blob_id, "an agent's try")
            except LibraryRefused as error:
                refused = error.code == "purge_refused"
            log.check(refused, "an agent's purge is refused")
    except Exception as error:
        log.check(False, f"lane aborted: {error}")
    finally:
        if hub_url:
            stop_hub(LANE)
    return log.close()


def bucket_source(blob_id: str) -> str:
    """Where the Hub store keeps a durable blob, sharded by its hash."""
    hexdigest = blob_id.removeprefix("sha256:")
    return f"{SERVER_DIR}/{LANE}/hub/library/blobs/{hexdigest[:2]}/{hexdigest[2:4]}/{hexdigest}"


if __name__ == "__main__":
    raise SystemExit(main())
