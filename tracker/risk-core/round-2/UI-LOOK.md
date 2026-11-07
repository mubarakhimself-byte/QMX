# What the running demo UI shows about pods

The lead opened the UI (`qmx-ui-design`, branch `ui-review/repair`) on 7 Nov and read Home, Lab (Pods bench), Portfolio (Pods tab), Apps and Settings. The UI is a design demo and is outdated; his UI notes propose changes. No backend sits behind it. This records intent, not fact about the code. **He stresses (M55): the UI is a proposal and mostly outdated. It binds nothing.** Read his UI notes beside it.

**Portfolio: a pod is money with a method.**
- Each pod card shows a name, Live or Paper, its money, its day change, a method and a place. For example, "BTC & ETH core, Live, $24,180, +1.4%, Book + BMS, Binance spot, 2 bots".
- Methods on screen: Book + BMS, Model, Workflow, Hybrid, Simple rules. So several ways of sizing live side by side, and Book + BMS is just one of them.
- A pod panel shows: at stake next trade, losses to kill line, room to kill line, deepest dip; meters for kill-line room, daily loss and a share limit; editable sizing fields (risk per trade, daily loss stop, most in one coin, kill line, a ladder); and its bots with their shares.
- A pod is on one account or venue. A pod has live and paper sides. Portfolio also has Road to live, MIS and Servers tabs, and exposure across pods.

**Lab: a pod is a stack of blocks.**
- Benches: Strategies and Pods. Modes for a pod: Design, Test, Paper.
- Slots on screen: Inputs, Guards, Allocator, Sizer, Throttles, Caps, Ledger. Each slot holds blocks with an add button. Blocks are removable.
- Templates seen: Classic Book, Trend rider, Vol-targeted core, plus New pod.
- Size trail: one sample trade walked block by block, for example sizer, regime ×0.5, volatility ×1, caps, venue fit. It follows every edit.
- Test screen inputs: ticked pods, bots and crises, including "Yours, New crisis". Then "Send to paper".
- "Every pod needs this" sits on the kill line block. So one block is required by the design.

**Apps: watchers already appear as mini apps.**
- "Weekend watcher: Live, 4 pods inside their lines, next check 14:18." A pod-level watcher as a mini app is what he described for monitoring.
- "Position sizer: XAUUSD 0.5% risk, 0.42 lots" shows lots on screen as a helper.
- Others: News and sentiment, Funding rates, Broker status (stopped, with Restart), Morning brief, Spread watcher (sandbox), Economic calendar watcher (shadow run), Correlation map (build). Apps have run stages: live, shadow run, sandbox, needs a look, build. There is a "Safe mode".

**Home: what reaches him.** "Needs you" (a few items, each one line, including "Sign ... for live" and a kill switch level). "Going on" (runs). Pods as a roll-up. News and events.

**Settings: "Alert me when".** Orders filled or refused; kill switch or risk stop; a copilot needs you; a mini app stopped itself; a server goes down; a test or sweep finished. Quiet hours. Per-channel pushes are not shown.

## What this means for the design

1. **His pod is the Lab and Portfolio thing: a stack of blocks plus money and members, on one place, with paper and live sides.** A "desk" or department is separate (a mini app or group of them), and he only said "I think" of that.
2. **The screens assume pod-level numbers exist:** at stake next trade, losses to kill line, room, daily loss. So a fold by pod scope is a record need.
3. **The size trail is core to how people understand size.** It needs one evaluator and receipts per step.
4. **Different methods side by side means the pod owns its sizing method.** A unit in a pod takes the pod's stack, and a unit alone needs its own.
5. **A watcher mini app reads pods and lands "Needs you" lines.** So apps need a read door and a card path.
6. **The demo's "Every pod needs this" kill line is a design choice,** not code. His fixed lines don't require it. Keep it as a template default unless he says otherwise.
7. **The demo's data is crypto-heavy and old.** Don't read the block names as a final list.
