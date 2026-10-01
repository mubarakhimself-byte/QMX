"""Stable module entrypoint shim for the host supervisor."""

from qmn.host._supervision import *  # noqa: F403
from qmn.host._supervision import main

if __name__ == "__main__":
    raise SystemExit(main())
