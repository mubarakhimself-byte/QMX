---
title: Plugins as the contract to mini apps (assumption A3; spec)
type: task
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Plugins as the mini-app contract stands (ruling 10); changing the harness plugin loader conflicts with ruling 24."
---

## Question

What a QMX plugin is, how every mini app ships as one so the hub and agents reach it without custom wiring, how plugins are signed and trusted, and how the harness loads approved plugins next to the SHA-locked core.

## Why it matters

Correction 2: plugins are the contract to mini apps, before any general Lab or Portfolio plugins. The harness loads exactly one plugin and refuses any other hash (`05` gap 4); that rule must change. Capability packs (correction F) use the same unit.

## Candidates

| Candidate | What must be true |
|---|---|
| (a) Core plugin SHA-locked in code; a registry in `control.db` (id, version, sha256, trust, enabled, homes) for app plugins he approved; the harness composes core plus enabled plugins per session and verifies every hash; agent-built plugins install disabled; trust from the approval record. | Composition into one Claude home works without name clashes (namespaced tools). |
| (b) One plugin per home, each locked in code. | Contradicts "every app is a plugin". |
| (c) Unlocked plugins. | Never; the interrogate verdict removed agent-writable settings. |

## Recommended answer

(a). The unit: `plugin.toml`, MCP tools, skills, agent folders, hooks, views, optional memory scope and autonomy row. An app's plugin installs with the app and leaves the active set when the app is archived. Packs reuse the same unit. Platform analogues (Shopify apps, VS Code extensions) pending study 14.

## What the session does

Grilling on vocabulary (plugin, pack, mini app, skill, agent) and on the install card and trust ladder he wants to see. Output: the plugin unit table and the loading rule.

## Unblocks

Capability packs, agent and workflow folders, mini-app lifecycle, mini-app data contract, methodology umbrella.

## Sources

`05-qmx-today.md` §1 gaps 3 and 5, §6; `BACKLOG.md` B23, B31, B32; `01-bmad.md` modules; `12` sections (b), (g); corrections 2, F.
