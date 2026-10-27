import { CONTENT, page } from "./pages.mjs";
import { pill, chips, figCard, bars, flow, cards, table, figScript, head, panel, opts, was } from "./site2.mjs";
import { replayFig } from "./fig-data.mjs";
import { guardFig } from "./fig-guard.mjs";
import { loopFig } from "./fig-papers.mjs";

// ---------------------------------------------------------------- data
const Y0 = 1970, Y1 = 2026;
const DEPTH = [
  ["EURUSD, daily", 1973, "day"], ["US 500, daily", 1980, "day"], ["Gold, daily", 1999, "day"],
  ["FX ticks + 1-min", 2003], ["Gold 1-min", 2003], ["1-min bars (paid)", 2008, "paid"], ["CME futures (paid)", 2010, "paid"],
  ["Brent oil 1-min", 2010], ["US 500 1-min", 2011], ["Stocks, crypto 1-min", 2017], ["Perps ticks (paid)", 2024, "paid"],
];
const pct = (y) => ((y - Y0) / (Y1 - Y0)) * 100;
const depthChart = `<div class="yr">${DEPTH.map(([l, y, c]) => `<div class="row"><span>${l}</span><span class="trk"><span class="fil" data-c="${c || ""}" style="left:${pct(y).toFixed(1)}%"><i${y >= 2020 ? ' style="left:auto;right:calc(100% + 4px);color:var(--strong)"' : ""}>${y}</i></span><span class="mark" style="left:${pct(2020.17).toFixed(1)}%"></span></span></div>`).join("")}
<div class="axis"><span></span><div style="position:relative;height:12px">${[[1970, "0%"], [1990, "-50%"], [2010, "-50%"], [2026, "-100%"]].map(([y, t]) => `<span style="position:absolute;left:${pct(y).toFixed(1)}%;transform:translateX(${t})">${y}</span>`).join("")}</div></div></div>
<div class="legend" style="margin-top:10px"><span><b style="color:var(--accent)">■</b> free intraday</span><span><b style="color:color-mix(in srgb,var(--accent) 35%,var(--panel-2))">■</b> daily only</span><span><b style="color:var(--t-open)">■</b> paid</span><span><b style="color:var(--t-open)">|</b> default start, March 2020</span></div>`;

CONTENT["data.html"] = page((p) => {
  const f = replayFig();
  return { script: figScript("fig-rp", { ...f, mode: "today" }), body: [
    head(p, "found", "The lookback limit you heard about is a memory bug in QMB's replay reader. No other cap exists. What really limits '1990' is how far back the data goes."),
    figCard({ id: "fig-rp", name: "Fig 8 · The copying reader", svg: f.svg, modes: [["today", "Today"], ["fixed", "Fixed"]] }),
    chips("fig-rp", [
      ["found", "Runs are capped at <b>1,000 steps</b>: about 17 hours of 1-minute bars", "mem"],
      ["found", "Prices are copied <b>three times per step</b>, and the replay check compares whole frames: four places", "fix"],
      ["found", "The docs already say <b>keep all history forever</b>", "tape"],
      ["found", "The 12-month seal hides the <b>newest</b> year. It isn't a lookback cap", "tape"],
    ]),
    `<h2>Three ways to fix the reader</h2><p class="note">Technical. A likely order: A first, B later.</p>`,
    opts([
      ["A", "One shared series, a pointer per step", "Same answers in linear memory. No unit changes. Unblocks 1990 first."],
      ["B", "Keep only the declared window", "Constant memory, like live. Units declare their window; the library already works it out."],
      ["C", "Frames made only when asked", "Long runs stream, but the biggest change to the contract."],
    ]),
    `<h2>How far back each source goes</h2>`,
    panel("", depthChart),
    `<h2>The any-start-date rule</h2>`,
    panel("", cards([
      { k: "Lookback cap", v: "None", p: "Your ruling. If a test wants 1990, allow it." },
      { k: "Default start", v: "1 March 2020", p: "Post-COVID. Configurable, never a cap." },
      { k: "Older than the data", v: "A plain answer", p: "e.g. 'no 1-minute EURUSD before 2003'." },
      { k: "Two sources stitched", v: "Seam recorded", p: "On the dataset's card, because feeds differ." },
    ])),
    `<h2>Dukascopy changed in 2026</h2>`,
    panel("", flow([{ t: "July", s: "old file feed stopped" }, { t: "New feed", s: "behind a bot wall" }, { t: "Needs a real browser" }, { t: "Blocked hour", s: "comes back empty, no error", c: "you" }])),
    chips("fig-rp", [
      ["found", "QMX's own downloader reads the old format, so it likely points at a dead feed", null],
      ["proposed", "Downloader settings: retries on, retry when empty, slow pace, keep flat bars", null],
      ["improve", "Back up the ~10 GB of old ticks: now hard to replace (needs your go)", null],
      ["found", "For your awareness: Dukascopy's terms forbid bots and databases. QMX's stance: personal use, never shared", null],
    ]),
    `<h2>Other sources</h2>`,
    panel("", table(["Class", "Free", "Paid"], [
      ["FX", "Dukascopy 2003; HistData (bid/ask swapped before June 2009); broker history", "1-minute from 2009"],
      ["Index, commodity", "Dukascopy 2010–2012; broker history", "Futures data from 2010"],
      ["Futures", "None deep", "Databento from June 2010, $199/month"],
      ["Crypto perps", "Binance and Bybit bulk files", "Tardis (Hyperliquid since Oct 2024)"],
    ]) + `<p class="note" style="margin-top:8px">TrueFX stopped publishing in January 2026. Paying is question 7.</p>`),
    chips("fig-rp", [
      ["improve", "Shipped code makes the <b>server</b> the main data store; your ruling says the PC", null],
      ["improve", "Shipped code turns the 12-month seal <b>on by default</b>; your ruling says optional, off", null],
    ]),
  ] };
});

// ---------------------------------------------------------------- guard + pod
CONTENT["guard-pod.html"] = page((p) => {
  const f = guardFig();
  return { script: figScript("fig-gp", f), body: [
    head(p, "open", "Your lean: the pod is the BMS, and the BMS already did the account guard's jobs. Three ways to shape it, judged by what a bad edit can reach."),
    figCard({ id: "fig-gp", name: "Fig 9 · Three shapes, one edit", svg: f.svg }),
    chips("fig-gp", [
      ["proposed", "<b>A · One object</b>: pod = BMS = guard + budget + same-bet limits", "a"],
      ["proposed", "<b>B · Two layers</b>: a fixed guard per account, pod templates above", "b"],
      ["proposed", "<b>C · Locked block</b>: one shape; the guard locked inside every pod", "c"],
    ]),
    `<h2>The one small door they share</h2>`,
    panel("", cards([
      { k: "Before every entry", v: "May this unit add risk?", p: "Yes, or no with a reason. Never resizes. Every call journaled." },
      { k: "On every account update", v: "Stop · flatten · alert", p: "A unit or the whole account." },
      { k: "State", v: "Green → black", p: "Rises on its own. Only your click lowers it." },
    ])),
    `<h2>Side by side</h2>`,
    panel("", table(["", "A one object", "B two layers", "C locked block"], [
      ["A bad copilot edit can lower the floor", '<span class="n">YES</span>', '<span class="y">NO</span>', '<span class="y">NO</span>, if code checks the lock'],
      ["Things to learn", "1", "2", "1"],
      ["Copilot can remake pods", "Risky", "Yes", "Yes"],
      ["Matches 'pod is the BMS'", "Exactly", "Partly", "Mostly"],
      ["Matches the shipped node", "Needs a merge", "Closest", "Needs a template format"],
    ])),
    `<h2>Design and instance</h2>`,
    panel("", flow([{ t: "Pod design", s: "in the Lab" }, { t: "Tested in QMB", s: "a portfolio backtest", c: "qmb" }, { t: "Pod instance", s: "on the node, live state", c: "node" }]) + `<p class="note" style="margin-top:10px">Same code, two lenses. Two things stay apart: the overall portfolio vs its configuration, and live trading vs research.</p>`),
    chips("fig-gp", [
      ["found", "The Library already has <b>pod, BMS and pod-block</b> kinds, with empty fields", "c"],
      ["found", "The node's kill line flattens a unit and <b>only you</b> resume it", "b"],
      ["found", "'Pod' means two things today: the Lab's risk system and account-level rules. It needs one", "a"],
      ["proposed", "Every self-configuration writes a <b>calibration receipt</b>: this is how 'self-configuring' becomes visible", null],
      ["open", "<b>Question 1</b>. The sizing maths stays in its own session", null],
    ]),
  ] };
});

// ---------------------------------------------------------------- papers
CONTENT["papers.html"] = page((p) => {
  const f = loopFig();
  return { script: figScript("fig-lp", f), body: [
    head(p, "found", "None of the 8 papers tests FX, CFDs or crypto intraday, or trades live. Take their process, not their numbers. The old Hermes sessions add the record-keeping."),
    figCard({ id: "fig-lp", name: "Fig 10 · The finding loop", svg: f.svg }),
    chips("fig-lp", [
      ["proposed", "Three papers share one loop: <b>card → build → test → feedback</b>. QMX's library verbs fit it", "track"],
      ["proposed", "They add <b>three cheap gates</b>: new vs existing units, complexity, code matches the card", "gates"],
      ["proposed", "Every screen and refinement is <b>a try</b>", "tries"],
      ["proposed", "Workflows end at a <b>proposal card</b>, never a promotion", "proposal"],
    ]),
    `<h2>The 8 papers</h2>`,
    panel("", table(["Paper", "Tested on", "Evidence"], [
      ["Tree-search alpha mining", "China, US stocks; 10–30 days", "Medium-good"],
      ["QuantaAlpha", "China stocks, transfer to US", "Medium-good"],
      ["AlphaAgent", "China, US stocks; next day", "Medium"],
      ["Multi-agent simulation", "China stocks; weekly", "Medium"],
      ["Strategy finding with LLMs", "China, US stocks; daily", "Weak: Sharpe 0.29 to 13 across tables"],
      ["MarketSenseAI 2.0", "US stocks; monthly", "Weak: two bull years"],
      ["FinLlama", "US stocks; daily", "Weak: no costs"],
      ["Cross-asset risk", "Non-finance data", "None"],
    ])),
    `<h2>Two lessons for judging</h2>`,
    panel("", cards([
      { k: "Lesson 1", v: "Search makes overfitting", p: "The test gap widens with refinement depth; gains fade after about 15 rounds. Count every screen as a try." },
      { k: "Lesson 2", v: "LLM memory is look-ahead", p: "A model may remember what worked. LLM-built units need a test window after the model's training cutoff." },
    ])),
    `<h2>Ten checks for the judging skill</h2><p>Each is a script. The model explains; numbers decide nothing alone; you decide.</p>`,
    `<ul class="chips">${[
      "Tries include screens, refinements, mutations and best-of-N picks",
      "Show each winner's round and depth; flag late, deep winners",
      "Overfit signs by count: free settings, blocks, changes, in/out gap, plateau width",
      "Originality and same-bet: two numbers, neither a gate",
      "LLM memory: test window after the model's cutoff",
      "Declared data vs data read; card vs blocks used",
      "Results by year and quarter, and the best quarter's share",
      "Exposure: how much is just the market moving",
      "A checklist for claims from papers and articles",
      "Same unit on sibling markets, shown beside the parent",
    ].map((t, i) => `<li class="chip">${pill("proposed")}<span><b>J${i + 1}</b> ${t}</span></li>`).join("")}</ul>`,
    `<h2>Six workflow templates</h2>`,
    `<div class="loop">${[
      ["Idea to unit", "Finding. The loop above."], ["Tree-search refinement", "Finding. Improves one unit; stops when the test gap widens."],
      ["Zoo hygiene", "Filtering. Weekly: per-year tables, crowding, look-alikes."], ["LLM-memory probe", "Filtering. Asks the model for 'the best' with no search; compares to random."],
      ["News labeler", "Router. Timestamped news labels on the PC, for direction only."], ["Consensus study", "Router research. Do our units agreeing predict the next hour?"],
    ].map(([b, t]) => `<div><b>${b}</b>${t}</div>`).join("")}</div>`,
    `<h2>Habits we don't copy</h2>`,
    panel("", table(["Paper habit", "Instead"], [
      ["No human in the loop", "Workflows stop at a proposal card"],
      ["An LLM score decides", "An advisory note; counted signs decide"],
      ["One combined score", "A temporary sort inside a run; store only the parts"],
      ["Hard caps (3 settings, fixed thresholds)", "Editable defaults for agents; they warn, never refuse"],
      ["An LLM in the trade path", "Text models write timestamped labels; a unit may read them like any feed"],
    ])),
    `<h2>The Hermes gold mine</h2><p>The sessions that built the old idea library. The Stats folder is the right one.</p>`,
    panel("", cards([
      { k: "Correction", v: "Hermes built an idea library", p: "Not QML. Today's plan merges them: QML becomes the unit library, the old one gives it ideas and lineage." },
      { k: "Gold", v: "Records worth keeping", p: "Dictionary → roles → logic graph; honest labels; variants as small edits; typed family links; named ports; one home per source with exact quotes." },
      { k: "Gold", v: "The old test design", p: "Result identity, tries control, signal counts per step, value added to the book." },
      { k: "Still rejected", v: "Ceremony", p: "Specialist fleets, approval steps for entries, staging, one overall score." },
      { k: "Reversed now", v: "Old placements", p: "'Sizing and exits belong to the Book', 'no test records'." },
    ])),
    chips("fig-lp", [
      ["improve", "The best originals live only in Hermes's own store, with no backup. Old logs hold passwords: clean before any copy (needs your go)", null],
      ["proposed", "The 359 saved sources become the first intake once judging works", null],
    ]),
  ] };
});

// ---------------------------------------------------------------- questions
const Q = [
  { t: "Account guard and pod", why: "Your lean is that the pod is the BMS, and the BMS already did the guard's jobs. The real risk to weigh: whether a copilot remaking a pod can ever lower the safety floor.", o: [["a", "One object", "Pod = BMS = guard + shared budget + same-bet limits, one per account. Simplest; one edit can reach the floor.", 1], ["b", "Two layers", "A fixed guard per account nobody can remove; pod templates above it that a copilot may remake."], ["c", "One shape, locked block", "Every pod template carries the guard as a part that can't be edited, checked by code."]], see: ["guard-pod.html", "Guard and pod"] },
  { t: "What your click admits", why: "The router now directs and never switches, and only you promote. This decides what 'admitted' covers, so the router knows where it may direct live trades.", o: [["a", "One unit on one market", "Every new market needs a new click."], ["b", "An envelope you tick", "Markets, sessions, brokers. The router directs live only inside; outside becomes a paper sibling proposal."], ["c", "Anything the unit's conditions allow", "Widest: the unit's own needs decide."]], see: ["envelope.html", "The admission envelope"] },
  { t: "With the router off", why: "Units stay independent, so they keep trading when the router is down. The question is how far.", o: [["a", "Home market only", "The safest; loses the rest of the envelope."], ["b", "The whole admitted envelope", "On the unit's own conditions."], ["c", "Follow the last offers until they expire", "Then fall back to home."]], see: ["envelope.html", "Try the three 'Router off' buttons"] },
  { t: "Units reading market labels", why: "In your dictation you leaned toward units reading both live prices and the market labels. The 20 October note said unit rules never read them. If they do, part of the label system moves inside the unit.", o: [["a", "Never", "Labels serve the router and guards only."], ["b", "Optional, with a declared fallback", "Tested in QMB with and without."], ["c", "Freely, like any feed", "A variant, c', keeps independence: the unit computes the label itself when the shared copy is missing."]], see: ["independence.html", "Units stand alone"] },
  { t: "The paper sequence", why: "Judging uses history and paper trading together, which lowers overfitting. This sets when paper starts. Paper is never live, so it also settles whether an agent may start a paper sibling without your click.", o: [["a", "Strict", "Paper only after the sealed check, for every unit."], ["b", "Parallel", "Paper starts when stress passes, beside the sealed check."], ["c", "Sibling fast lane", "Siblings of live units paper for less, judged against the parent."]], see: null },
  { t: "Your unfinished thought", why: "In the review you started an idea about market conditions over time and stopped. Three guesses at it:", o: [["a", "A market almanac", "Each instrument's conditions over time: spread, volatility, session behaviour by month."], ["b", "A cell map", "Where alpha lives (family × instrument × condition) and how it moves."], ["c", "Cost-aware placement", "The best broker and hour for each unit: 'gold fits my scalper but costs are high: broker or hour?'"], ["d", "Something else", "In your own words."]], see: ["journals.html", "Journals and logs"] },
  { t: "Paying for data", why: "Money, so your call. Free sources plus our own recording cover FX, gold, indices and crypto. Futures and perps depth need paid feeds.", o: [["a", "Free only", "Dukascopy, HistData, Binance bulk files, broker history, our own recording."], ["b", "Add Databento when a futures unit is real", "$199 a month, CME data from June 2010."], ["c", "Add Tardis when a perps unit is real", "Tick trades and order books for perps, Hyperliquid since October 2024."]], see: ["data.html", "Data and lookback"] },
  { t: "A name for the trading router", why: "In the code, the name 'router' already belongs to the AI-model router, the part that picks which AI provider answers. The trading router needs its own name. Vocabulary, so your call.", o: [["a", "A new name for the trading router", "Your word."], ["b", "Rename the AI-model router instead", "And keep 'router' for trading."]], see: ["router.html", "The router directs"] },
];
CONTENT["questions.html"] = page((p) => ({ script: "", body: [
  head(p, "open", "Each question is explained first, then its options. No answer is picked or recommended. We go through them one at a time."),
  ...Q.map((q, i) => `<details class="qa"${i === 0 ? " open" : ""}><summary><span class="n">${i + 1}</span><b>${q.t}</b></summary><div class="body"><h4>Why it matters</h4><p class="why">${q.why}</p><h4>Options</h4>${opts(q.o.map(([l, t, d, lean]) => [l, t, d, lean]))}${q.see ? `<p class="see">See: <a href="${q.see[0]}">${q.see[1]}</a></p>` : ""}</div></details>`),
  `<h2>For your awareness, not questions</h2>`,
  `<ul class="chips">${[
    ["found", "Dukascopy's terms forbid bots and databases. QMX's stance: personal use, never shared"],
    ["found", "A bigger local disk is the only full fix for keeping tick archives on the PC"],
    ["improve", "Backing up the ~10 GB of old Dukascopy ticks needs your go"],
    ["open", "Risk and sizing (size regrowth, house money, the floor) gets its own session"],
  ].map(([t, s]) => `<li class="chip">${pill(t)}<span>${s}</span></li>`).join("")}</ul>`,
] }));
