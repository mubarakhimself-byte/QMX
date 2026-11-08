"""The interpreter and the TA-Lib build QML's numbers are proven on (QML-25, AD-119).

``environment_check`` names a wrong one in plain words, every problem at once. A hosted unit's
snapshot records ``current_environment()``, so a snapshot taken under another interpreter
restores cold instead of resuming on numbers that interpreter never produced.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

__all__ = [
    "PYTHON",
    "TALIB_BUILD",
    "Environment",
    "EnvironmentProblem",
    "current_environment",
    "environment_check",
]

PYTHON: Final[tuple[int, int]] = (3, 14)
TALIB_BUILD: Final[str] = "0.7.1"
"""The build QML's goldens were taken from (``qml/tests/golden/talib-0.7.1.json``)."""


@dataclass(frozen=True, slots=True)
class Environment:
    """Where a hosted unit ran: the interpreter's major and minor version, such as ``3.14``."""

    python: str


@dataclass(frozen=True, slots=True)
class EnvironmentProblem:
    """``what`` is ``python`` or ``talib``; ``message`` says what is wrong and what to install."""

    what: str
    message: str


def _python(version_info: Sequence[int] | None) -> Sequence[int]:
    return tuple(sys.version_info[:3]) if version_info is None else version_info


def current_environment(version_info: Sequence[int] | None = None) -> Environment:
    found = _python(version_info)
    return Environment(python=f"{found[0]}.{found[1]}")


def environment_check(
    version_info: Sequence[int] | None = None, talib: str | None = None
) -> tuple[EnvironmentProblem, ...]:
    """Every way this machine differs from what QML needs; empty when it matches.

    ``version_info`` defaults to the running interpreter's. QML imports no TA-Lib, so the caller
    passes the TA-Lib version it found; ``None`` leaves the build unchecked.
    """
    problems: list[EnvironmentProblem] = []
    found = _python(version_info)
    if tuple(found[:2]) != PYTHON:
        want = ".".join(str(n) for n in PYTHON)
        have = ".".join(str(n) for n in found)
        problems.append(
            EnvironmentProblem(
                "python",
                f"QML needs Python {want}.x, and this is Python {have}. "
                f"Install Python {want} and recreate this environment with it.",
            )
        )
    if talib is not None and talib != TALIB_BUILD:
        problems.append(
            EnvironmentProblem(
                "talib",
                f"QML's indicators are checked against TA-Lib {TALIB_BUILD}, and this machine has "
                f"TA-Lib {talib}. Install TA-Lib {TALIB_BUILD}.",
            )
        )
    return tuple(problems)
