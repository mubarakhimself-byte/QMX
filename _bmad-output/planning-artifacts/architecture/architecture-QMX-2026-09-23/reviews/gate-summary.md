# Reviewer gate — 2026-09-23

Lint: clean.

Applied:

- Named parent amendments for AD-8 (optional authoring instance + `selected_refs` kind `instance_id`) and AD-24 (`caller_kind`).
- Home invoke requires exactly one selected instance; envelope `instance_id` still required.
- `view:*` and copilot profile are not contribution points.
- Retry default is none/read only; never-retry, unknown-manual, unknown-blocked, CAS conflict, outbox identity preserved.
- Nested workflow is one nested Mission/JobHandle; include-at-author is a new template version.
- `failure_class=view` not widget-as-invoke.
- json-render snapshot v0.21.0 (still unpinned).
- AD-9 graduation path (loop/template → pack export).

Not operator-accepted. Not Codex-ratified.
