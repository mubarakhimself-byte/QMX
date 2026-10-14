"""One-action export of a thread: blocks, engine transcript, usage, traces, hook log."""

from __future__ import annotations

from pathlib import Path

from qma2.harness import BlockSink
from qma2.store import Store
from qma2.types import ExportBundle, ThreadId


def export_thread(
    thread_id: ThreadId, *, store: Store, sink: BlockSink, claude_home: Path, trace_dir: Path, out_dir: Path
) -> ExportBundle:
    """Zip layout:
      blocks.jsonl            every block (from sink.blocks)
      segments.json           engine, account, model per segment
      transcript/<segment>/   Claude: the JSONL from <claude_home>/projects/<cwd-key>/<id>.jsonl
                              (copied verbatim; QMX reads only transcripts, never credentials);
                              OpenAI: items dumped from the SQLiteSession
      usage.jsonl             rows for the thread
      traces/                 per-turn JSONL
      hooks.log
    Redaction applies to blocks, usage and traces; transcripts are the engine's own text.
    Idempotent: the zip name includes the last block seq; re-export overwrites the same file."""
    raise NotImplementedError
