# The lead's review of the funnel (31 Oct, 11:35 UTC)

The three funnel files were read against each other and against STATE midday rulings 1-55. Most lead's calls agree. Where they clash with each other or with a ruling, the settlement below binds the architecture step. The agents' calls not named here stand as they are.

Sources: `solutions/00-index.md` §4 (calls LC-01 to LC-38), `experience/design-thinking.md` "Lead's calls" (calls 1 to 17, cited F2-n), `edge-cases/catalogue.md` §20 (calls 1 to 10, cited E1-n).

## Settled clashes

| # | Clash | Settlement | Why |
| --- | --- | --- | --- |
| 1 | LC-30 keeps workflow agent steps without file tools ("units do not need it") | **Overruled.** The skipped agent-step file writes (probe P-PERM, 18 Oct) is designed as a fix, grounded in the workflow engine's design session | STATE ruling 49: "one of the fixes, maybe a simple one". F1 ran before ruling 49 was recorded |
| 2 | LC-36 says units are never mini apps and parks a "unit companion" template; E1-3 lets a mini app hold a unit for research, backtests or paper | **E1-3 wins.** A mini-app template that holds a unit for research, backtests and paper is in the build as a Should, built only with what the mini-app core offers; live trading stays with the node alone | STATE ruling 24 ("at most, add a mini-app template that holds a unit") and his 31 Oct morning answer 5 ("units may need to sit inside mini apps") |
| 3 | F2-9 refuses a unit with a placeholder slot on a live account by default; E1-4 shows placeholders at promotion and never blocks | **E1-4 wins.** The promotion card shows every placeholder plainly; nothing refuses; his click decides | Standing order 6 (no money gates) and his rule that only he promotes. The risk session may add a refusal later |
| 4 | LC-23 stores a live grant only "on a machine he marked trading server"; F2-4 drops any "trading server" kind | **F2-4's words win.** No machine kind is named. A server takes the trading role when he binds a live account to the trading-node app on it; that host then runs the trading profile with no chats and no agent steps | "A server can be a server." (STATE morning answer 5) |
| 5 | LC-20 renames the shipped volatility buckets "volatility state" and gives "regime" his meaning (trend against range) | **Kept as a lead's call, flagged as his word.** The words on his screens are his to veto; the summary to him names this one | Ledger: words on his screens are his |

## Calls confirmed against his rulings

- Self-healing (E1-2, F2-10, LC-22): after a technical fault the node restarts with back-off, reconciles and resumes entries by itself; a risk stop survives restarts and waits for his click (rulings 27, 35; standing order 7).
- The live key lives only on the server he binds for live trading; his PC trades practice accounts only (LC-23, F2-8; ruling 135 handled technically).
- One monitoring stack, OpenObserve; QMN's Grafana, Loki and Prometheus go (LC-34; ruling 42).
- The node keeps its working parts and replaces its shell (LC-21; ruling 27). The deletions happen in the build's PRs, which he lands.
- QMB is a mini app; the judge, the run id and the try count stay in the core (LC-14; rulings 22, 43).
- The MIS's readings are core code; its publisher is the third mini app (LC-19; rulings 48, 55). Indicators first, no training needed now.
- The copilot reaches QMB and the node through the existing rows and the two app names in its default home (LC-15, F2-6; rulings 8, 53).
- Moving a unit from tested to paper is his click by default (LC-37; standing order 7).
- Both soak numbers stay as settings: 24 hours on the PC before a release, one week on demo before a live binding (LC-24; his node ruling of a week-long soak).
- No Databento adapter now; the futures route is a port with a working placeholder (LC-27; rulings 29, 40).

## Gaps the architecture must close

- E1 "Not verified": whether Hyperliquid's trigger orders can carry the venue-resident stop; whether cTrader rejects a repeated client order id. Part C proves both, or designs around them.
- The mini-app core's two blockers (F2): a `money` app is proposal-only and needs his signature to publish, so the node cannot send orders as built; app tools drop out of the copilot's default home. Part C fixes the first within ruling 46; the shipped default in F2-6 fixes the second.
- F1 read the gold mine (research 39) and the Hermes files only through other files. Part A reads research 39 in full (its brief already says so).
