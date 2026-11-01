---
name: build-unit
description: Write a QMX trading unit and check it until it has no errors. Use when the operator asks for a unit, a strategy, a trading idea turned into rules, or a change to a unit he has.
allowed-tools: mcp__qmx_unit__new mcp__qmx_unit__check mcp__qmx_unit__explain mcp__qmx_blocks__find mcp__qmx_blocks__get mcp__qmx_blocks__check mcp__qmx_blocks__match
---

# Build a unit

A unit is one JSON document: what it trades, its logic as blocks in slots, its exits, its sizer
and its numbers. You write the document. The checker tells you what is wrong with it. You do not
decide that it is right; the check does.

## What you promise

- A unit draft in his Library, and nothing else. `unit_new` and `unit_check` save drafts only.
- You never publish, test, promote or trade a unit. His yes publishes it. QMB tests it after that.
- You never save a unit with `library_save`. That saves a plain artifact, not a unit.
- You never write a `bot` or a `strategy`. The unit is the only shape.

## The loop

1. Start from a template. Call `unit_new`. The dummy trend pullback is the default, and it
   already passes. Pass `overrides` to change fields by JSON pointer, for example
   `{"/title": "Gold pullback"}`. Keep the `item` it returns.
2. Read what you started from. Call `unit_explain` with the `item`. It lists the markets, the
   slots and their blocks, the exits, the sizer and every number.
3. Change the document to fit his request. Before you write any block, search the dictionary
   for one that already does the job (see Blocks). Keep every block you use in `pins`.
4. Check it. Call `unit_check` with the whole `document` and the `item`. It saves the document
   as the unit's draft, then checks it at layers A to F.
5. Read every problem. Each one has a `layer`, a `kind`, `where` (the JSON pointers), a
   `message` and a `hint`. Read all of them before you change anything, because one change can
   fix several.
6. Fix every error. Then check again, and pass the last answer's `problem_set` as
   `previous_problem_set`.
7. Stop when `counts.errors` is 0. Warnings may stay. Tell him what each warning means in one
   line, for example that a placeholder exit is for demo only.

If the answer says `no_progress` is true, your last change fixed nothing. Do not try the same
change again. Stop and tell him which problem you cannot fix and what you tried.

If `saved.refused` lists problems, the draft was not saved, because the document's shape does not
hold. The draft keeps its last good version. Fix those problems first.

## Blocks

The dictionary holds every block a unit can bind. Search it before you write code.

1. Call `blocks_find` with the trader's words, for example `"trend filter"`. Pass `role` to keep
   blocks that can fill the slot you need. Each row is one line: the pin, the type, the output,
   the data level it needs and its status.
2. Call `blocks_get` on a row to read the entry in full: what a trader means by it, its inputs,
   its parameters with their defaults, and its code.
3. Bind only a block whose status is `implemented` or above. A `named` or `specified` entry has
   no code yet.
4. When his request is a source or a written idea, call `blocks_match` on its text. Each sentence
   comes back with the entry it states, or as an append request. Tell him about every append
   request. Never invent an entry for it silently.
5. Write a new block only when no entry does the job. Call `blocks_check` with the entry and its
   source, fix every error, and write the `fingerprint` it returns into the entry. No row saves
   a new entry yet, so show him the checked entry and its source, and say a unit can bind it
   only once it is saved and published.

## When you are done

Tell him in plain words what the unit trades, when it enters and exits, which numbers are
placeholders, and that it waits in his Library as a draft for his yes.
