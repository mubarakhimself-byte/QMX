"""Run named quality profiles. Verdicts come from command exit codes."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ui_factory.config import FactoryConfig, load_profiles
from ui_factory.evidence import (
    CommandResult,
    EvidenceRecord,
    dirty_fingerprint,
    evidence_ok,
    is_stale,
    read_evidence,
    sha256_text,
    toolchain_fingerprint,
    write_command_log,
    write_evidence,
)
from ui_factory.gitops import observed_toolchain
from ui_factory.paths import FIXTURE_HOST, PRODUCT_HOST


def _parse_test_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for kind in ("passed", "failed", "skipped", "error"):
        match = re.search(rf"(\d+)\s+{kind}", text, re.IGNORECASE)
        if match:
            counts[kind] = int(match.group(1))
    vitest = re.search(r"Tests\s+(\d+)\s+passed", text)
    if vitest:
        counts["passed"] = int(vitest.group(1))
    ran = counts.get("passed", 0) + counts.get("failed", 0)
    if ran:
        counts["ran"] = ran
    return counts


def _is_test_command(name: str, argv: Sequence[str]) -> bool:
    blob = " ".join(argv).lower()
    return any(
        token in blob
        for token in ("pytest", "vitest", "playwright", "poe test", "run test")
    )


def _which(binary: str) -> str | None:
    return shutil.which(binary)


def _expand(template: str, mapping: Mapping[str, str]) -> str:
    out = template
    for key, value in mapping.items():
        out = out.replace("{" + key + "}", value)
    return out


def applicable_profiles(
    worktree: Path,
    changed_files: Sequence[str],
    *,
    user_facing: bool,
    needs_backend: bool,
) -> list[str]:
    names: list[str] = []
    profiles = load_profiles()
    files = [f.replace("\\", "/") for f in changed_files if f]
    ui_ext = any(f.endswith((".ts", ".tsx", ".svelte", ".css", ".js")) for f in files)
    product_touch = any(f.startswith(PRODUCT_HOST + "/") or f == PRODUCT_HOST for f in files)
    py_touch = any(f.endswith(".py") for f in files)
    ui_required = user_facing or ui_ext or product_touch
    if py_touch or not ui_required:
        names.append("python")
    if ui_required:
        names.extend(["ui-format", "ui-lint", "ui-types", "ui-build", "ui-unit"])
        names.append("ui-playwright")
        if needs_backend:
            names.append("ui-contract")
        if user_facing:
            names.append("ui-reticle")
    if "python" not in names:
        names.insert(0, "python")
    known = set(profiles.keys())
    return [n for n in names if n in known]


def run_command(
    *,
    name: str,
    argv: list[str],
    cwd: Path,
    log_dir: Path,
    env: Mapping[str, str] | None,
    timeout: int,
) -> CommandResult:
    if not argv:
        return CommandResult(
            name=name,
            argv=[],
            cwd=str(cwd),
            exit_code=1,
            duration_ms=0,
            stdout_sha256="",
            stderr_sha256="",
            log_path="",
            skipped=True,
        )
    binary = argv[0]
    missing_named = (
        binary not in {"python", "uv", "pnpm", "cmd", "git"}
        and _which(binary) is None
        and shutil.which(binary) is None
        and not Path(binary).exists()
    )
    if missing_named:
        return CommandResult(
            name=name,
            argv=argv,
            cwd=str(cwd),
            exit_code=127,
            duration_ms=0,
            stdout_sha256="",
            stderr_sha256="",
            log_path="",
            missing_tool=True,
        )
    merged = os.environ.copy()
    if env:
        merged.update(dict(env))
    start = time.perf_counter()
    proc = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=merged,
        shell=False,
    )
    duration = int((time.perf_counter() - start) * 1000)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    log_path = write_command_log(log_dir, name, stdout, stderr)
    counts = _parse_test_counts(stdout + "\n" + stderr)
    if _is_test_command(name, argv):
        counts["required"] = max(counts.get("required", 0), 1)
        if "ran" not in counts:
            counts["ran"] = 0
    return CommandResult(
        name=name,
        argv=argv,
        cwd=str(cwd),
        exit_code=int(proc.returncode),
        duration_ms=duration,
        stdout_sha256=sha256_text(stdout),
        stderr_sha256=sha256_text(stderr),
        log_path=str(log_path),
        test_counts=counts,
    )


def _profile_commands(
    profile: Mapping[str, Any],
    *,
    worktree: Path,
    host_root: Path,
) -> list[tuple[str, list[str], Path, int]]:
    mapping = {
        "worktree": str(worktree),
        "host": str(host_root),
        "python": "python",
    }
    rows: list[tuple[str, list[str], Path, int]] = []
    commands = profile.get("commands") or []
    timeout = int(profile.get("timeout_seconds") or 300)
    cwd_key = str(profile.get("cwd") or "worktree")
    cwd = host_root if cwd_key == "host" else worktree
    if isinstance(commands, list):
        for item in commands:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "cmd")
            argv_raw = item.get("argv") or []
            argv = [_expand(str(a), mapping) for a in argv_raw]
            rows.append((name, argv, cwd, int(item.get("timeout_seconds") or timeout)))
    return rows


def find_host_root(
    worktree: Path,
    roots: Sequence[str],
    *,
    factory_mode: str = "product",
) -> Path | None:
    if factory_mode == "fixture":
        fixture = worktree / FIXTURE_HOST
        if (fixture / "package.json").is_file():
            return fixture
        return None
    product = worktree / PRODUCT_HOST
    if (product / "package.json").is_file():
        return product
    for rel in roots:
        if rel == FIXTURE_HOST:
            continue
        path = worktree / rel
        if path.name == "qmx-ui" and (path / "package.json").is_file():
            return path
    return None


def run_profiles(
    *,
    config: FactoryConfig,
    worktree: Path,
    unit_id: str,
    story_hash: str,
    candidate_sha: str,
    profile_names: Sequence[str],
    user_facing: bool,
    evidence_dir: Path,
    factory_mode: str = "product",
    reticle: Mapping[str, str] | None = None,
) -> tuple[EvidenceRecord, bool, str]:
    profiles = load_profiles()
    host = find_host_root(
        worktree, config.host_app_roots, factory_mode=factory_mode
    )
    toolchain = toolchain_fingerprint(observed_toolchain())
    dirty = dirty_fingerprint(worktree)
    existing = evidence_dir / f"quality-{unit_id}.json"
    if existing.is_file():
        previous = read_evidence(existing)
        stale = is_stale(
            previous,
            candidate_sha=candidate_sha,
            story_hash=story_hash,
            toolchain=toolchain,
            dirty=dirty,
            profiles=list(profile_names),
        )
        if stale == "":
            ok, reason = evidence_ok(previous, require_reticle=user_facing)
            return previous, ok, "reused evidence" if ok else reason
    results: list[CommandResult] = []
    log_dir = evidence_dir / "logs" / unit_id
    for name in profile_names:
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            results.append(
                CommandResult(
                    name=name,
                    argv=[],
                    cwd=str(worktree),
                    exit_code=1,
                    duration_ms=0,
                    stdout_sha256="",
                    stderr_sha256="",
                    log_path="",
                    skipped=True,
                )
            )
            continue
        if str(profile.get("cwd") or "") == "host" and host is None:
            results.append(
                CommandResult(
                    name=name,
                    argv=[],
                    cwd=str(worktree),
                    exit_code=1,
                    duration_ms=0,
                    stdout_sha256="",
                    stderr_sha256="",
                    log_path="",
                    missing_tool=True,
                    test_counts={"required": 1, "ran": 0},
                )
            )
            continue
        host_path = host if host is not None else worktree
        env_raw = profile.get("env")
        env_map: dict[str, str] | None = None
        if isinstance(env_raw, dict):
            env_map = {str(k): str(v) for k, v in env_raw.items()}
        for cmd_name, argv, cwd, timeout in _profile_commands(
            profile, worktree=worktree, host_root=host_path
        ):
            results.append(
                run_command(
                    name=f"{name}:{cmd_name}",
                    argv=argv,
                    cwd=cwd,
                    log_dir=log_dir,
                    env=env_map,
                    timeout=timeout,
                )
            )
    reticle_map = dict(reticle or {})
    verdict = reticle_map.get("verdict", "")
    source = reticle_map.get("source", "")
    if not user_facing:
        verdict = "not-applicable"
        source = "not-applicable"
    elif verdict == "":
        verdict = "missing"
        source = source or "missing"
    record = EvidenceRecord(
        kind="quality",
        unit_id=unit_id,
        candidate_sha=candidate_sha,
        story_hash=story_hash,
        toolchain=toolchain,
        dirty_fingerprint=dirty,
        commands=results,
        reticle_verdict=verdict,
        reticle_tool=reticle_map.get("tool", ""),
        reticle_journey=reticle_map.get("journey", ""),
        reticle_source=source,
        profiles=list(profile_names),
    )
    write_evidence(evidence_dir, record)
    ok, reason = evidence_ok(record, require_reticle=user_facing)
    return record, ok, reason
