"""Error signatures: one hash for every failure that differs only in ids, hashes, paths or numbers.

The watchdog and the ladder compare signatures to tell "the same node failed the same way twice"
from two different failures (AD-16), so the parts of a message that change from run to run are
replaced before hashing.
"""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Final

_UUID: Final = re.compile(
    r"\b[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}\b", re.IGNORECASE
)
# At least one digit, so a plain word made of the letters a-f stays a word.
_HASH: Final = re.compile(r"\b(?:sha256:)?(?=[0-9a-f]*\d)[0-9a-f]{7,}\b", re.IGNORECASE)
_PATH: Final = re.compile(r"""[^\s'"`]*[\\/][^\s'"`]*""")
_DIGITS: Final = re.compile(r"\d+")


def normalized(message: str) -> str:
    message = _UUID.sub("<uuid>", message)
    message = _HASH.sub("<hash>", message)
    message = _PATH.sub("<path>", message)
    return _DIGITS.sub("<n>", message)


def signature(code: str, message: str) -> str:
    return sha256(f"{code}\n{normalized(message)}".encode()).hexdigest()
