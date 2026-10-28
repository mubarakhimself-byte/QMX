---
title: Which UI-HANDOFF section 26 gaps belong here
type: grilling
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

UIH §26 lists nine backend gaps that the screens hit. Which ones belong to sync and connect, and which go elsewhere?

## Resolution

| Gap | In? | Where it lands |
|---|---|---|
| 1. Run place on the run read (`GET /api/workflow-runs/{id}` and the list lack `placement`) | in | Places. Once compute is connected, the run card says where each run went. The data already sits on the run's Library object and each span (UIH §20 row 3) |
| 2. Broker reads over REST | out | Broker and connections work (R129, R133). Not sync or connect |
| 3. cTrader app key entry | in | The write-only key route of the connect dialog |
| 4. Backup incidents missing from `GET /api/inbox` | in | Sync incidents. The inbox read lists open incidents of every kind, sync ones included, so the screen never needs a second route |
| 5. A read-only store said up front | in | Install and update. A restored older copy or a rolled-back update can leave a store newer than the program; the health read names each store's open mode |
| 6. Telemetry value check | in | Deep logs |
| 7. Local deep logs | in | Deep logs on this PC |
| 8. Backup and restore beyond the card | in | The sync and restore tickets: restore from Settings and cancel, the after-restore pause (PR 229), the monthly check, off-site copies. The key passphrase is parked |
| 9. Attach route and `@file` and the rest | out | The parked attach plan. Only its secret-list fix lands here, through the class table |

The UI notes (`UI-HANDOFF.md`) get a sync, storage, maintenance and deep-logs section once the design is written. The coordinator owns that edit (`words:106`).

## Evidence

UIH §26 (read this session). The QUEUE's last section lists the same gaps "to fold into the plan where they belong" (`D:/QMX-worktrees/qma-ship/wrapup/QUEUE.md`, "Sync and connect design round").
