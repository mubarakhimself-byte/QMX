---
title: One folder shape (C1)
type: task
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Ruling 19; keep pending/ outside the hashed folder (20b finding 4)."
---

## Question

Write the one folder shape for agents, workflows, variants, skills, packs and mini apps, each a valid Claude plugin plus `qmx.toml`, with the Eve rules (path is the name, defaults in the same slots, tests and evals beside the code), versions by semver plus content hash, `pending/` for agent-written edits, archive never delete, and a validator script.

## Why it matters

Central piece C1 in `19` section 4. Every template folder, every variant, every pack and every app is this shape. The Claude Agent SDK loads a plugin by path with no custom loader, so the outer folder is the plugin format; QMX adds only what it lacks. `qmx agent info` and `qmx app check` read it.

## What the session does

AFK task. Write `FOLDER-FORMAT.md` (slots per kind, `qmx.toml` keys, lifecycle states, version rules, what never lives in a folder) and `validate_folder.py` (plugin.json valid, Agent Skills frontmatter valid, path escapes, literal secrets, unknown keys, tests and evals present). Rewrite the three empty QMX skills as worked examples. Hand back the spec, the validator output and one example of each kind.

## Unblocks

Skill format and verbs, agents and workflows as folders, shared blocks catalogue, app check command, methodology umbrella.

## Sources

`14-folders-miniapps-browser.md` §1, §2.5; `01-bmad.md` §Q1; `02-pocock-pstack.md` §3 Agent Skills; `19` C1.
