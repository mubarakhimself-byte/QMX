---
title: Capability packs across homes
type: grilling
mode: HITL
status: closed
blocked_by: [session-homes, plugin-unit-and-loading]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Matches rulings 12-13; packs are fixed at launch (20b finding 16), so adding one is a relaunch."
closed: 2026-10-16
---

## Question

How one session composes Lab, Portfolio, Library, a workflow and a mini app at once, so the hub copilot has every Lab and Portfolio capability without becoming a split agent, and a Lab session opened in the hub keeps its Lab tools and context.

## Why it matters

Correction F. Lab tools differ from hub tools; the hub must still reach all of them. The hub is a place. The earlier draft had "modes"; packs replace them.

## Recommended answer

A pack is a plugin-shaped folder: tools, skills, agent folders, hooks, views, a memory scope, an autonomy row. The home sets the default packs; a session may add packs; packs travel with the session wherever it is opened. Tool names are namespaced by pack (`lab.*`, `portfolio.*`, `library.*`, `app.<id>.*`, `wf.<name>.*`). When two packs disagree on an autonomy row, the stricter row wins for that object. Portfolio writes stay proposals in any combination.

## What the session does

Grilling on what a combined session should show (which packs are loaded, which rules apply) and on default packs per home. Output: the pack table and the composition rule.

## Unblocks

Lab agent tools, portfolio copilot purpose, system-prompt design, methodology umbrella.

## Sources

`12` section (b); `10-ui-depth.md` §3 message aim and reach; `05-qmx-today.md` §6; corrections F, G.

## Resolution

Resolved. Engine AD-33 (`qmx_engine.packs`, loaded by node scope) and Lab AD-14 (the Lab copilot pack is a plugin with Effects). Packs are fixed at launch (20b finding 16). (Map rewrite 2026-10-16.)
