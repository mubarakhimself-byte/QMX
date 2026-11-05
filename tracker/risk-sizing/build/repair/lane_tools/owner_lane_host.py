"""`python -m qmx_host` for a C-14 lane: the same host, with one outbound rule added. Every
`socket.create_connection` it makes to a host other than this machine is refused and written to
stderr, so the connect kind's round-trip step reaches no broker. Its node runs as a child with its
own endpoints file, which names only loopback."""

from __future__ import annotations

import faulthandler
import os
import runpy
import socket
import sys
from pathlib import Path

LOOPBACK = {"127.0.0.1", "::1", "localhost"}
shipped = socket.create_connection


def loopback_only(address, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN201
    if address[0] not in LOOPBACK:
        print(f"LANE refused an outbound connection to {address[0]}:{address[1]}", file=sys.stderr, flush=True)
        raise OSError(f"the lane holds this host to loopback; {address[0]} refused")
    return shipped(address, *args, **kwargs)


socket.create_connection = loopback_only
stacks = (Path(os.environ["C38_KEYRING_FILE"]).parent / "host-stacks.log").open("a", encoding="utf-8")
faulthandler.dump_traceback_later(40, repeat=True, file=stacks)


def watch_the_lease() -> None:
    """Every refused volume lease, with every thread's stack at that moment."""
    from qmx_apps import volume  # noqa: PLC0415

    shipped_lock = volume.VolumeLease._lock  # noqa: SLF001

    def told(self):  # noqa: ANN001, ANN202
        try:
            return shipped_lock(self)
        except Exception as refused:
            print(f"LANE lease refused on {getattr(self.file, 'name', '?')}: {refused}", file=stacks, flush=True)
            faulthandler.dump_traceback(file=stacks, all_threads=True)
            stacks.flush()
            raise

    volume.VolumeLease._lock = told  # noqa: SLF001


watch_the_lease()
sys.argv = ["qmx_host", *sys.argv[1:]]
runpy.run_module("qmx_host", run_name="__main__", alter_sys=True)
