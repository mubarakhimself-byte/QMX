# Workflow — one UI epic

Launch `ui-epic-build.rhai` with the `workflow` tool as `script` (read the
file, pass the text). Optionally replace only `meta.name` with
`ui-epic-NNN-slug`. Destination is `args.destination_branch`
(`ui-integration`). Never pass `integration`.

## Args

```
{
  "worktree": "<abs path>",
  "branch": "ui-epic/NNN-slug",
  "destination_branch": "ui-integration",
  "stories": [{
    "id": "70.1",
    "title": "...",
    "brief": "...",
    "files": ["apps/host/..."],
    "user_facing": true,
    "already_commit": "<optional hash>"
  }],
  "quality": {
    "lint": "uv run poe lint",
    "typecheck": "uv run poe types",
    "test": "uv run poe test"
  },
  "factory_cli": "python tools/ui_factory_cli.py",
  "review_skill": "<abs bmad-code-review/SKILL.md or empty>",
  "review_adapter": "<abs unattended-adapters.md>",
  "frontend_entry": "<abs design-system-entry.md>",
  "build_model": "grok-4.6"
}
```

`already_commit` skips rebuild and re-runs quality. A story commit means
built, not verified.

## Budget

`stories.len * 10 + 12` (build + up to 4 verifies + up to 3 fixes +
runtime + review + headroom).

## On completion

Read `all_green` and `blocking`. Green and empty blocking → merge gate
against `destination_branch`. Review never overrides a red command suite.
A non-empty `blocking` list keeps `all_green` false.
