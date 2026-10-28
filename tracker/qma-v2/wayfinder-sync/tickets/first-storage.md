---
title: Which storage do you connect first? (E1)
type: grilling
mode: HITL
status: closed
blocked_by: [connect-storage, sync-switch-and-timing]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: operator (his answer of 2026-10-28, `../research/sync/05-his-answers-2026-10-28.md`)
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

## Resolution

**This PC is the first storage and the default. Everything works with no cloud at all. Every other storage is one he connects himself with a click in the connect dialog, during install or later. Google Drive is the first one he will try.** The recommended answer above (Drive first) is not taken as written: his answer puts his machine first.

His words, verbatim (`../research/sync/05-his-answers-2026-10-28.md`, E1):

> "Let's try Google Drive, but like I said, I think the same notion should remain. My machine first. So if my machine can't work, the rest don't make sense. ... I can't assure you that I'm going to have Google Drive and other things. And also, this reduces the friction when you are coding. ... if I say Google Drive, it means you are going to need my Google Drive credentials ... during installation, I can select and easily click and like connect. ... So it reduces that friction during coding and also improves the customizability of the platform."

What it decides:

- **The storage list starts with This PC.** "Copies on this PC" is the first storage row, built in and on by default. It is not an extra beside the "real" storages. With no other storage connected, QMX is whole.
- **No storage kind is a default beyond This PC.** Google Drive, another drive, his server, R2 and any rclone kind are choices in the one connect dialog. The dialog runs from the first-start card's optional "Keep your work in another storage" card or later from Settings or the copilot.
- **Builders never need his Google credentials, or any account.** Every storage path is proven on throwaway folders: the folder kind directly, the rclone adapter through rclone's own `local` backend. The Drive kind is proven up to the card where he would sign in, and no further. Registering QMX's own Google sign-in client stays his one-time step inside the Drive kind (`connect-storage`), shown as a card with a link.
- **The old ticks.** They are write-once, so This PC's copies name them without copying them. Each storage he connects later has its own "prices that can't be downloaded again" switch, on by default; he turns it off on a small storage.

Where it lands: `../research/sync/06-sync-and-connect-design.md` sections 4, 5, 9 and 10.
