# PR body template and skill shortlist (2026-11-12)

Sources read: tstack (t3dotgg, cloned at depth 1, nothing run), pstack (poteto: `poteto-mode/playbooks/opening-a-pr.md`, `technical-writing`, `unslop`, `principle-*`, `blast-radius`, `show-me-your-work`), Matt Pocock (`writing-for-agents`, `code-review`, `tdd`; source confirmed in `~/.agents/.skill-lock.json`), and the in-house `to-kanban`, `queue-publish`, `ship-check`.

## Why PRs 383 and 376 are hard to read

- PR 376 opens with branch genealogy and SHAs ("RC-21, stop B, slice 6. Base ..."). The plain explanation of what it does for a trade sits in the sixth section.
- Both are long essays (376 runs past 2,000 words). Most sentences carry three or more code names (`risk_fraction`, `K9 6`, `own-r-step@1`, `COMPILER_FORMAT_VERSION`) that are never explained.
- Each has a 13 to 15 row test table inline. pstack and tstack both say to link this, not paste it.
- Process sections ("Files outside the Files block", "Departures from the plan", "The join, conflict by conflict") serve the coordinator, not the owner or a reviewer.
- Open issues are scattered. 383 mentions "a finding for a later PR", "RC-26 owns", and two long runs that never finished, each in a different section. A later agent cannot grep for them.
- Neither has a one-line answer to "can this touch money or live trading?"

## Final PR body (v2, after comparing Matt Pocock's /pr skill)

Matt Pocock's `pr` skill (aihero.dev/skills-pr, `npx skills@latest add mattpocock/skills --skill=pr`) has three sections. The Summary is a small visual (pseudocode, call tree, file tree, shaped diff or Mermaid), not prose. Evidence is a before and after, never "tests are green". Merge Danger is a one-way or two-way door plus the blast radius. v2 keeps all three and adds what QMX needs: a plain-words line for the owner, and searchable `OPEN:` and `DOC:` lines. No model or tool credit line anywhere. The owner ruled on 12 November that PRs and commits carry no "Generated with" or "Co-Authored-By" line; sign as Mubarak, or not at all.

```markdown
**In plain words:** <one or two sentences, no code names: what is true now that wasn't before.>

## Summary
<the smallest visual that shows the change's shape: pseudocode, call tree,
file tree or shaped diff. A short line of text beside it, no preamble.>

## Evidence
- Before: <the exact test or output that failed, as pseudocode or the real line>
- After: <the same, now passing>

## Merge danger
**Door:** <one-way | two-way>, because <reason>. **Blast radius:** <what could break if this is wrong, and the one fact proved safe, with the command that proved it>

## Open issues
- OPEN: <what is wrong or unproven> | where: <path> | owner: <slice id or none>

## Docs to update
- DOC: <doc path> | <what changed>   (or "DOC: none")

Shipped by Mubarak.
```

QMX's one-way doors, which the agent reads before it makes the door call: a stored data format change, a compiler format bump, a deleted public API, anything that sends outward (orders, messages), and anything near the fixed lines (exits, kill switch, keys, money). Under about 40 lines in all. Long tables and logs go to `evidence/<id>/` with one link.

## First proposed PR body (v1, superseded by v2 above)

Title: plain words about the effect, not the mechanism (tstack `file-pr`). Example: "Let a unit's risk size adjust itself inside the range you set". Put the ticket id at the end in brackets.

Keep the whole body under about 40 lines (pstack). Long logs, tables and genealogy go to `evidence/<ticket>/` and get one link.

```markdown
## In plain words
<2-3 sentences a non-technical owner understands. What was wrong or missing,
what is true now. No code names.>

**Money and live trading:** <none | how it touches them and why it is safe>
**Status:** <ready for review | blocked on X>. **Not proven:** <none | one line>

## Why
<1-3 sentences: the problem and the approach.>

## What changed
- <1-3 bullets. Name a file or symbol only when it carries the change.>

## Scope
- Covers: <...>
- Leaves out: <follow-ups and known gaps, with the ticket that owns each>

## Blast radius
<1-2 sentences: what else this could break, and the one fact that makes it
safe, with the script or test that proved it.>

## Verification
- <run path> -> <outcome>  (1-3 bullets; full table at evidence/<ticket>/)

## Open issues
- OPEN: <what is wrong or unverified> | where: <path> | owner: <ticket or none>

## Docs to update
- DOC: <docs/path.md> | <what changed in behavior>   (or "DOC: none")

## Review
<reviewer model, rounds, verdict. Findings declined, one line each with reason.>

Made with <model> in <harness>.
```

Where each section comes from:

| Section | Source |
| --- | --- |
| Plain title, "In plain words" first | tstack `file-pr` (lead with the problem, not an inventory) |
| Money line | New. QMX's own rule that agents cannot touch money |
| Status and "Not proven" | tstack `full-stop` handoff verdict, `ship-check` phrase "cannot confirm from the record" |
| Why, What changed, Scope, Blast radius, Verification | pstack `opening-a-pr.md`, in its order and size limits |
| Blast radius "one fact proved" | pstack `blast-radius` |
| Open issues with a fixed `OPEN:` prefix | tstack `babysit-pr` (declined findings become follow-ups) and `modernize` (say what could not be verified). The prefix is new, so a bug-hunting agent can grep merged PRs |
| Docs to update with `DOC:` prefix | New. Feeds a docs agent running documentation-factory change mode |
| Review line | tstack `sol-loop` and `council` (rounds and verdict in the description, not a comment) |
| Model and harness footer | tstack `file-pr` |

Writing rules for the body: `technical-writing` then `unslop` (both pstack).

## Skill shortlist

Builders:

- `C:/Users/Mubarak/.claude/skills/unslop/SKILL.md` (pstack). Neutral as is.
- `C:/Users/Mubarak/.claude/skills/technical-writing/SKILL.md` (pstack). Neutral. Long; could be trimmed to the "sentences" and "voice" sections for PR writing.
- `C:/Users/Mubarak/.claude/skills/principle-prove-it-works/SKILL.md`, `principle-laziness-protocol`, `principle-sequence-verifiable-units` (pstack). Short and neutral.
- `C:/Users/Mubarak/.claude/skills/tdd/SKILL.md` (Matt Pocock). Neutral.
- tstack `file-pr` (`C:/Users/Mubarak/AppData/Local/Temp/claude/research/tstack/skills/file-pr/SKILL.md`). Needs edit: replace its body advice with the template above. It has no Claude-only tools.

Reviewers:

- `C:/Users/Mubarak/.claude/skills/blast-radius/SKILL.md` (pstack). Needs edit: delete step 6 (run as an `arena`, which spawns models) and the pointers to `how` and `why`.
- `C:/Users/Mubarak/.claude/skills/code-review/SKILL.md` (Matt Pocock). Needs edit: it spawns two parallel sub-agents, asks the user for the fixed point and spec, and depends on `/setup-matt-pocock-skills`. Rewrite as two passes in one agent, base branch given in the brief. The Fowler smell list is worth keeping.
- tstack `leaving-pr-comments`. Neutral. Borrow too the `sol-loop` severity scale (blocker, should, nit) and its finding format, not the skill.

Coordinator:

- tstack `modernize`. Neutral. Fits stacked rc-* branches: decide MODERNIZE, REWORK or CLOSE before rebasing.
- `C:/Users/Mubarak/.claude/skills/show-me-your-work/SKILL.md` (pstack). Needs edit: delete the "spawn a subagent on a different model family" step.
- `C:/Users/Mubarak/.claude/skills/writing-for-agents/SKILL.md` (Matt Pocock). Use only when editing these skills.

## Skills to avoid

- tstack `full-send`: grants itself merge rights and asks the user through `AskUserQuestion`. QMX rule: never merge unasked.
- tstack `full-stop`, `takeover`: chain into `full-send`, `sol-loop` and `babysit-pr`.
- tstack `council`, `sol-loop`: spawn reviewers on other providers through T3 `delegate_task`. Score tables add noise.
- tstack `babysit-pr`: built around T3 `watch_pull_request`, the Claude Monitor tool and a Python watcher script. Its "keep the PR small, decline extras as follow-ups" paragraph is worth copying into the reviewer brief.
- pstack `interrogate`, `arena`, `swarm`, `no-comments`, and `opening-a-pr.md` as written: all spawn subagents. The playbook also calls `/deslop` from a kit that is not installed.
- In-house `to-kanban`, `queue-publish`, `ship-check`: tied to the retired factory Board and `adws/ship_report.py`, and they ask the operator. Keep only `ship-check`'s "cannot confirm from the record" rule.
