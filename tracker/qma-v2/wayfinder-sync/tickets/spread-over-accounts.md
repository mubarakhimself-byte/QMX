---
title: Spread copies over several free Google accounts (E2)
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

He asked: "Can I connect multiple accounts more than one and we spread the data across? That's an edge case I would like you to test if it's even viable. I'm just joking anyway, but if it's viable..." (`words:185`). Is it viable, and does the design spread?

## Resolution

**Viable only if QMX places files itself; not built now.** Each storage holds a whole copy. Several storages give several whole copies, which is more safety, not a share of one.

- **rclone `union` is unsafe for the pool.** If any member fails to open, the whole union fails to open; if a member fails while listing, its files silently drop out of the list; the "most free space" rule needs a free-space report that R2 does not give (`src:` 2.1, from `sources/rclone-union-go-excerpt.md`; read from source, not run).
- **QMX-side spreading would work** (each account one place, each new pack to the place with the most room), but it solves no problem today: the saved set is estimated at tens to a couple hundred MB compressed (`inv:` 1), which fits one free account many times. Losing any one account would also lose the packs on it.
- **Terms risk:** Google's rules ban using several accounts to get around a limit that was "previously prohibited"; the research corrected the inventory, since no rule says outright that spreading storage is abuse (`src:` 2.5). The risk is real but unwritten; one paid account carries none.
- **Revisit** only if the measured set outgrows one storage (map fog).

## Why this is not his call

It reads as "risk to his accounts", but the facts settle it: the set fits one account, spreading adds a way to lose data, and he framed it as a test of viability. The answer to his test is above.
