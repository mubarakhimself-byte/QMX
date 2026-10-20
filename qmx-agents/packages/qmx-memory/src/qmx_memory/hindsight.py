"""Hindsight as the engine's index (AD-18, ruling 119): three banks by writer, rows by document id.

Memory rows stay QMX's own Library objects. Hindsight holds no record QMX does not have: each row
is retained as one document whose id is the row's object id, in the bank of its writer, tagged by
scope, tag, keywords and refs. `rebuild` wipes and re-indexes, so a lost or swapped index costs
nothing but time.

The server runs in this process on embedded Postgres (`pg0`) with its local embedder and reranker,
which is where P-MEM measured it: 2,223 MB peak and one digest retain in 42 s on this PC, so the
plan keeps it on the PC and the server's runs fall back to FTS5 (PRB-L's FAIL). Retains are
`chunks` mode: the row is already QMX's own digest, so Hindsight is not asked to spend a model call
re-extracting text QMX wrote. That is also what keeps a retain inside P-MEM's 30 s line.

No provider key reaches this module. The extractor's model call, when a `reflect` needs one, is the
host's relay grant: a base URL on the router's key lane and a grant secret minted for the
`memory_extractor` role (SOLUTION-DESIGN 28.6). The grant is held in memory and never printed.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from qmx_memory.rows import MemoryRow

BANKS: dict[str, str] = {
    "operator": "qmx-operator",
    "home": "qmx-copilot",
    "run": "qmx-workflows",
    "workflow": "qmx-workflows",
}
"""One bank per writer, tagged by subject: the operator's rows, the copilot's, a workflow's."""

TOP = 50
"""Rows a Hindsight read scores before the engine filters them."""

RETAIN_MODE = "chunks"
"""The extraction Hindsight does on a retain: chunk, embed and index the row QMX already wrote."""


def bank_of(scope: str) -> str:
    try:
        return BANKS[scope]
    except KeyError:
        raise ValueError(f"{scope!r} is not a memory scope") from None


@dataclass(frozen=True)
class HindsightConfig:
    """Where the engine keeps its own folders, and how it reaches a model when it needs one."""

    home: Path
    url: str = ""
    """An already-running server. Empty starts one in this process on `db_url`."""
    db_url: str = "pg0"
    base_url: str = ""
    """The router's key lane, as an OpenAI-compatible root. Empty means no model call."""
    grant: str = field(default="", repr=False)
    """The relay grant minted for the `memory_extractor` role. Never printed, never written."""
    model: str = ""
    timeout_s: float = 120.0
    start_timeout_s: float = 600.0


def importable() -> bool:
    """Whether Hindsight is installed. The engine builds its fallback when it is not."""
    try:
        import hindsight  # noqa: F401, PLC0415
    except ImportError:
        return False
    return True


class HindsightIndex:
    """One Hindsight server and client, in this process, over the home's own folders."""

    def __init__(self, config: HindsightConfig) -> None:
        self.config = config
        self.server: object | None = None
        self.client: object | None = None
        self._banks: set[str] = set()

    def start(self) -> None:
        """Start the server (or take the URL it was given) and make the three banks."""
        if self.client is not None:
            return
        from hindsight import HindsightClient, HindsightServer  # noqa: PLC0415

        url = self.config.url
        if not url:
            self._isolate()
            self.server = HindsightServer(
                db_url=self.config.db_url,
                llm_provider="openai",
                llm_api_key=self.config.grant or "none",
                llm_model=self.config.model or "none",
                llm_base_url=self.config.base_url or None,
            )
            start = getattr(self.server, "start")  # noqa: SLF001
            start(timeout=self.config.start_timeout_s)
            url = str(getattr(self.server, "url"))  # noqa: SLF001
        self.client = HindsightClient(base_url=url, timeout=self.config.timeout_s)
        for bank in dict.fromkeys(BANKS.values()):
            self.bank(bank)

    def _isolate(self) -> None:
        """Hindsight's own folders and its embedder's downloads, under the memory home on `D:`."""
        home = self.config.home
        home.mkdir(parents=True, exist_ok=True)
        for name in ("HF_HOME", "SENTENCE_TRANSFORMERS_HOME"):
            os.environ.setdefault(name, str(home / "hf"))
        os.environ["HINDSIGHT_API_EMBEDDINGS_PROVIDER"] = "local"
        os.environ["HINDSIGHT_API_RERANKER_PROVIDER"] = "local"
        os.environ["HINDSIGHT_API_ENABLE_OBSERVATIONS"] = "false"

    def bank(self, bank_id: str) -> str:
        """The bank, made once per process with the plan's two settings."""
        if bank_id in self._banks:
            return bank_id
        client = self._need()
        try:
            client.create_bank(  # pyright: ignore[reportAttributeAccessIssue]
                bank_id=bank_id, retain_extraction_mode=RETAIN_MODE, enable_observations=False
            )
        except Exception as error:  # a bank that exists is what we wanted
            if "exist" not in str(error).lower():
                raise
        self._banks.add(bank_id)
        return bank_id

    def close(self) -> None:
        client, server = self.client, self.server
        self.client, self.server, self._banks = None, None, set()
        if client is not None:
            closer = getattr(client, "close", None)
            if closer is not None:
                closer()
        if server is not None:
            stop = getattr(server, "stop", None)
            if stop is not None:
                stop()

    # -- the index interface ------------------------------------------------------------

    def index(self, rows: Iterable[MemoryRow], *, rebuild: bool = False) -> int:
        """Retain each row as one document in its writer's bank. Idempotent by object id."""
        found = list(rows)
        self.start()
        for row in found:
            self._retain(row)
        return len(found)

    def _retain(self, row: MemoryRow) -> None:
        client = self._need()
        bank = self.bank(bank_of(row.scope))
        client.retain(  # pyright: ignore[reportAttributeAccessIssue]
            bank_id=bank,
            content=row.indexed(),
            document_id=row.object_id,
            tags=list(row.tags()),
            update_mode="replace",
        )

    def forget(self, row_ids: Sequence[str]) -> int:
        """Delete each row's document from every bank. A gone row is gone from recall."""
        self.start()
        client = self._need()
        removed = 0
        for row_id in row_ids:
            for bank in dict.fromkeys(BANKS.values()):
                if self._delete(client, bank, row_id):
                    removed += 1
        return removed

    def _delete(self, client: object, bank: str, document_id: str) -> bool:
        documents = getattr(client, "documents", None)
        if documents is None:
            return False
        delete = getattr(documents, "delete_document", None)
        if delete is None:
            return False
        found = delete(bank, document_id)
        if asyncio.iscoroutine(found):
            asyncio.run(found)
        return True

    def rebuild(self, rows: Iterable[MemoryRow]) -> int:
        """Wipe the banks and re-index. A row archived by `forget` is not in `rows`, so it stays
        out of recall."""
        found = list(rows)
        self.start()
        client = self._need()
        for bank in dict.fromkeys(BANKS.values()):
            try:
                client.delete_bank(bank)  # pyright: ignore[reportAttributeAccessIssue]
            except Exception as error:
                if "exist" not in str(error).lower() and "found" not in str(error).lower():
                    raise
            self._banks.discard(bank)
        return self.index(found)

    def recall(
        self, query: str, tags: Sequence[str] = (), limit: int = TOP
    ) -> list[tuple[str, float]]:
        """`(row_id, score)` best first, from Hindsight's own ranking."""
        self.start()
        client = self._need()
        found: dict[str, float] = {}
        for bank in dict.fromkeys(BANKS.values()):
            asked = list(tags) if tags else None
            try:
                answer = client.recall(  # pyright: ignore[reportAttributeAccessIssue]
                    bank_id=bank, query=query, budget="mid", max_tokens=4096, tags=asked
                )
            except Exception as error:
                if "exist" in str(error).lower():
                    continue
                raise
            for rank, result in enumerate(answer.results[:limit]):
                row_id = getattr(result, "document_id", None)
                if not isinstance(row_id, str) or not row_id:
                    continue
                score = _score(result, rank)
                found[row_id] = max(found.get(row_id, 0.0), score)
        return sorted(found.items(), key=lambda pair: pair[1], reverse=True)[:limit]

    def reflect(self, question: str, tags: Sequence[str] = ()) -> tuple[str, list[str]]:
        """Hindsight's own answer to a question, with the row ids it cited."""
        self.start()
        client = self._need()
        bank = self.bank(BANKS["operator"])
        asked = list(tags) if tags else None
        answer = client.reflect(  # pyright: ignore[reportAttributeAccessIssue]
            bank_id=bank, query=question, tags=asked
        )
        text = str(getattr(answer, "text", "") or getattr(answer, "answer", "") or "")
        cited = [
            str(found)
            for found in (getattr(answer, "citations", None) or [])
            if isinstance(found, str)
        ]
        return text, cited

    def _need(self) -> object:
        client = self.client
        if client is None:
            raise RuntimeError("Hindsight is not started")
        return client


def _score(result: object, rank: int) -> float:
    """A hit's score from Hindsight's own numbers when it reports one, else its rank."""
    scores = getattr(result, "scores", None)
    for name in ("final", "relevance", "score", "similarity"):
        value = getattr(scores, name, None) if scores is not None else None
        if isinstance(value, int | float):
            return float(value)
    return 1.0 / (1.0 + rank)


def config_document(config: HindsightConfig) -> str:
    """What the host may log: where it points, never the grant."""
    return json.dumps(
        {
            "home": config.home.as_posix(),
            "db_url": config.db_url,
            "url": config.url or "in process",
            "base_url": config.base_url or "none",
            "model": config.model or "none",
            "grant": "held" if config.grant else "none",
        },
        sort_keys=True,
    )
