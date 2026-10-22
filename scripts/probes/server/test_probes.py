"""Each PRB-S verdict on recorded fixtures: the server's heartbeat row against the library's, the
P-MEM judge against the PC's numbers and the 2,048 MB line, and the capacity arithmetic behind
`overhead_mb`.

uv run --no-sync python -m pytest scripts/probes/server -q
"""

# ruff: noqa: S101

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common
import p_mem
import p_ops

OPS = common.library("p_ops")


def a_process() -> SimpleNamespace:
    """A process as psutil reports one."""
    return SimpleNamespace(
        cpu_times=lambda: SimpleNamespace(user=1.0, system=0.5),
        memory_info=lambda: SimpleNamespace(rss=256 * 2**20),
        create_time=lambda: 0.0,
    )


def test_ops_row_is_the_library_row_for_the_server_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: SimpleNamespace(free=8 << 30))
    server = p_ops.row("run-01", a_process(), ["claim"])
    library_row = OPS.row("run-01", a_process(), ["claim"])
    assert set(server) == set(library_row)
    assert {"run_id", "at", "cpu_seconds", "rss_mb", "machine_minutes", "capacity_in_use"} <= set(
        server
    )
    assert (server["host"], server["free_disk_mb"]) == ("server", 8192)
    assert (library_row["host"], library_row["free_disk_mb"]) == ("pc", 8192)


def test_ops_passes_a_small_row_and_a_small_share() -> None:
    result = OPS.verdict(809, 0.03, ticks=60, seconds=1800)
    assert (result.outcome, result.numbers["max_row_bytes"]) == ("PASS", 809)


def test_ops_fails_a_row_over_4_kb_and_names_the_interval_fallback() -> None:
    result = OPS.verdict(5000, 0.03, ticks=60, seconds=1800)
    assert (result.outcome, result.reason, result.fallback) == (
        "FAIL",
        "the row is over its line",
        OPS.FALLBACK,
    )


def test_mem_passes_at_the_pc_numbers_within_the_ram_line() -> None:
    result = p_mem.judge(p_mem.PC_QUALITY, memory_mb=2000, pc=p_mem.PC_QUALITY)
    assert (result.outcome, result.numbers["memory_mb"]) == ("PASS", 2000)


def test_mem_fails_on_ram_with_the_fts5_fallback() -> None:
    result = p_mem.judge(p_mem.PC_QUALITY, memory_mb=2100, pc=p_mem.PC_QUALITY)
    assert (result.outcome, result.reason, result.fallback) == (
        "FAIL",
        "FAIL on RAM",
        p_mem.FALLBACK_RAM,
    )


def test_mem_fails_when_a_type_falls_behind_the_pc() -> None:
    behind = dict(p_mem.PC_QUALITY) | {"dead-end": 1.0}
    result = p_mem.judge(behind, memory_mb=2000, pc=p_mem.PC_QUALITY)
    assert result.reason == "FAIL on quality: Hindsight is behind the PC on dead-end"
    assert result.fallback == p_mem.FALLBACK_QUALITY


def test_mem_reports_every_failed_line_with_its_fallback() -> None:
    behind = dict(p_mem.PC_QUALITY) | {"lab-to-hub": 1.0}
    result = p_mem.judge(behind, memory_mb=2500, pc=p_mem.PC_QUALITY)
    assert result.reason == (
        "FAIL on RAM; FAIL on quality: Hindsight is behind the PC on lab-to-hub"
    )
    assert result.fallback == f"{p_mem.FALLBACK_RAM} {p_mem.FALLBACK_QUALITY}"


def test_overhead_counts_hindsight_and_keeps_four_sessions_without_it() -> None:
    assert p_mem.capacity(p_mem.BASE_OVERHEAD_MB) == 4
    overhead = p_mem.derive_overhead(1800)
    assert (overhead, p_mem.capacity(overhead)) == (8192, 2)


def test_overhead_follows_the_measured_footprint_rather_than_forcing_two_sessions() -> None:
    assert p_mem.derive_overhead(100) == 6400
    assert p_mem.capacity(6400) == 3


def test_ram_record_carries_both_numbers_and_the_derived_overhead() -> None:
    result = p_mem.ram_verdict(without_mb=9000, with_mb=7200, peak_mb=1700, overhead_mb=8192)
    assert result.outcome == "PASS"
    assert (
        result.numbers["free_without_hindsight_mb"],
        result.numbers["free_with_hindsight_mb"],
    ) == (9000, 7200)
    assert result.numbers["hindsight_footprint_mb"] == 1800
    assert (
        result.numbers["sessions_with_hindsight"],
        result.numbers["sessions_without_hindsight"],
    ) == (2, 4)


def test_ram_record_fails_when_a_number_is_missing() -> None:
    assert p_mem.ram_verdict(
        without_mb=0, with_mb=7200, peak_mb=1700, overhead_mb=8192
    ).outcome == ("FAIL")
