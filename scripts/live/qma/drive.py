"""Drive the QMA host's HTTP doors and print PASS or FAIL with the observed value.

    drive.py [--port 8876] get /api/doctor --expect "plan auth method"
    drive.py put /api/claude-settings '{"permissions": {"allow": ["Read"]}}' --status 200
    drive.py put /api/claude-settings @body.json --status 400 --expect apiKeyHelper
    drive.py post /api/chats '{"title": "check 2", "workspace": "D:/Temp/ws"}'
    drive.py turn <sid> "What is in this folder? Summarise the README." --expect-block tool

`turn` posts operator text, prints each block the turn writes as it lands, and reads the chat
record under `--home` until the turn is idle. It passes when the record ends with turn "idle"
and started true and every `--expect-block` kind arrived. It also listens on the chat's live
channel and prints the seconds from the post to the first text delta (the HP6 perf metric).

The bearer comes from keyring `qmx/control-token` and is never printed. Exit 0 when every
expectation holds, 1 otherwise, 3 when there is no token or no host.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
import threading
import time
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
    parser.add_argument("method", choices=["get", "put", "post", "turn"])
    parser.add_argument("path", help="the route, or the session id for turn")
    parser.add_argument("body", nargs="?", help="JSON text, or @file; the operator text for turn")
    parser.add_argument("--status", type=int, default=200, help="expected HTTP status")
    parser.add_argument("--expect", action="append", default=[], help="text the reply holds")
    parser.add_argument("--absent", action="append", default=[], help="text the reply lacks")
    parser.add_argument("--home", type=Path, default=Path("D:/QMX-worktrees/qma-ship/home"))
    parser.add_argument("--expect-block", action="append", default=[], help="a block kind")
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    token = keyring.get_password("qmx/control-token", "control-token")
    if token is None:
        print("BLOCKED no qmx/control-token in the keyring; start qma.serve once")
        return 3
    if args.method == "turn":
        return turn(args, {"Authorization": f"Bearer {token}"})
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


def events_after(client: httpx.Client, chat: str, after: int) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    while True:
        page = client.get(f"/api/sessions/{chat}/events", params={"after": after, "limit": 1000})
        page.raise_for_status()
        rows: list[dict[str, Any]] = page.json()
        found += rows
        if len(rows) < 1000:
            return found
        after = rows[-1]["id"]


def first_delta(
    base: str, headers: dict[str, str], chat: str, first: list[float], listening: threading.Event
) -> None:
    with (
        httpx.Client(base_url=base, headers=headers, timeout=httpx.Timeout(5, read=600)) as client,
        client.stream("GET", f"/api/sessions/{chat}/live") as stream,
    ):
        listening.set()
        for line in stream.iter_lines():
            if line.startswith("data:") and '"kind":"text"' in line.replace(" ", ""):
                first.append(time.monotonic())
                return


def turn(args: argparse.Namespace, headers: dict[str, str]) -> int:
    chat, record_path = args.path, args.home / "chats" / f"{args.path}.json"
    base = f"http://127.0.0.1:{args.port}"
    kinds: list[str] = []
    with httpx.Client(base_url=base, headers=headers, timeout=120) as client:
        try:
            seen = events_after(client, chat, 0)
        except httpx.HTTPError as error:
            print(f"BLOCKED no host on port {args.port} or no chat {chat}: {error!r}")
            return 3
        after = seen[-1]["id"] if seen else 0
        first: list[float] = []
        listening = threading.Event()
        threading.Thread(
            target=first_delta, args=(base, headers, chat, first, listening), daemon=True
        ).start()
        listening.wait(10)
        started = time.monotonic()
        sent = client.post(f"/api/sessions/{chat}/turns", json={"text": args.body})
        print(f"POST turn -> {sent.status_code} {sent.text}")
        record: dict[str, Any] = {}
        while time.monotonic() - started < args.timeout:
            record = json.loads(record_path.read_text(encoding="utf-8"))
            for event in events_after(client, chat, after):
                after = event["id"]
                block = event["data"].get("block")
                if block:
                    kinds.append(block["type"])
                    print(
                        f"  +{time.monotonic() - started:5.1f}s [{block['type']}] "
                        f"{json.dumps(block['content'], ensure_ascii=False)[:300]}"
                    )
            if sent.status_code != 202 or record.get("turn") == "idle":
                break
            time.sleep(0.5)
    print(f"record turn={record.get('turn')} started={record.get('started')}")
    delay = f"{first[0] - started:.2f} s" if first else "none"
    print(f"first text delta on the live channel after {delay}")
    checks = [
        ("status 202", sent.status_code == 202, sent.status_code),
        ("record turn idle", record.get("turn") == "idle", record.get("turn")),
        ("record started", record.get("started") is True, record.get("started")),
    ]
    checks += [(f"a {kind} block", kind in kinds, kinds.count(kind)) for kind in args.expect_block]
    for name, ok, seen_value in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: observed {seen_value}")
    passed = all(ok for _, ok, _ in checks)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
