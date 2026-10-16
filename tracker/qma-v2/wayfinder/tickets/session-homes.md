---
title: Session homes (assumption A4; spec)
type: task
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Matches ruling 12; store the home where no harness edit is needed (ruling 24)."
---

## Question

What a session's home is, how a session gets one, what travels with the session, and how a session born in the Lab or Portfolio is brought into the hub and back again without losing its context.

## Why it matters

Correction 5: home is where a session was born; the session is visible and continuable in both the hub and its home. The UI today rewrites `origin` to Main in `absorb()` and has no way back (`10` §3, mismatch 3). The backend session carries only `origin="qma"` and `parent_id` (`05` gap 3). Capability packs, memory scopes, system prompts and the UI badge key on this.

## Recommended answer

`home = {kind, project_id}` stored on the control session at start; kinds general, lab, portfolio, library, app; never changed. The home sets the default packs and the autonomy row. Packs, workspace, memory scope and history travel with the session wherever it is opened. The hub lists every session with a home badge; "view in hub" keeps the home; "open in its home" is the way back. Child sessions inherit the parent's home; background chats carry the home of the workflow that started them. The UI fix: replace `absorb()` with a view switch, keep `origin` untouched, add the return link, and word the handoff block "born in the Lab".

## What the session does

Grilling on the kinds and on what a combined session shows. `domain-modeling` adds home, project, workspace, pack to the glossary. Output: the home table, the field name for today's UI session, the UI fix list.

## Unblocks

Capability packs, memory scopes and lessons, system-prompt design, methodology umbrella; the UI badge and the `absorb()` fix.

## Sources

`BACKLOG.md` B30, ruling 10-13 Q4; `05-qmx-today.md` §6, gap 3; `10-ui-depth.md` §3, §6 mismatches 2 and 3; `UI-NOTES.md` §10; corrections 5, F.
