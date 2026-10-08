"""Small process-local cache; durable fetched_at rows stay in the app's SQLite."""

import threading
from collections.abc import Callable, Hashable

from cachetools import TTLCache


class ReadCache[K: Hashable, V]:
    def __init__(self, *, maxsize: int = 128, ttl: float = 30) -> None:
        self._cache = TTLCache[K, V](maxsize=maxsize, ttl=ttl)
        self._lock = threading.RLock()

    def get(self, key: K, fetch: Callable[[], V]) -> V:
        with self._lock:
            try:
                return self._cache[key]
            except KeyError:
                value = fetch()
                self._cache[key] = value
                return value

    def invalidate(self) -> None:
        with self._lock:
            self._cache.clear()
