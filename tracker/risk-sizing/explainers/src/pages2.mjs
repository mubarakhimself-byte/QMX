import { CONTENT, head, panel } from "./pages.mjs";
import { pill, chips, figCard, bars, flow, cards, table, figScript, Y, N, H } from "./site.mjs";
import { lifeFig } from "./fig-life.mjs";
import { journalFig } from "./fig-journal.mjs";
import { testingFig } from "./fig-testing.mjs";
import { judgingFig } from "./fig-judging.mjs";
import { sizingFig } from "./fig-sizing.mjs";
import { decayFig } from "./fig-decay.mjs";
import { routerFig } from "./fig-router.mjs";
import { marketsFig, libraryFig, buildFig, MARKETS, FOUND } from "./fig-more.mjs";

const page = (fn) => (p) => { const { body, script } = fn(p); return { body: body.join(""), script }; };
const tree = `<div class="tree">
<div class="tnode root"><b>Asian-range reversion</b><small>family · one shared try count: 37</small></div>
<div class="tkids">
<div class="tgroup"><span class="tlabel">${pill("proposed")} same bet: they move together</span>
<div class="tnode"><b>EURUSD 1m</b><small>IC · cTrader</small></div><div class="tnode"><b>EURUSD 5m</b><small>IC · cTrader</small></div></div>
<div class="tnode"><b>GBPUSD 1m</b><small>IC · cTrader</small></div>
<div class="tnode"><b>EURUSD 1m</b><small>other broker</small></div>
</div>
<p class="note">Each box is a complete sibling unit: its own calibration, its own journal. Sessions and sniping windows stay inside one unit.</p></div>`;
const newRows = `<div class="nrows">
${[
  ["Logic or an exit changes", "New version", "linked to its parent"],
  ["A setting moves inside its range", "Same unit", "each value tried = +1 try"],
  ["The unit recalibrates its risk", "Journal entry", "not a new unit"],
  ["A model rewrites it", "New unit", "marked 'rewritten from', same family"],
].map(([a, b, c]) => `<div class="nrow"><span class="nwhen">${a}</span><span class="nar">&rarr;</span><span class="nwhat"><b>${b}</b><small>${c}</small></span></div>`).join("")}</div>`;

CONTENT["lifecycle.html"] = page((p) => {
  const f = lifeFig();
  return { script: figScript("fig-life", f), body: [
    head(p, "proposed", "A unit moves one way: from an idea to live. Two worlds: QMB tests, the node trades."),
    figCard({ id: "fig-life", name: "Fig 2 · Six stations, one direction", svg: f.svg }),
    chips("fig-life", [
      ["proposed", "<b>Open stages</b> (research, backtest, optimise): logic may change", "build"],
      ["proposed", "<b>Compiled</b> after stress: logic and exits frozen", "token"],
      ["proposed", "<b>Paper is per unit</b>, on the node, ends on a trade count", "paper"],
      ["open", "<b>Live needs your click</b>, from the unit's journal page", "live"],
    ]),
    `<h2>The family tree</h2><p>The same logic on another instrument, timeframe or broker becomes a <b>sibling unit</b>.</p>`, panel("", tree),
    `<h2>When is it "new"?</h2>`, panel("", newRows),
    `<h2>Small siblings going live</h2>`,
    panel("Recommended, needs your yes (question 3)", flow([{ t: "Sibling of an admitted unit" }, { t: "Own backtest + stress", c: "qmb" }, { t: "Live at minimum lot", s: "no click needed", c: "node" }, { t: "Grows only on its own trades" }]) + `<p class="note" style="margin-top:10px">Paid from a monthly evidence budget you set (start: 5% of equity a month, configurable). A new broker or market kind (perps, futures) still needs your click.</p>`),
    chips("fig-life", [
      ["found", "The written rule today: <b>no per-bot paper or probation</b>", "paper"],
      ["open", "Questions 1, 2 and 3 settle identity and promotion", null],
    ]),
  ] };
});

CONTENT["journal.html"] = page((p) => {
  const f = journalFig();
  return { script: figScript("fig-journal", f), body: [
    head(p, "proposed", "One journal per unit, from creation to retirement. Each part has exactly one writer."),
    figCard({ id: "fig-journal", name: "Fig 3 · One book, two writers", svg: f.svg }),
    chips("fig-journal", [
      ["proposed", "<b>Backtest + stress</b>: written by QMB only", "tab-qmb"],
      ["proposed", "<b>Paper + live</b>: written by the node only", "tab-node"],
      ["proposed", "<b>Front page</b>: computed, never typed", "front"],
      ["proposed", "<b>Exam baseline</b>: frozen at promotion, never refitted on live data", "exam"],
      ["proposed", "<b>Readers keep no copy</b>: registry, router, your page, calibrator", "readers"],
    ]),
    `<h2>One trade row</h2><p>Every trade, in every section, carries the same fields. That is what lets live be compared with the exam.</p>`,
    panel("", cards([
      { k: "Result", v: "R planned · R result", p: "Measured in R, so instruments compare." },
      { k: "Costs", v: "Spread · fees · swap · slippage", p: "Each in R." },
      { k: "Path", v: "MAE · MFE", p: "Worst and best excursion, in R." },
      { k: "Context", v: "Session · state at entry", p: "MIS labels at the moment it opened." },
      { k: "Why it ended", v: "Exit reason", p: "Which exit fired." },
      { k: "Kind", v: "Filled · skipped · blocked", p: "Skipped for size, or blocked by the guard, still logged." },
    ])),
    `<h2>The front page shows</h2>`,
    panel("", flow([{ t: "Best markets", s: "instruments, timeframes, sessions" }, { t: "Risk now" }, { t: "Tries", s: "n, effective n, best corrected" }, { t: "Stage" }, { t: "Pod" }])),
    chips("fig-journal", [
      ["found", "Fill importers and a Library <b>trade</b> item give a base", null],
      ["found", "Backtest trades carry <b>no market state</b> today", null],
      ["improve", "Journals keep running when a unit is paused, on paper", null],
    ]),
  ] };
});

CONTENT["testing.html"] = page((p) => {
  const f = testingFig();
  return { script: figScript("fig-test", { ...f, mode: "today" }), body: [
    head(p, "found", "QMB is the backtest and stress world. It has a lot of machinery, but nothing it produces counts as proof yet."),
    figCard({ id: "fig-test", name: "Fig 4 · The QMB test line", svg: f.svg, modes: [["today", "Today"], ["proposed", "Proposed"]] }),
    chips("fig-test", [
      ["found", "Agents <b>can't backtest</b> a strategy they wrote: the door is setup-only", "unit"],
      ["found", "<b>No backtest that trades</b>: the only runner is silent", "unit"],
      ["found", "<b>Quotes only</b>: no crypto, no perps replay", "sealed"],
      ["found", "<b>No R</b>, no pass marks, <b>no tries correction</b>", "tries"],
      ["found", "<b>Cost calibration empty</b>, so no verdict is proof", "cost"],
      ["found", "Long scalper tests choke: about 16 GB per month of 1m data (estimate)", null],
    ]),
    `<h2>The small recommended set</h2><p>Few tests, each known to catch overfitting, cheap to expensive, stop at the first failure. QMB measures; it never benches or promotes.</p>`,
    panel("", `<div class="cards">${[
      ["Always", "Tries ledger", "Every run counts. Headline = best of N, deflated."],
      ["T1", "Cost × 2", "Net > 0 at 1× and 2× calibrated cost."],
      ["T2", "Out-of-sample in R", "≥ +0.15R, ≥ 200 test trades, sealed months > 0."],
      ["T3", "Plateau", "Median of nearby settings > 0 after cost."],
      ["T4", "Family check", "PBO ≤ 0.25 passes, > 0.50 dead. From 10 tries."],
      ["T5", "Size cone", "Block-bootstrap: sets size and the live cone. Not a gate."],
    ].map(([k, v, t]) => `<div class="card"><div class="k">${k}</div><div class="v">${v}</div><p>${t}</p></div>`).join("")}</div><p class="note" style="margin-top:10px">All numbers are configurable starting values. Optional: 5–10 real event days (news, gaps, spread blowouts). Monthly: a "test of the tests" drops any test that adds no lift.</p>`),
    `<h2>Old QMX, new QMB, research</h2>`,
    panel("", table(["", "Old QMX", "New QMB", "Research"], [
      ["Pass numbers", Y, N, "Keep"],
      ["Results in R", Y, N, "Use R"],
      ["Counts tries", N, H, "Most predictive"],
      ["Sealed holdout", N, Y, "Strongest guard"],
      ["Calibrated costs", H, N, "Main test for scalpers"],
      ["Family check (PBO)", Y, N, "Keep, per family"],
      ["Shuffle Monte Carlo", "Gate", "Robustness", "Size only"],
      ["Paper per bot", Y, N, "Most trusted step"],
    ]) + `<p class="note" style="margin-top:8px">YES / PART / NO. Old QMX had numbers; new QMB has more machinery, honest labels and real-fill costs, but no numbers yet.</p>`),
    `<h2>Drop as gates</h2>`,
    chips("fig-test", [
      ["proposed", "Trade-shuffle Monte Carlo as pass/fail (keep for sizing)", "mc"],
      ["proposed", "What-If filters (they become hypotheses)", null],
      ["proposed", "Candle and parameter wiggles, composite scores", null],
      ["improve", "Fix PR 204's house-rule breaks; it proved one landing path", null],
    ]),
  ] };
});

CONTENT["judging.html"] = page((p) => {
  const f = judgingFig();
  return { script: figScript("fig-judge", f), body: [
    head(p, "proposed", "When strategies are nearly free to make, judging them is the product. Five simple rules."),
    figCard({ id: "fig-judge", name: "Fig 5 · The luck bar", svg: f.svg }),
    chips("fig-judge", [
      ["proposed", "<b>1. Count every try</b> in a family", "count"],
      ["proposed", "<b>2. Correct the best</b> for that count", "bar"],
      ["proposed", "<b>3. Sealed months</b> the search never saw", null],
      ["proposed", "<b>4. Stress the costs</b>", null],
      ["proposed", "<b>5. Judge live</b> against the unit's own exam baseline", null],
    ]),
    `<h2>Near-copies count less</h2>`,
    panel("Effective tries", flow([{ t: "10 near-copies", s: "EURUSD 1m, 5m, … of one idea" }, { t: "≈ 2–3 real tries" }])),
    `<h2>Sealed months</h2>`,
    panel("", flow([{ t: "2021–2024", s: "search and tune" }, { t: "2025 · locked", s: "judged once, like an unseen exam", c: "you" }])),
    `<h2>Enough trades to believe it</h2>`,
    panel("", bars([
      { label: "55% win, 1:1", value: 270, max: 600, text: "~270" },
      { label: "70% win, small wins", value: 550, max: 600, text: "~550", c: "warn" },
    ]) + `<p class="note" style="margin-top:8px">Scalpers get there in weeks. A unit that can't get there in time is "too thin to judge", not "failed".</p>`),
    `<h2>Trust grows with its own record</h2>`,
    panel("Weight of its own record = trades ÷ (trades + 100)", bars([
      { label: "20 trades", value: 17, max: 100, text: "17%" },
      { label: "100 trades", value: 50, max: 100, text: "50%" },
      { label: "300 trades", value: 75, max: 100, text: "75%" },
    ]) + `<p class="note" style="margin-top:8px">A new unit starts near its template's usual size. k = 100 is a configurable start.</p>`),
    `<h2>Expanding a family</h2>`,
    chips("fig-judge", [
      ["proposed", "Each family has a small <b>false-alarm budget</b>; each new variant spends a little", null],
      ["proposed", "Expand only while: budget left, enough trades in time, neighbours profit, not a copy", null],
      ["proposed", "The expansion workflow waits until QMX is live", null],
    ]),
  ] };
});

CONTENT["sizing.html"] = page((p) => {
  const f = sizingFig();
  return { script: figScript("fig-size", f), body: [
    head(p, "proposed", "Each unit sizes itself from its own journal. It shrinks fast, grows back only on fresh evidence, and never passes your ceiling."),
    figCard({ id: "fig-size", name: "Fig 6 · Size column and floor ratchet", svg: f.svg, hint: "Drag the ceiling · tap a part · step with the arrows" }),
    chips("fig-size", [
      ["proposed", "<b>Shrink fast</b> on rules after losses", "size"],
      ["open", "<b>Grow back</b> only on fresh trades, after a minimum time, inside your ranges (question 4)", "fresh"],
      ["proposed", "<b>One-way ratchet</b> on the account floor, not on size", "floor"],
      ["proposed", "<b>Skip</b> a trade the minimum lot can't size safely, and log it", "skip"],
      ["open", "<b>House money</b> only where the record shows streaks (question 5)", "house"],
    ]),
    `<h2>What the calibrator tunes (v1)</h2>`,
    panel("Every fortnight, once enough new trades exist (configurable)", cards([
      { k: "1", v: "Risk per trade", p: "Scaled by how much evidence it has, under a Kelly ceiling." },
      { k: "2", v: "Loss points per session", p: "With a day cap." },
      { k: "3", v: "Session weights", p: "Its session profile." },
    ])),
    `<h2>Why size must be able to grow back</h2>`,
    panel("", `<p>Measured edges wobble. If size can only go down, every downward wobble sticks, and every unit sits at the minimum within a year.</p>` + flow([{ t: "Shrink only" }, { t: "wobbles stick" }, { t: "all units at minimum", c: "you" }])),
    `<h2>Kelly is a ceiling, not a target</h2>`,
    panel("Chance of touching a kill line 40% below the start", bars([
      { label: "Full Kelly", value: 60, max: 100, text: "~60%", c: "bad" },
      { label: "Half Kelly", value: 22, max: 100, text: "~22%", c: "warn" },
      { label: "Quarter Kelly", value: 3, max: 100, text: "~3%", c: "ok" },
    ]) + `<p class="note" style="margin-top:8px">With a perfectly known edge. Real edges are estimates, so real risk is higher.</p>`),
    `<h2>House money, only on streaks</h2>`,
    panel("Example record", bars([
      { label: "Win after a win", value: 60, max: 100, text: "60%", c: "ok" },
      { label: "Win after a loss", value: 45, max: 100, text: "45%", c: "warn" },
    ]) + `<p class="note" style="margin-top:8px">Here pressing after wins helps, so it switches on. If wins and losses come in random order, pressing only adds risk, and it stays off.</p>`),
    chips("fig-size", [
      ["found", "No per-type or per-bot calibration code exists yet", null],
      ["found", "On gold, 0.01 lot with a $3 stop is already 1% of $300", "skip"],
      ["improve", "Signal strength changes size only after QMB shows it earned more", null],
    ]),
  ] };
});

CONTENT["decay.html"] = page((p) => {
  const f = decayFig();
  return { script: figScript("fig-decay", f), body: [
    head(p, "proposed", "Loss points protect today. Statistics confirm a dying edge later. Keep the two apart."),
    figCard({ id: "fig-decay", name: "Fig 7 · Fuses and the nightly console", svg: f.svg }),
    chips("fig-decay", [
      ["proposed", "<b>Fast</b>: daily loss, loss points per session, kill switch, on the node", "fast"],
      ["proposed", "<b>Slow</b>: one nightly job per unit journal, four readings", "slow"],
      ["proposed", "<b>States, not scores</b>: OK, Watch, Alarm", "state"],
    ]),
    `<h2>How long a slow check needs</h2><p>Trades until the edge alarm fires, for an edge that starts at +0.1R per trade.</p>`,
    panel("", bars([
      { label: "drops to 0", value: 240, max: 260, text: "~240" },
      { label: "drops to −0.1R", value: 115, max: 260, text: "~115", c: "warn" },
      { label: "drops to −0.3R", value: 55, max: 260, text: "~55", c: "bad" },
    ]) + `<p class="note" style="margin-top:8px">An earlier file said 1,400 for the first row; the newer check corrected it to about 240. Either way it is slow, so fast protection stays a set of rules.</p>`),
    `<h2>The four readings</h2>`,
    panel("", cards([
      { k: "Edge alarm", v: "CUSUM on R", p: "Adds up shortfall vs the baseline. About 1 false alarm per 1,000 trades." },
      { k: "Cone", v: "Below the 5th percentile", p: "Cumulative live R vs the stress-test cone." },
      { k: "Cost drift", v: "> 1.5× card cost", p: "Over the last 50 trades." },
      { k: "Behaviour", v: "Trade rate 0.5×–2×", p: "And replay match above 80%." },
    ]) + `<p class="note" style="margin-top:8px">Watch: edge alarm past 70% of its limit, or any one other reading. Alarm: edge alarm fires, or two others. All configurable.</p>`),
    `<h2>Back to paper when</h2>`,
    chips("fig-decay", [
      ["proposed", "Loss points hit in <b>3 sessions in a row</b>", "fuse"],
      ["proposed", "Live results fall <b>outside its exam band</b>", "m-cone"],
      ["proposed", "A <b>slow decay alarm</b> fires", "m-edge"],
      ["proposed", "Loosen only on new evidence (score passes 20) plus a minimum time", "state"],
      ["found", "Old QMX's pool-cleaning workflow never had its maths written down", null],
    ]),
  ] };
});

CONTENT["router.html"] = page((p) => {
  const f = routerFig();
  return { script: figScript("fig-router", f), body: [
    head(p, "proposed", "The router only routes: it switches units on and off. Speed comes from doing the slow work early, not from clever code."),
    figCard({ id: "fig-router", name: "Fig 8 · Planner and gate", svg: f.svg, modes: [["online", "PC online"], ["offline", "PC offline"]] }),
    chips("fig-router", [
      ["proposed", "<b>Planner</b> on the PC writes a signed plan with an expiry", "pc"],
      ["proposed", "<b>Gate</b> on the node: cheap checks, only blocks new entries", "gates"],
      ["proposed", "<b>Open trades</b> always finish under the unit's own exits", "trades"],
      ["proposed", "<b>Kill switch</b> is local and independent of the plan", "kill"],
      ["open", "Split the router: planner on the PC, gate on the node (question 7)", null],
    ]),
    `<h2>Today: no router at all</h2>`,
    panel("The MIS today", flow([{ t: "6 rule labelers" }, { t: "+ 1 fitted model" }, { t: "read by the Book door and kill switch", c: "you" }]) + `<p class="note" style="margin-top:8px">Inside the node. No router exists in docs or code. Units' rules never read the MIS, and that stays.</p>`),
    `<h2>The plan's life</h2>`,
    panel("", `<div class="span3"><span data-c="ok">fresh<small>e.g. 24 h</small></span><span data-c="warn">stale, still used<small>until e.g. 5 trading days</small></span><span data-c="bad">expired<small>no new entries</small></span></div>`),
    `<h2>Live checks become "taints"</h2>`,
    panel("A seat stays open only if it tolerates every active taint", flow([{ t: "wide spread" }, { t: "flash move" }, { t: "feed stale" }, { t: "news" }, { t: "session closed" }, { t: "cost drift" }])),
    `<h2>Why two speeds</h2>`,
    panel("", bars([
      { label: "Volatility jump", value: 5, max: 100, text: "minutes", c: "ok" },
      { label: "Regime change", value: 44, max: 100, text: "~44 min", c: "warn" },
      { label: "New trend", value: 100, max: 100, text: "hours", c: "bad" },
    ]) + `<p class="note" style="margin-top:8px">Time to detect from 1-minute bars. So the gate reads fast facts; slow regime labels only feed the plan.</p>`),
    chips("fig-router", [
      ["proposed", "No index, ranker, model or event bus in the hot path: a plain loop", "gates"],
      ["proposed", "On reconnect, the PC replays the node's decisions to check them", "pc"],
      ["improve", "Drill the expiry: a demo seat with a short stop-after time", "plan"],
    ]),
  ] };
});

CONTENT["instruments.html"] = page((p) => {
  const f = marketsFig();
  return { script: figScript("fig-mkt", { ...f, mode: "all" }), body: [
    head(p, "found", "Every market differs in four places: how costs arrive, how time works, what data exists, and how the contract ends. Today the backend models mostly FX."),
    figCard({ id: "fig-mkt", name: "Fig 9 · What each market needs", svg: f.svg, modes: [["all", "Tour"], ...MARKETS.map(([id, name]) => [id, name.replace(" CFD", "").replace("SPOT CRYPTO", "Spot").replace("COMMODITY", "Cmdty")])], hint: "Green = exists · red = missing · amber = partly" }),
    chips("fig-mkt", [
      ["found", "<b>Stock CFDs at IC are MT5 only</b>; cTrader can't trade them", "s-venue"],
      ["found", "<b>IC futures CFDs expire</b> 2 working days early and are never rolled", "s-expiry"],
      ["found", "<b>cTrader</b> has a depth book but no trade tape", null],
      ["found", "<b>CCXT is spot only</b>: no perps, no funding, no open interest", "s-funding"],
      ["found", "Missing: funding, expiry/roll, dividends, calendars, order-flow indicators", "s-sessions"],
    ]),
    `<h2>Hyperliquid, in four facts</h2>`,
    panel("", cards([
      { k: "Time", v: "24/7", p: "Perps on crypto, and on stocks, indices, gold and FX too." },
      { k: "Cost", v: "Hourly funding", p: "Plus taker/maker fees." },
      { k: "Orders", v: "Rationed", p: "1 action per 1 USDC traded, plus a 10,000 start buffer." },
      { k: "History", v: "~3.5 days of 1m", p: "QMX must record its own history." },
    ])),
    `<h2>Scalper types</h2>`,
    panel("", `<div class="cards">${[
      ["Keep 5", "Momentum, mean reversion, volatility expansion, session open, VWAP"],
      ["Change 3", "Order-flow sniper splits by data; liquidity window and funding become router settings"],
      ["Drop 1", "Cross-venue latency"],
      ["Add 2 + guard", "Liquidity-sweep reversal, passive maker; a guard that flags martingale and grid"],
    ].map(([v, t]) => `<div class="card"><div class="v">${v}</div><p>${t}</p></div>`).join("")}</div>`),
    chips("fig-mkt", [
      ["improve", "Instrument spec v1 (FX, metals, index CFDs first) is foundation 5", null],
      ["improve", "A 'don't hold across rollover or a funding hour' exit block", null],
      ["found", "The docs still say no futures or options: an old rule to overturn", null],
    ]),
  ] };
});

CONTENT["library.html"] = page((p) => {
  const f = libraryFig();
  return { script: figScript("fig-lib", f), body: [
    head(p, "proposed", "QML, upgraded in place into the library agents use to build units. One small door, a lot behind it."),
    figCard({ id: "fig-lib", name: "Fig 10 · The unit library", svg: f.svg }),
    chips("fig-lib", [
      ["proposed", "<b>You write</b> one spec and two hooks: entry() and exit()", "inputs"],
      ["proposed", "<b>Six verbs</b>: new, check, test, promote, watch, find", "body"],
      ["proposed", "<b>Refusals name the fix</b>", "slip"],
      ["proposed", "<b>Stages move one way</b>; live needs your click", "stage"],
    ]),
    `<h2>Two files</h2>`,
    panel("", cards([
      { k: "Unit spec", v: "What it is", p: "id, version, family, parent, market, logic and settings with ranges, exits, risk template and ranges, sessions, needs, pod." },
      { k: "Journal", v: "What happened", p: "front page, exam baseline, backtest, stress, paper, live, events, notes." },
    ])),
    `<h2>Promises the library keeps</h2>`,
    panel("", `<div class="nrows">${[
      ["After compiling", "Logic and exits never change", "only calibrated numbers move, inside ranges"],
      ["test()", "Only way into backtest/stress", "the node is the only writer of paper/live"],
      ["Every test", "Counts as a try", "in the unit's family"],
      ["Inside a hook", "No clock, no I/O, no future bar", "only closed, declared data"],
    ].map(([a, b, c]) => `<div class="nrow"><span class="nwhen">${a}</span><span class="nar">&rarr;</span><span class="nwhat"><b>${b}</b><small>${c}</small></span></div>`).join("")}</div>`),
    `<h2>Hidden behind the door</h2>`,
    panel("", `<div class="cloud">${["compiling", "conformance", "footprint", "look-ahead checks", "parity check", "dictionary + blocks", "self-calibrator", "session learner", "exam extraction", "try counting", "QMB door", "journal read/write", "stage machine", "cost + seal stamps"].map((t) => `<span>${t}</span>`).join("")}</div><p class="note" style="margin-top:8px">The QMB seam has two adapters: the real door and an in-memory fake for tests.</p>`),
    chips("fig-lib", [
      ["found", "Only 6 indicators run today; the dictionary was a good start, not sacred", null],
      ["improve", "Add exit blocks and runnable scalper indicators (ATR, VWAP, Bollinger, session range)", null],
      ["found", "Agent door: follow QuantConnect's MCP server", null],
    ]),
  ] };
});

CONTENT["old-rules.html"] = (p) => {
  const rows = [
    ["No futures or options, ever", "Futures and perps allowed, each with its own instrument spec"],
    ["The Book owns exits", "Exits belong to the unit and are tested with it"],
    ["The bot never sizes", "The unit sizes itself, inside your ranges"],
    ["No per-bot paper or probation", "Paper per unit; small siblings may go live at minimum lot (question 3)"],
    ["No per-bot warm-up", "Open: does it also ban indicator warm-up when a unit joins a market?"],
    ["Stored composite scores banned", "Keep any fitness ranking sort-only, or amend the rule"],
    ["Cost calibration left empty", "Fill it from published costs first, then demo fills"],
    ["QML rebuilt from scratch (13 Oct)", "QML upgraded in place into the unit library"],
    ["MIS = blocks bots read (20 Oct lean)", "Reversed: unit rules never read the MIS"],
  ];
  const body = [
    head(p, "improve", "Written rules from earlier sessions that clash with the new design. Each needs a recorded overrule before building starts."),
    `<div class="clash">${rows.map(([o, n]) => `<div class="cl"><span class="old"><em>Written today</em>${o}</span><span class="arrow">&darr;</span><span class="new"><em>Proposed</em>${n}</span></div>`).join("")}</div>`,
    panel("Why this is first", `<p>Agents cite the old rulings and refuse. Recording the overrules is foundation 1, and the docs get one rewrite pass after the design is agreed.</p>`),
  ].join("");
  return { body, script: "" };
};

CONTENT["build-path.html"] = page((p) => {
  const f = buildFig();
  return { script: figScript("fig-build", f), body: [
    head(p, "proposed", "Ten foundations in order. Each unblocks the next; the last proves the whole chain on the cTrader demo."),
    figCard({ id: "fig-build", name: "Fig 11 · Ten steps to one working unit", svg: f.svg }),
    panel("", `<ol class="steps">${FOUND.map(([, long, cost], i) => `<li data-fig="fig-build" data-for="f${i}" tabindex="0"><b>${long}</b><span class="sz">${cost}</span></li>`).join("")}</ol><p class="note">Size: S small, M medium, L large.</p>`),
    `<h2>Then, after the reference unit</h2>`,
    panel("", flow([{ t: "Self-calibrator v1" }, { t: "Router plan + node cache" }, { t: "Small variants" }, { t: "Pod budget" }, { t: "Crypto, then perps" }, { t: "Expansion workflow" }])),
    `<h2>Where it stands</h2>`,
    chips("fig-build", [
      ["open", "<b>Paused</b> (25 Oct): a deeper talk with you comes first", null],
      ["open", "Then planning, architecture and PRs; coding in another session", null],
      ["found", "Reference unit candidates: index cash-open breakout with a VWAP trail, or FX Asian-range reversion", "flag"],
    ]),
  ] };
});

const QS = [
  ["Same logic on another market: new unit or same unit?", "On 13 Oct you said a variant on a new timeframe becomes a brand new strategy. On 20 Oct you wrote that 1m and 5m are two registry entries, each with its own proof.", "A new instrument, timeframe or broker makes a sibling unit: complete on its own, self-calibrating from its own journal, linked in one family tree. The family shares one try count, and siblings count as one bet where they move together. Sessions and sniping windows stay inside one unit, as its session profile."],
  ["When is something \"new\"?", "Needed so tries are counted fairly and journals stay clean.", "Changing the logic or an exit makes a new version linked to its parent. Moving a setting inside its range keeps the same unit, but each value tried counts as a try. The unit recalibrating its own risk is a journal entry. A model's rewrite is a new unit marked \"rewritten from\", in the same family."],
  ["Who promotes, and small new variants?", "Your click admits each unit to live, from its journal page. This reopens the written rule \"no per-bot paper or probation\".", "A sibling of a unit you already admitted may go live without your click, only at the smallest lot, paid from a monthly evidence budget you set (start: 5% of equity a month), and only after its own backtest and stress test. It grows only as its own trades prove it. A new broker or a new kind of market still needs your click."],
  ["May size grow back after a cut?", "Example: a unit drops from 0.5% to 0.3% risk after a bad week.", "Yes, but only after fresh trades show the edge is still there (say 60 new trades), after a minimum time, and never above the ranges you set. If size could only shrink, normal bad patches would add up and every unit would sit at the minimum within a year. The one-way ratchet goes on the account floor instead."],
  ["House money: everywhere, or only where it helps?", "House money and reverse house money stay.", "Each unit switches them on only when its own record shows streaks (for example: after a win it wins 60% of the time, after a loss 45%). If wins and losses come in random order, pressing only adds risk, and loss points do the safety job."],
  ["Keep the word \"unit\"?", "You used \"bot\", \"algo\" and \"trading algorithm\"; Claude coined \"unit\".", "Keep \"unit\" in QMX, meaning one complete self-calibrating trading algorithm, and say \"bot\" freely in conversation."],
  ["Split the router?", "Your seed said the node holds the MIS.", "Put the planning half on the PC (any machine later) and the cheap live checks on the node. The node always runs from its cached plan, so a PC that is off only means the plan stops being refreshed. After the plan expires, no new entries; open trades and the kill switch carry on."],
  ["Scalper types and seed additions?", "From the markets research and the router report.", "Keep 5 types (momentum, mean reversion, volatility expansion, session open, VWAP). Split the order-flow sniper by data type; make liquidity window and funding router settings, not types. Drop cross-venue latency. Add the liquidity-sweep reversal and the passive maker, plus a guard that flags martingale and grid."],
];
CONTENT["questions.html"] = (p) => {
  const body = [
    head(p, "open", "Only real ambiguity: your intent, words, money or irreversible scope. Each has a recommended answer, so \"yes\" accepts it."),
    QS.map(([q, ctx, rec], i) => `<details class="qa"${i === 0 ? " open" : ""}><summary><span class="n">Q${i + 1}</span><b>${q}</b></summary><div class="body"><p>${ctx}</p><div class="rec"><em>Recommended</em>${rec}</div></div></details>`).join(""),
    panel("Also settled without asking you", `<p class="note">Technical calls Claude settles and reports in one line: the domain-expansion rule and the self-tuning sizing and exits details. They follow from your answers above.</p>`),
  ].join("");
  return { body, script: "" };
};
