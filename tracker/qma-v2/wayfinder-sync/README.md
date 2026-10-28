# Wayfinder tracker (local Markdown): sync and connect

This folder is the issue tracker for the "sync to my storage, and connect from the screen" map. It follows the Wayfinder skill (`~/.claude/skills/wayfinder/SKILL.md`) with the local-markdown fallback, the same way `../wayfinder/` does for the methodology map. That map is a separate effort; nothing here edits it.

## Wayfinding operations

| Operation | How this tracker does it |
|---|---|
| The map | `MAP.md`. It carries the `wayfinder:map` label in its frontmatter. |
| A ticket | One file `tickets/<slug>.md`. The file name is the ticket's id. The `title` in its frontmatter is its name; refer to tickets by name in prose. |
| Ticket type | `type:` one of `research`, `prototype`, `grilling`, `task`. `mode:` `HITL` or `AFK`. |
| Blocking | `blocked_by:` a list of ticket slugs. A ticket is unblocked when every slug it lists has `status: closed`. |
| Claiming | Set `claimed_by:` to the session or person before any work. An open, unclaimed ticket is unclaimed. |
| Frontier | Run `python frontier.py` in this folder. It prints open, unblocked, unclaimed tickets, then blocked, claimed and closed ones. It errors on an unknown slug in `blocked_by` or a cycle. |
| Resolution | Append a `## Resolution` section to the ticket with its evidence, set `status: closed` and `closed:`, and add one line to `MAP.md` under "Decisions so far" that names the ticket and gists the answer. |
| New tickets | Create the file, then wire `blocked_by` in a second pass. Graduate fog from `MAP.md` by deleting the fog line when the ticket exists. |
| Out of scope | Close the ticket (if one exists) and add one line under "Out of scope" in `MAP.md`. |

## Rules for this map

- **Stand-in resolutions.** The charting agent resolved every ticket whose answer the inputs settle (his words of 2026-10-28, a ruling, a primary source, a measured fact or the code), standing in for the operator under the coordinator's brief. Those tickets say `mode: AFK` and `resolved_by: map agent (stand-in)`. The coordinator checks them; a wrong one is reopened, not patched.
- **Tickets for him** say `mode: HITL` and `owner: operator`. Each carries a recommended answer in plain words that he can accept with "yes". They stay unclaimed until he answers.
- Never resolve more than one HITL ticket per session.
- Planning only: tickets hold decisions, never code. Build PRs are not tickets; the planner cuts them from the design.

## Evidence shorthand

| Short | Means |
|---|---|
| `words:N` | line N of `../research/sync/01-his-words-2026-10-28.txt` (his dictations are the `=== OPERATOR` blocks at lines 8, 70, 101, 151, 185, 219) |
| `explore:` `inv:` `src:` `align:` | `../research/sync/00-backup-explore.md`, `02-inventory.md`, `03-primary-sources.md`, `04-alignment-and-domain.md` |
| `sources/<file>` | the saved primary source under `../research/sync/sources/` |
| `R<n>` | ruling n in `../research/methodology/26-operator-rulings-and-alignment.md` (105 to 145 bind; the latest wins) |
| `design:` `plan:` | `../research/methodology/62-local-first-design.md`, `../BACKUP-RESTORE-PLAN.md` |
| `UIH §n` | section n of `../UI-HANDOFF.md` |
| `BK/` `HO/` `QX/` | `D:/QMX-worktrees/bld-br4/qmx-agents/packages/` + `qmx-home/src/qmx_home/backup/`, `qmx-host/src/qmx_host/`, `qmx-control/src/qmx_control/` (branch `build/br4` at `1e9f695a`, PRs 225 to 228) |
| `PK/` | `D:/QMX-worktrees/bld-br4/qmx-agents/packages/` |

## Ticket frontmatter

```yaml
---
title: What a sync sends, decided once by class
type: grilling          # research | prototype | grilling | task
mode: AFK               # HITL (his) | AFK (settled from evidence)
status: closed          # open | closed
blocked_by: []          # ticket slugs
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28      # only when closed
resolved_by: map agent (stand-in)
owner: operator         # only on his tickets
---
```
