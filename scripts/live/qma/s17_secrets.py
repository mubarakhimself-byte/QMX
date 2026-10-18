"""S17, no key value at rest. Searches the QMX homes the checks used, the evidence logs in
`QMA_EVIDENCE_DIR`, and every transcript and run journal under them for each key value the
checks used: the OpenRouter key from the keyring, the fake model's key and the ChatGPT refresh
token stored in `qmx/chatgpt`. ChatGPT access tokens live only in the memory of the process that
refreshed them, so they are found by shape instead: any JWT whose issuer or audience names
OpenAI. Values are compared in memory and never printed; the log names only the key and the
files that hold it.

PASS when no file holds any value.

    s17_secrets.py [--root <folder> ...] [--slug hp7-s17]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

import keyring
from common import SCRATCH, SHIP_HOME, Log, files_holding
from fake_model import FAKE_KEY
from spend import openrouter_key

JWT = re.compile(rb"eyJ[A-Za-z0-9_-]{8,}\.(eyJ[A-Za-z0-9_-]{8,})\.[A-Za-z0-9_-]{8,}")


def chatgpt_refresh_token() -> str | None:
    raw = keyring.get_password("qmx/chatgpt", "chatgpt")
    return None if raw is None else str(json.loads(raw).get("refresh_token") or "") or None


def openai_jwt(payload: bytes) -> bool:
    try:
        claims = json.loads(base64.urlsafe_b64decode(payload + b"=" * (-len(payload) % 4)))
    except ValueError:
        return False
    named = json.dumps([claims.get("iss"), claims.get("aud")]) if isinstance(claims, dict) else ""
    return "openai" in named.lower()


def files_with_openai_jwt(roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        for path in [root] if root.is_file() else root.rglob("*"):
            try:
                data = path.read_bytes() if path.is_file() else b""
            except OSError:
                continue
            if any(openai_jwt(match.group(1)) for match in JWT.finditer(data)):
                found.append(path)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(prog="s17_secrets.py")
    parser.add_argument("--root", type=Path, action="append", default=[])
    parser.add_argument("--slug", default="hp7-s17")
    args = parser.parse_args()
    log = Log(args.slug)
    evidence = Path(os.environ["QMA_EVIDENCE_DIR"])
    roots = [SCRATCH / "homes", SCRATCH / "workspaces", evidence, SHIP_HOME, *args.root]
    roots = [root for root in roots if root.exists()]
    log(f"searching: {[str(root) for root in roots]}")
    keys = {
        "openrouter": openrouter_key(),
        "fake provider key": FAKE_KEY,
        "ChatGPT refresh token": chatgpt_refresh_token(),
    }
    for name, value in keys.items():
        if value is None:
            log(f"{name}: no keyring entry, nothing to search for")
            continue
        holders = files_holding(roots, value)
        log.check(f"no file holds the {name}", not holders, [str(path) for path in holders])
    shaped = files_with_openai_jwt(roots)
    log.check("no file holds an OpenAI-issued JWT", not shaped, [str(path) for path in shaped])
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
