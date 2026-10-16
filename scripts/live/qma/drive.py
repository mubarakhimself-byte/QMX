"""Drive the QMA host's HTTP doors and print PASS or FAIL with the observed value.

    drive.py [--port 8876] get /api/doctor --expect "plan auth method"
    drive.py put /api/claude-settings '{"permissions": {"allow": ["Read"]}}' --status 200
    drive.py put /api/claude-settings @body.json --status 400 --expect apiKeyHelper

The bearer comes from keyring `qmx/control-token` and is never printed. Exit 0 when every
expectation holds, 1 otherwise, 3 when there is no token or no host.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path
from typing import Any

import httpx
import keyring


def body_of(text: str | None) -> Any:
    if text is None:
        return None
    if text.startswith("@"):
        text = Path(text[1:]).read_text(encoding="utf-8")
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(prog="drive.py")
    parser.add_argument("--port", type=int, default=8876)
    parser.add_argument("method", choices=["get", "put", "post"])
    parser.add_argument("path")
    parser.add_argument("body", nargs="?", help="JSON text, or @file")
    parser.add_argument("--status", type=int, default=200, help="expected HTTP status")
    parser.add_argument("--expect", action="append", default=[], help="text the reply holds")
    parser.add_argument("--absent", action="append", default=[], help="text the reply lacks")
    args = parser.parse_args()
    token = keyring.get_password("qmx/control-token", "control-token")
    if token is None:
        print("BLOCKED no qmx/control-token in the keyring; start qma.serve once")
        return 3
    try:
        response = httpx.request(
            args.method.upper(),
            f"http://127.0.0.1:{args.port}{args.path}",
            json=body_of(args.body),
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )
    except httpx.HTTPError as error:
        print(f"BLOCKED no host on port {args.port}: {error!r}")
        return 3
    text = response.text
    with contextlib.suppress(ValueError):
        text = json.dumps(response.json(), indent=2)
    print(f"{args.method.upper()} {args.path} -> {response.status_code}")
    print(text)
    checks = [(f"status {args.status}", response.status_code == args.status, response.status_code)]
    checks += [(f"holds {want!r}", want in text, want in text) for want in args.expect]
    checks += [(f"lacks {gone!r}", gone not in text, gone in text) for gone in args.absent]
    for name, ok, seen in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: observed {seen}")
    passed = all(ok for _, ok, _ in checks)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
