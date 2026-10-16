---
title: Account guard: no agent write path, ever
type: task
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Read-only guard idea stands, but the effect-table edit touches the harness (ruling 24) and guard facts are node depth (ruling 14)."
closed: 2026-10-16
---

## Question

Lock every agent out of writing the account guard (kill line, loss budget, correlation limits, kill switch, news rules, venue rules) with a deny rule and a canary test, while zero-token scripts and templates may still read guard facts through the C7 reader.

## Why it matters

The risk session agreed the guard sits outside units. `21` A5 settles the earlier contradiction: agents may READ guard facts through C7; they may never write or change the guard. The money hook (HP8) covers moving money; it does not cover guard settings.

## What the session does

AFK task. Add guard settings to the effect table as a class no permission mode or allow rule can grant; a `PreToolUse` deny on any tool or file path that writes guard settings; a canary file and a live script (like HP8's `s21_canary.py`) proving every write attempt is denied in default, bypass and sub-agent modes, and that reads through the C7 reader still work. Until a node read model exists, the reader returns `unknown` for guard facts and templates render "could not check". Hand back the diff plan and the test lane.

## Unblocks

The unit read adapter's guard half; wave 1 packets; the node-dependent templates later.

## Sources

`09-self-configuring-unit.md` §3 item 10; `19` C7; `20-review-a` finding 5; `20-review-b` finding 5; `21` A5, B5.

## Resolution

Resolved. The money gate stays in the harness, untouched (ruling 24; HARNESS-REQUESTS 'not requested'); engine AD-8 classes effects and no agent gets an order verb; engine AD-33 deny-lists broker windows; guard facts are node depth (ruling 14). (Map rewrite 2026-10-16.)
