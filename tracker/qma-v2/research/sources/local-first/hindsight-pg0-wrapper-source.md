<!--
source_url: https://github.com/vectorize-io/hindsight/blob/main/hindsight-api-slim/hindsight_api/pg0.py
fetched_from: https://raw.githubusercontent.com/vectorize-io/hindsight/main/hindsight-api-slim/hindsight_api/pg0.py
title: Hindsight source: embedded pg0 wrapper (lines 1-70)
fetched: 2026-10-26
fetched_by: research agent for study 62b (source excerpt; shows the wrapper passes name, username, port to Pg0 and no data_dir)
-->

```python
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qsl

if TYPE_CHECKING:
    from pg0 import Pg0

logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "hindsight"
DEFAULT_PASSWORD = "hindsight"
DEFAULT_DATABASE = "hindsight"


class EmbeddedPostgres:
    """Manages an embedded PostgreSQL server instance using pg0-embedded."""

    def __init__(
        self,
        port: int | None = None,
        username: str = DEFAULT_USERNAME,
        password: str = DEFAULT_PASSWORD,
        database: str = DEFAULT_DATABASE,
        name: str = "hindsight",
        config: dict[str, str] | None = None,
        **kwargs,
    ):
        self.port = port  # None means pg0 will auto-assign
        self.username = username
        self.password = password
        self.database = database
        self.name = name
        # Extra postgresql.conf settings forwarded to Pg0 (e.g. ``max_connections``).
        # Useful when tests spawn many xdist workers that each open a pool against
        # the same pg0 instance — the postgres default of 100 max_connections is
        # easy to exhaust under that fan-out.
        self.config = config
        self._pg0: Pg0 | None = None

    def _get_pg0(self) -> Pg0:
        if self._pg0 is None:
            try:
                from pg0 import Pg0
            except ImportError:
                raise ImportError(
                    "pg0-embedded is required for embedded PostgreSQL. "
                    "Install it with: pip install 'hindsight-api-slim[embedded-db]'"
                )
            # A kwargs BAG, assembled conditionally below. Inferred, its value type is the union
            # of everything in it, so the `**` unpack is checked as if every key could be every
            # type -- one diagnostic per parameter of the callee, none of them real.
            kwargs: dict[str, Any] = {
                "name": self.name,
                "username": self.username,
                "password": self.password,
                "database": self.database,
            }
            # Only set port if explicitly specified
            if self.port is not None:
                kwargs["port"] = self.port
            if self.config is not None:
                kwargs["config"] = self.config
            self._pg0 = Pg0(**kwargs)
        return self._pg0

    async def start(self, max_retries: int = 5, retry_delay: float = 4.0) -> str:
```
