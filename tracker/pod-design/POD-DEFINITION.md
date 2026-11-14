# What a pod is (working definition, 12 November 2026)

His words today, settled in conversation after the grounding reports beside this file (`POD-GROUNDING-2026-11-12.md`, `BRAKES-ACCELERATORS-GROUNDING-2026-11-12.md`). It's the base for the pod design session, not yet a final design.

## The model

- **A pod is the Book plus the BMS, revised and versioned,** so its numbers can change. He said: "the book and the BMS system are actually the best version I could ever get of what I've been trying to pull off this entire time."
  - **The Book half** holds the trading rules for its style, including exits. A scalping pod may need first invalidation, or a moving stop-loss and take-profit. The old scalping book is the model.
  - **The BMS half** holds the money: its share of an account, its brakes and accelerators, and its kill line.
- **Pods are circumstantial:** a pod for cash flow, for stability, for one instrument, for one timeframe, like a hedge fund's pods.
- **A unit is the logic.** It registers into one or more pods. The pod supplies the unit's risk half: rc-03 already splits every unit into a logic half and a risk half, so one unit can sit in several pods with no copies.
- **Outside all pods are things that touch trading but not money:**
  - the MIS;
  - the SQS;
  - the kill switch (in levels, about six; it has survived every redesign);
  - the correlation ledger;
  - and likely more, still to be listed.
- **Brakes prevent trading; they never close trades.** Only the kill switch's top, black-swan level closes. Which other kill levels close trades is still his call.
- **Accounts:** many accounts across platforms. Sizing reads the account a unit trades through, and the pod decides how much of it the unit may use.

## Conflicts between unit and pod are prevented, not refereed

Each pod gets its own herd: a dedicated workflow, with agents that keep a unit's rules and the pod's rules from disagreeing in the first place. This comes from his QMA v3 idea: the Shepherd protocol, plus a continual harness, plus Prime Intellect. So there's no "which exit wins" rule. The herd stops the clash from arising.

## Order of work he set

1. Pod-central design first.
2. Then the unit, completed fully.
3. Then the unit registering to a pod.

One exception: the 6 high bugs in the built unit core are repaired first, because that core survives any pod design.

## What exists today

- Empty Library kinds `pod`, `book` and `bms` on `engine/base`.
- A node account roster that holds many accounts, each tied to one BMS.
- The correlation ledger as a records name only.
- The risk plan's "recipe" pods (RC-53, RC-54) are dropped. The group and pod rows (RC-49 to RC-52, RC-55 to RC-57) wait for this design.
