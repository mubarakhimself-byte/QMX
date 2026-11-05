#!/usr/bin/env bash
# Run one of the audit's proof scripts at a check worktree, with the credential guards on.
# The scripts hard-code D:/QMX-worktrees/audit-head and read siblings under D:/Temp/audit, so this
# runs a copy of the script's folder with both paths replaced. A file holding test functions runs
# under pytest. Keep this file beside the store's env.sh.
# Usage: proof_at.sh <root|agents> <check worktree> <script path> [script args...]
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/env.sh"
env_kind=$1; check=$2; script=$3; shift 3
case "$env_kind" in
  root) python="$check/.venv/Scripts/python.exe"; cwd="$check" ;;
  agents) python="$check/qmx-agents/.venv/Scripts/python.exe"; cwd="$check/qmx-agents" ;;
  *) echo "first argument is root or agents, not $env_kind" >&2; exit 2 ;;
esac
[ -x "$python" ] || { echo "no environment at $python; run the boot recipe first" >&2; exit 2; }
script_dir=$(dirname "$script")
name=$(basename "$script")
mkdir -p "D:/Temp/audit/$(basename "$script_dir")"
copy=$(mktemp -d "D:/Temp/proof-XXXXXX")
trap 'rm -rf "$copy"' EXIT
for file in "$script_dir"/*.py; do
  sed -e "s#D:/QMX-worktrees/audit-head#$check#g" \
      -e "s#D:/Temp/audit/[a-z0-9/-]*/\([A-Za-z0-9_]*\.py\)#$copy/\1#g" \
      "$file" > "$copy/$(basename "$file")"
done
export PYTHONPATH="$PYTHONPATH;$copy"
cd "$cwd" || exit 2
if grep -q '^def test_' "$copy/$name"; then
  "$python" -m pytest "$copy/$name" -q -s -p no:cacheprovider --no-cov --basetemp="$copy/t" "$@"
else
  "$python" "$copy/$name" "$@"
fi
