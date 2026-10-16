# Wayfinder tracker (local Markdown)

This folder is the issue tracker for the QMX methodology and agent system map. It follows the Wayfinder skill (`~/.agents/skills/wayfinder/SKILL.md`) using its local-markdown fallback, because the operator asked for no GitHub issues.

## Wayfinding operations

| Operation | How this tracker does it |
|---|---|
| The map | `MAP.md`. It carries the `wayfinder:map` label in its frontmatter. |
| A ticket | One file `tickets/<slug>.md`. The file name is the ticket's id. The `title` in its frontmatter is its name; refer to tickets by name in prose. |
| Ticket type | `type:` one of `research`, `prototype`, `grilling`, `task`. `mode:` `HITL` or `AFK`. |
| Blocking | `blocked_by:` a list of ticket slugs. A ticket is unblocked when every slug it lists has `status: closed`. |
| Claiming | Set `claimed_by:` to the session or person before any work. An open, unclaimed ticket is unclaimed. |
| Frontier | Run `python frontier.py` in this folder. It prints open, unblocked, unclaimed tickets, then blocked, claimed and closed ones. It errors on an unknown slug in `blocked_by`. |
| Resolution | Append a `## Resolution` section to the ticket, set `status: closed`, and add one line to `MAP.md` under "Decisions so far" that names the ticket and gists the answer. |
| New tickets | Create the file, then wire `blocked_by` in a second pass. Graduate fog from `MAP.md` by deleting the fog line when the ticket exists. |
| Out of scope | Close the ticket and add one line under "Out of scope" in `MAP.md`. |

## Rules for this map

- Never resolve more than one ticket per session, except research tickets.
- Every HITL ticket carries a recommended answer so the operator can accept with "yes".
- Research tickets are ready for AFK agents. They were not fired during charting (the operator's instruction to the charting agent: no sub-agents).
- Do not commit from a charting or resolving session unless the operator says so.

## Ticket frontmatter

```yaml
---
title: Workflow engine contract
type: grilling          # research | prototype | grilling | task
mode: HITL              # HITL | AFK
status: open            # open | closed
blocked_by: []          # ticket slugs
claimed_by: ""
created: 2026-10-16
closed: 2026-10-16      # only when status is closed
owner: harness owner    # optional; who answers it when not the operator
---
```

Build PRs are not tickets. They live in `../ENGINE-PLAN.md`; tickets link to it.
