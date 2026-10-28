---
title: Which storage do you connect first? (E1)
type: grilling
mode: HITL
status: open
blocked_by: [connect-storage, sync-switch-and-timing]
claimed_by: ""
created: 2026-10-28
owner: operator
---

## Question (for him, in plain words)

QMX can sync your work to any storage you connect. Which one do you connect first?

## Why it is yours

It is money, and it uses one of your Google accounts.

## What you are choosing between

| Choice | Cost | Room | What it needs from you |
|---|---|---|---|
| Google Drive, the free space on your main account | nothing | 15 GB, shared with your Gmail and Photos | a one-time setup: you register QMX's own Google sign-in in Google Cloud (free; QMX walks you through it). rclone's shared Google sign-in stops working during 2026, so every Drive user needs this. Your friends would sign in through yours |
| Google One or AI Pro | monthly (you mentioned 400 GB, or 5 TB for about 20 a month) | plenty | the same one-time setup |
| Cloudflare R2 | free up to 10 GB, then about 1.5 cents per GB a month | no limit | a Cloudflare account and one key |
| Your server | already paid | 100 GB | the server set up first; it comes second, after QMX runs on this PC |

**The one big thing:** your old 10 GB of ticks can't be downloaded again, so QMX would sync it. The free 15 GB that your Gmail also uses can't hold it safely. QMX keeps 2 GB or a tenth free on any Google account, so your mail keeps working.

## Recommended answer

**Google Drive on your main account's free space, for everything except the old ticks. The ticks go to your server once it is connected.**

- Your work is likely tens to a couple hundred MB once compressed. That is an estimate; it gets measured at your first real start.
- It costs nothing, and it is the same path your friends would use.
- Each storage has its own switches, so Drive gets your recipes, your own content and your run results, and the server gets all of that plus the ticks.
- Until the server is connected, the ticks stay on this PC only.
- Buy a bigger plan only if the measured size outgrows the free space.

Say "yes" to accept. Or name another choice, such as "use Google One for everything".

## What changes with the answer

The answer changes only the defaults: which storage the first sync and the first build check use, and whether the Google sign-in setup is on the path. The design is the same for every storage.

## Evidence

- Free Google storage is 15 GB, shared across Gmail, Drive and Photos (`sources/google-one-storage-terms.md:19`). Over quota, Gmail "can be impacted" (same file).
- rclone's shared Google client is going away (`sources/rclone-drive.md`). R2 pricing is in `sources/r2-pricing.md`.
- The old ticks are about 10 GB, on his PC (R130).
- His words: "storage might not be an issue because, man, a terabyte is quite kind of high", and the AI Pro plan "gives me 5 terabytes ... 20 per month" (`words:151`).
