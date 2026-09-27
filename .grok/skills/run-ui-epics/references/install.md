# Source vs installed copy

| Copy | Path | Role |
|---|---|---|
| Source | `<ui-factory worktree>/.grok/skills/run-ui-epics` on `ui-integration` | version-controlled truth |
| Project workflow | `.grok/workflows/ui-epic-build.rhai` | `/workflow ui-epic-build` |
| User skill | `~/.grok/skills/run-ui-epics` | `/run-ui-epics` |
| User workflow | `~/.grok/workflows/ui-epic-build.rhai` | slash/workflow name |
| User plugin | `~/.grok/plugins/ui-epic-factory` | auto-trusted plugin |
| Marketplace | `~/grok-plugins/ui-epic-factory` | sibling of epic-factory |

Refresh installed copies:

```
python tools/ui_factory_cli.py setup
```

Edit source on `ui-integration` first. Do not edit only the installed
copy.

Base SHA for this lane: `7b65732fc03683476c3221889d62d23ae8ccf88e`
(`origin/integration` when the worktree was cut). Destination:
`ui-integration`. Existing branch `ui` at `af662888` is old BMAD epics
and is not this destination.

State: `C:/Users/Mubarak/Desktop/QMX-worktrees/_ui-factory/`.
Worktrees: `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-epic-*`.
After a Grok process death, `/run-ui-epics resume` rejoins git + state.
Same-process pause uses `/workflow resume <display-name>`.
