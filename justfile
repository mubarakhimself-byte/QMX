# QMX recipes.

# `.env` reaches every recipe through this.
set dotenv-load
# just has no `sh` on Windows PATH by default; cmd.exe is always there. `just`
# only applies `windows-shell` when actually running on Windows, so Linux/mac
# keep the default shell - the server is unaffected.
set windows-shell := ["cmd.exe", "/c"]

# QMN operations toolkit (DevOps only; never a trading control). COMP-QMN /
# TN-16 / AR-79 / DEC-0202. Closed allow-list lives in qmn/deploy/boundary.py.
import "./qmn/deploy/justfile-recipes/node.just"

# list every recipe
default:
    @just --list

# probe: shell + dotenv + recipe execution actually work (no tokens spent)
doctor:
    uv run python -c "print('doctor ok')"

# Run every Python suite in its owning environment and print the results.
test-all:
    uv run python tools/test_all.py

# The PR workflow calls this same runner; suites never overlap.
ci:
    uv run python tools/ci.py
