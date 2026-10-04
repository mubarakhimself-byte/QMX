"""One reentrant authority lock for Task graph, leases and TaskLedger mutations.

Admission holds this lock only across host checks and durable effects. Provider
and QMB child execution must happen outside it. Lock order is request runtime,
Task authority, then journal/sqlite; Task mutations never call request runtime.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from threading import RLock
from typing import Concatenate, Protocol


class AuthorityOwner(Protocol):
    @property
    def authority_lock(self) -> RLock: ...


def serialized[Owner: AuthorityOwner, **P, T](
    method: Callable[Concatenate[Owner, P], T],
) -> Callable[Concatenate[Owner, P], T]:
    @wraps(method)
    def call(owner: Owner, /, *args: P.args, **kwargs: P.kwargs) -> T:
        with owner.authority_lock:
            return method(owner, *args, **kwargs)

    return call
