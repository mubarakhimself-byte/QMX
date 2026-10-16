---
title: Engine OPEN-1: agent burst provider to try first
type: grilling
mode: HITL
status: open
blocked_by: [provider-setup-from-skills]
claimed_by: ""
created: 2026-10-16
---

## Question

Contabo runs first (ruling 74) but holds only 4-6 concurrent Claude sessions (ruling 76). Which burst provider is tried first when it fills, and how is it chosen?

## Recommended answer

Add his Contabo box as an Amp runner (free) and Cloudroom's free tier as a comparison; keep E2B, Modal and Cloudflare as adapters with no account; choose on cost per agent-hour after one measured week. Ruling 74 already answers 'Contabo first'; only the burst choice remains.

## Unblocks

Library OPEN-5 (public listener), burst placements.

## Sources

`architecture/workflow-engine/`OPEN-DECISIONS.md item 1; rulings 55, 69, 74, 76; `33-state-of-play.md` section 6 (Cloudroom facts).
