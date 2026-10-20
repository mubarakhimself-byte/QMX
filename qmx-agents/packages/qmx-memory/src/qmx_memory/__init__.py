"""QMX memory: memory rows in the Library, Hindsight as the index, FTS5 as the backup (AD-18).

`RecallEngine` is the port the engine and the host's memory tools speak. `HindsightIndex` is the
default index and `FtsIndex` the fallback over the same rows. `RetainWorker` turns a chat's turn
into a digest row. `rows` holds the row's shape and its filters, so a read is one function to
audit.
"""

from qmx_memory.engine import RecallEngine
from qmx_memory.fts import FtsIndex
from qmx_memory.hindsight import HindsightConfig, HindsightIndex
from qmx_memory.retain import RetainWorker
from qmx_memory.rows import SCOPES, SNAPSHOT_LINES, TAGS, MemoryRow, memory_ref

__all__ = [
    "SCOPES",
    "SNAPSHOT_LINES",
    "TAGS",
    "FtsIndex",
    "HindsightConfig",
    "HindsightIndex",
    "MemoryRow",
    "RecallEngine",
    "RetainWorker",
    "memory_ref",
]
