#!/usr/bin/env bash
# The whole-repo check at one commit, run by the coordinator in the background. Every step runs even
# if an earlier one fails, because tools/ci.py stops at the first failure and would hide the tests.
# It is the audit's tools/run_tests.sh with the commit and the output folder as arguments, so its
# SUMMARY.txt reads line for line against D:/QMX-worktrees/audit-ship/tests/SUMMARY.txt.
# Safe to run again: a finished run exits at once, a live run is left alone, a run killed by a power
# cut has its lock and copy cleared and starts over. Keep this file beside the store's env.sh.
# Usage: run_tests.sh <sha> <out-folder>
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/env.sh"
HEAD=$1
OUT=$2
REPO=C:/Users/Mubarak/Desktop/QMX
COPY=D:/Temp/repair-ci
LOCK=D:/QMX-worktrees/.ci-lock
mkdir -p "$OUT"
if [ -f "$OUT/SUMMARY.txt" ] && grep -q '^DONE$' "$OUT/SUMMARY.txt"; then echo "already finished"; exit 0; fi
if [ -d "$LOCK" ]; then
  read -r who pid < "$LOCK/owner" 2>/dev/null || { who=none; pid=0; }
  if [ "$who" != "repair" ]; then echo "BLOCKED: another run holds $LOCK: $who $pid"; exit 3; fi
  if kill -0 "$pid" 2>/dev/null; then echo "already running as $pid"; exit 0; fi
  rm -rf "$LOCK"
fi
mkdir "$LOCK" || { echo "BLOCKED: could not take $LOCK"; exit 3; }
echo "repair $$" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
: > "$OUT/SUMMARY.txt"
note() { echo "$1" | tee -a "$OUT/SUMMARY.txt"; }
git -C "$REPO" worktree remove --force "$COPY" 2>/dev/null
rm -rf "$COPY"
git -C "$REPO" worktree prune
git -C "$REPO" worktree add -q --detach "$COPY" "$HEAD" || { note "BLOCKED: could not create $COPY"; exit 3; }
cd "$COPY" || exit 3
uv sync --frozen > "$OUT/sync-root.log" 2>&1; note "sync root rc=$?"
(cd qmx-agents && uv sync --frozen --all-packages --all-groups > "$OUT/sync-agents.log" 2>&1); note "sync agents rc=$?"
step() {
  name=$1; shift
  started=$(date +%s)
  timeout 10800 "$@" > "$OUT/$name.log" 2>&1
  rc=$?
  note "$name rc=$rc seconds=$(( $(date +%s) - started ))"
}
step test-all uv run --no-sync python tools/test_all.py
for task in money-path-scan secret-scan mock-data-scan ambient-scan; do step "$task" uv run --no-sync python -m poethepoet "$task"; done
step corpus-gate uv run --no-sync python -m pytest qml/tests/test_check_layers.py -k corpus -q -p no:cacheprovider
for space in . qmx-agents qmx-agents/packages/qmx-control qmx-agents/packages/qmx-tools qmx-agents/packages/qmx-apps qmx-agents/packages/qmx-broker qmx-agents/packages/qmx-remote qmx-agents/packages/qmx-ledger qmx-agents/packages/qma-harness qmx-agents/packages/qmx-engine qmx-agents/packages/qmx-host qmx-agents/packages/qmx-library qmx-agents/packages/qmx-judge qmx-agents/packages/qmx-router qmx-agents/packages/qmx-memory qmx-agents/packages/qmx-hub qmx-agents/packages/qmx-home; do
  label=$(basename "$space"); [ "$space" = "." ] && label=root
  for task in fmt-check lint types; do (cd "$space" && step "$task-$label" uv run --no-sync python -m poethepoet "$task"); done
done
note "--- failed tests"
grep -hE '^(FAILED|ERROR) ' "$OUT/test-all.log" | cut -c1-200 | sort -u | tee -a "$OUT/SUMMARY.txt" | wc -l | sed 's/^/count /' | tee -a "$OUT/SUMMARY.txt"
note "--- suite table"
sed -n '/^| Suite/,$p' "$OUT/test-all.log" >> "$OUT/SUMMARY.txt"
cd "$REPO" && git worktree remove --force "$COPY"
note DONE
