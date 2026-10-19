"""Ids the router shares with the harness."""

from __future__ import annotations

from typing import NewType

SessionId = NewType("SessionId", str)
"""The qmx-control session UUID, also the SDK session id and the launcher's chat id."""
