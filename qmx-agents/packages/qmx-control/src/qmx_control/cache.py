"""Short-lived caches for expensive reads; never cache model responses."""

from collections.abc import Callable
from threading import RLock
from time import monotonic
from typing import Any

from cachetools import TTLCache, cached


def read_cache(
    ttl: float = 30, maxsize: int = 128, *, timer: Callable[[], float] = monotonic
) -> Callable[[Callable[..., Any]], Any]:
    """Decorate synchronous read tools; cache_clear invalidates them on events."""
    cache: TTLCache[Any, Any, float] = TTLCache(maxsize=maxsize, ttl=ttl, timer=timer)
    return cached(cache, lock=RLock())
