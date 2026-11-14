# Slice prefixes in use

Every program's slice ids start with its own prefix, because worktrees are named `slice-<id>` and branches `slice/<id>`. A planner registers a prefix here only after `git ls-remote --heads origin "slice/<prefix>-*"` and `grep -l "^| <prefix>-" D:/QMX-worktrees/*/tracker/*/SLICES.md` both print nothing.

- rc: risk build (rc-01 to rc-69), 2026-11
