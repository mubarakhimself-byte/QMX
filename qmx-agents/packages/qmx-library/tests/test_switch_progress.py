"""The switch says how far it is, one call per old version row, so the first-start card can show
versions switched while it runs."""

from __future__ import annotations

from pathlib import Path

from qmx_engine.ledger import redact
from test_migrate import library_b

from qmx_library.migrate.from_library_b import switch_over


def test_the_switch_counts_each_version_row_it_imports(tmp_path: Path) -> None:
    library_b(tmp_path)
    seen: list[tuple[int, int]] = []

    switched = switch_over(
        tmp_path, redactor=redact, on_item=lambda done, total: seen.append((done, total))
    )

    assert switched.ok, switched.verification.render()
    assert seen == [(n, 7) for n in range(1, 8)]


def test_the_switch_without_a_progress_reader_is_unchanged(tmp_path: Path) -> None:
    library_b(tmp_path)

    switched = switch_over(tmp_path, redactor=redact)

    assert switched.ok, switched.verification.render()
    assert (switched.imported.objects, switched.imported.edges) == (7, 2)
