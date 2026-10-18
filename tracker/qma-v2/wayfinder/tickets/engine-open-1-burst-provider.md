---
title: Engine OPEN-1: burst provider and paid machines (incl. a Windows desktop for cTrader demo)
type: grilling
mode: HITL
status: open
blocked_by: []
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

## Update (2026-10-18 evening, re-centralize)

Parked operator call (39 R.7 item 6, F.4 item 6): which burst provider to pay for and when, now also **whether to pay for a Windows desktop placement** (a VM or a spare machine) so cTrader demo click-through exists (engine AD-33; MT5 demo needs none). Recommend: decide only when Contabo's four sessions overflow too often; the onboarding flow adds any provider without code (AD-30). The research ticket "Provider setup from the providers' own skills" feeds the eventual choice but no longer blocks the call. The ticket `engine-open-4-server-check` (`/dev/kvm` on Contabo) says whether a Windows VM there is even possible.
