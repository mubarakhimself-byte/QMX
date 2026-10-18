"""The one redaction function (AD-37). Nothing the engine stores or serves carries a secret.

It runs at the write seams, not in executors: the ledger writer, the inbox table, the memo
table, the `LibraryPort` adapter, the trace export and the REST serializer. Two mechanisms:

- Shapes. The high-specificity key prefixes match anywhere, glued to a word or not
  (`key_sk-or-v1-...`). The generic `sk-` shape needs a digit and matches only at a word start or
  right after `key`, `token`, `secret` or `bearer`, so `risk-adjusted-returns` is no key.
- Values. A secret the engine handled (a tool key it resolved into a child, a pass it minted) is
  registered once and replaced by `[redacted:<ref>]` wherever it appears.

Keys in encoded forms (base64, reversed, split across fields) pass; that is an accepted miss.
"""

from __future__ import annotations

import re
import threading
from typing import Final, cast

from pydantic import JsonValue

MASK: Final = "[redacted]"
MIN_VALUE: Final = 12
"""A registered value shorter than this is refused, so redaction never blanks common words."""

GLUED: Final = (
    r"sk-or-v1-[A-Za-z0-9_-]{16,}",
    r"sk-ant-[A-Za-z0-9_-]{16,}",
    r"sk-proj-[A-Za-z0-9_-]{16,}",
    r"sk-svcacct-[A-Za-z0-9_-]{16,}",
    r"sk-admin-[A-Za-z0-9_-]{16,}",
    r"AKIA[0-9A-Z]{16}",
    r"gh[pousr]_[A-Za-z0-9]{36,}",
    r"github_pat_[A-Za-z0-9_]{22,}",
    r"xox[abposr]-[0-9A-Za-z-]{10,}",
    r"AIza[0-9A-Za-z_-]{35}",
    r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*",
    r"-----BEGIN[A-Z ]*PRIVATE KEY-----[A-Za-z0-9+/=\s\\]*(?:-----END[A-Z ]*PRIVATE KEY-----)?",
)
LEADS: Final = ("key", "token", "secret", "bearer")
GENERIC: Final = (
    "(?:(?<![A-Za-z0-9_-])"
    + "".join(f"|(?<=(?i:{lead}){sep})" for lead in LEADS for sep in ("", "_", "-"))
    + r")sk-(?=[A-Za-z_-]*[0-9])[A-Za-z0-9_-]{20,}"
)
ZHIPU: Final = r"(?<![0-9a-f])[0-9a-f]{32}\.[A-Za-z0-9]{16}(?![A-Za-z0-9])"
"""A GLM (Z.ai) key: 32 hex digits, a dot, 16 letters or digits. It has no prefix."""
SHAPES: Final = re.compile("|".join((*GLUED, GENERIC, ZHIPU)))

_values: dict[str, str] = {}
_values_lock = threading.Lock()


def register(ref: str, value: str) -> None:
    """Redact `value` as `[redacted:<ref>]` from now on, in every seam of this process."""
    if len(value) < MIN_VALUE:
        raise ValueError(f"{ref} resolved to a value shorter than {MIN_VALUE} characters")
    with _values_lock:
        _values[value] = ref


def counted(text: str) -> tuple[str, int]:
    """The text redacted, and how many secrets it held."""
    found = 0
    if _values:
        with _values_lock:
            values = sorted(_values.items(), key=lambda pair: -len(pair[0]))
        for value, ref in values:
            if value in text:
                found += text.count(value)
                text = text.replace(value, f"[redacted:{ref}]")
    text, shaped = SHAPES.subn(MASK, text)
    return text, found + shaped


def redact(text: str) -> str:
    return counted(text)[0]


def holds_value(data: bytes) -> bool:
    """True when a binary blob holds a registered value, which no text pass can mask."""
    with _values_lock:
        values = list(_values)
    return any(value.encode() in data for value in values)


def redact_json(value: object) -> tuple[JsonValue, int]:
    """Every string in the value redacted, keys included, and the total count. A tuple comes back
    a list, as JSON would write it."""
    if isinstance(value, str):
        return counted(value)
    if isinstance(value, dict):
        total = 0
        out: dict[str, JsonValue] = {}
        for key, item in cast(dict[object, object], value).items():
            clean_key, n = counted(str(key))
            clean, m = redact_json(item)
            out[clean_key] = clean
            total += n + m
        return out, total
    if isinstance(value, list | tuple):
        total = 0
        items: list[JsonValue] = []
        for item in cast(list[object], value):
            clean, n = redact_json(item)
            items.append(clean)
            total += n
        return items, total
    return cast(JsonValue, value), 0
