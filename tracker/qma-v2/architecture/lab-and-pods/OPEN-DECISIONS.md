# Open decisions (four; the design proceeds on the recommendation)

Refreshed 2026-10-16 night against rulings 73-88 (27c gap fixes). Two of the original six were answered by rulings 73-88 and are closed below; four stay open.

| # | Decision | Recommendation | If ruled the other way |
| --- | --- | --- | --- |
| OPEN-1 | How does a pod reach the trading node now? | **Compile to the default Book (CT-22) + BMS (CT-27) composition through `PodCompilerPort`, and name every block the adapter cannot place as `unsupported_blocks`.** Those blocks run in the Lab's simulator for tests and paper and appear as a failed "Ready for live?" row. When the risk session settles the unit, only the adapter changes. | Wait for the risk session: the Pods bench can be designed and tested but never sent to paper or promoted until then; or add a PolicyPair adapter first (ATC, ADR-0024 AD-23), which is more work and still leaves the same blocks homeless. |
| OPEN-2 | What paper money does a Lab paper run use in v1? | **The server paper ledger on live prices** (simulated fills, no venue). Broker demo and exchange testnet accounts arrive through `NodePort` once the node mints demo bindings (TN-9 node-paper). The screens keep the three money kinds; two are greyed with the reason. | Demo accounts first: the Lab would need the node's binding path and the venue importer before any pod can soak, and "every fill matched the exchange" needs reconciliation the node owns. |
| OPEN-4 | What is a mix ("Run together")? | **A pod whose `members` are other pod versions and whose allocator is one block `split-across-pods`**; it is saved, tested and sent to paper like any pod, so no new kind and no new screen. | A separate `mix` kind: one more Library kind and one more adapter branch for no visible gain. |
| OPEN-6 | Pairs (one market against another) in the scenario builder | **Defer** until QMB declares a spread instrument; keep the control greyed with "needs a spread instrument". | Cut the control now; it reappears in the UI handoff list when QMB can do it. |

## Closed by rulings 73-88

- **OPEN-3 Who may start a paper run?** Answered by ruling 80 ("creation is human-driven first: build, test, paper if needed, then run autonomously"; starting a pod on paper is part of that human-driven creation). The operator starts it through a MANAGE ask ("Needs your yes: put Weekend rider v1 on paper", shot 27); agents prepare everything up to that point. After his yes the daily paper runs need nothing more from him (AD-12).
- **OPEN-5 How are Lab-scoped schedules enabled?** Answered by ruling 80 with engine AD-22: a Lab schedule (the overnight loop, weekly code health) is a workflow like any other, so he says yes once when it is published and enabled, and it then runs without asking. No separate standing Lab allow rule is needed. The old wording "bounded by the engine's budgets" is replaced by the engine's runaway guard, which never asks (ruling 27; AD-13).

Recorded in `.memlog.md` as `question` entries.
