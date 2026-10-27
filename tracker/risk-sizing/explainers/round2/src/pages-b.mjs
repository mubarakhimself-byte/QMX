import { CONTENT, page } from "./pages.mjs";
import { PAGES, pill, chips, figCard, bars, flow, cards, table, figScript, head, panel, opts, was, ROUND1 } from "./site2.mjs";
import { hubFig } from "./fig-hub.mjs";
import { indepFig } from "./fig-indep.mjs";
import { poolFig, leaseFig } from "./fig-feeds.mjs";
import { journalsFig } from "./fig-journals.mjs";
import { ideasFig } from "./fig-ideas.mjs";

// ---------------------------------------------------------------- hub
CONTENT["index.html"] = (p) => {
  const f = hubFig();
  const list = PAGES.slice(1).map((q, i) => `<a href="${q.file}"><i>${String(i + 1).padStart(2, "0")}</i><b>${q.name}</b><span>${q.blurb}</span></a>`).join("");
  const chg = (id, t, s) => `<div class="chg" data-fig="fig-hub" data-for="${id}" tabindex="0"><b>${t}</b><small>${s}</small></div>`;
  const body = [
    `<p class="eyebrow">Unit system · round 2 ${pill("proposed")}</p><h1>QMX unit system: round 2</h1><p class="lede">Your review of 27 October changed five things. This round turns them into options, in pictures.</p>`,
    `<div class="banner">Options only. Nothing here is decided.<small>Every page shows options side by side. Nothing is folded into the architecture until you have talked them through. Tags: ${pill("found")} ${pill("proposed")} ${pill("open")} ${pill("improve")}</small></div>`,
    figCard({ id: "fig-hub", name: "The round 2 bench", svg: f.svg, hint: "Tap a part to open its page" }),
    `<h2>What changed since round 1</h2>`,
    `<div class="changes">${[
      chg("router", "The router directs and never switches", "Round 1 had it turning units on and off. Now it only offers, and offers expire."),
      chg("units", "Units stand alone", "Router, PC link or Library down: a unit keeps trading on its own conditions."),
      chg("lock", "Only you promote", "No automatic minimum-lot promotion. The only automatic step is a risk stop, logged."),
      chg("data", "Unbounded by default", "No lookback cap; post-COVID is a default. Plain Python, ML and mini apps are never blocked."),
      chg("pc", "Local first", "Everything works on your PC alone. Servers extend or stand in, never replace."),
    ].join("")}</div>`,
    `<h2>Your answers to round 1</h2>`,
    panel("", table(["Question", "Your answer"], [
      ["1 · Sibling unit", "Yes, rethought for agents"],
      ["2 · What counts as new", "Held: may come from the old Hermes design"],
      ["3 · Promotion", "Only you. Auto minimum-lot rejected"],
      ["4–5 · Size regrowth, house money", "Not decided: own risk session"],
      ["6 · The word 'unit'", "Keep it"],
      ["7 · Router split", "Yes, with the corrections above"],
      ["8 · Scalper types", "Defaults, never a cage"],
    ])),
    `<h2>Pages</h2><div class="pages">${list}</div>`,
    `<a class="round1" href="${ROUND1}" target="_blank" rel="noopener"><span><b>Round 1 site</b>The converged design you reviewed: 14 pages.</span><span class="go">Open &rarr;</span></a>`,
    panel("What comes next", chips("fig-hub", [
      ["open", "We talk these pages through, then your 8 questions, one at a time", null],
      ["open", "Risk and sizing gets its own session, with the maths", null],
      ["open", "Only after both: fold the choices into the architecture", null],
    ])),
  ].join("");
  return { body, script: figScript("fig-hub", f) };
};

// ---------------------------------------------------------------- independence
CONTENT["independence.html"] = page((p) => {
  const f = indepFig();
  return { script: figScript("fig-ind", { ...f, mode: "router" }), body: [
    head(p, "proposed", "Everything a unit needs to trade sits on its own machine. The router, the PC link and the Library are extras. Pull a cable and see."),
    figCard({ id: "fig-ind", name: "Fig 3 · Pull a cable", svg: f.svg, modes: [["router", "Router down"], ["pc", "PC link down"], ["feed", "Feed stale"], ["guard", "Guard down"], ["labels", "Labels missing"]] }),
    chips("fig-ind", [
      ["proposed", "<b>Hard needs, all local</b>: spec, your admission, feed, guards, journal", "node"],
      ["proposed", "<b>Soft</b>: router offers and market labels. The PC and Library aren't needed to trade", "router"],
      ["found", "The shipped node already shows <b>'unreachable since …'</b> and keeps last values", "pc"],
      ["found", "The news guard already <b>fails entries closed</b> while exits continue", "guard"],
      ["found", "The Library already has an <b>outbox</b> for writes that can't go yet", "lib"],
    ]),
    `<h2>What a unit needs</h2>`,
    panel("", table(["Need", "Kind", "When it's missing"], [
      ["Spec and code", "Hard", "Can't start: a deploy problem, not a trading one"],
      ["Your admission", "Hard", "Can't start; never fetched live"],
      ["Feed per symbol", "Hard", "No new entries on that symbol; open trades keep broker stops"],
      ["Warm-up history", "Hard at start", "Waits, locked from trading, as QMB already does"],
      ["Guards", "Hard", "No new entries on that account (fail closed)"],
      ["Journal", "Hard", "Written before every order; a refusal blocks the entry"],
      ["Router offers", "Soft", "Offers expire; router-off mode (question 3)"],
      ["Market labels", "Soft or none", "Declared fallback or compute locally (question 4)"],
      ["PC link", "None", "Your screen shows 'unreachable since …'"],
      ["Library", "None", "Writes wait in an outbox"],
    ])),
    `<h2>Guards stand alone too</h2>`,
    panel("", flow([{ t: "Local inputs", s: "feed, news calendar, broker account" }, { t: "Spread · news · account guards" }, { t: "Verdict", s: "allow · block new · flatten" }, { t: "Guard journal" }]) + `<p class="note" style="margin-top:10px">No router and no PC in any guard's inputs.</p>`),
    chips("fig-ind", [
      ["proposed", "<b>Drill</b>: unplug the router, the labels and the PC during a node self-test; the guard still stops", "guard"],
      ["proposed", "Weekly drills on demo, with the outcome journaled", null],
    ]),
    `<h2>Units reading market labels</h2><p>You leaned toward units reading both live data and the market labels. Four ways to do it:</p>`,
    opts([
      ["a", "Never", "Units read raw prices only; labels serve the router and guards. Total independence, but each unit recomputes things like 'is spread wide?'."],
      ["b", "Optional, with a declared fallback", "The unit lists the labels it uses and what to do without each one. QMB tests it both ways."],
      ["c'", "Compute where you are", "Labels are library code. The unit reads the shared copy, or computes it itself with the same code when that copy is missing. Works for rule labels, not trained models."],
      ["c", "Freely, like any feed", "Simplest to write, but an outage silently changes behaviour unless paired with c'."],
    ]),
    `<h2>One clock per job</h2>`,
    was("The plan expires after 5 trading days; then no new entries anywhere.", "No single clock. Each job gets its own, so a scalper never waits on a 5-day plan."),
    panel("", table(["Job", "Clock", "Example default"], [
      ["Live facts: spread, feed age", "Seconds", "Stale after 5× the usual gap for that hour"],
      ["Router offers", "Session windows", "An offer lives for the window it names"],
      ["A unit's own calibration", "Its own trades", "After N closed trades, never a calendar"],
      ["Slow labels and plans", "Days or events", "Daily, plus label flips, holidays, clock changes"],
      ["Model retraining", "Data months", "On a frozen month or a decay alarm"],
    ]) + `<p class="note" style="margin-top:8px">Every default is configurable.</p>`),
    chips("fig-ind", [["open", "<b>Question 4</b>: never, optional with fallback, or freely", "labels"], ["open", "<b>Question 3</b>: what a unit trades while the router is off", "router"]]),
  ] };
});

// ---------------------------------------------------------------- feeds
CONTENT["feeds.html"] = page((p) => {
  const f = poolFig(), g = leaseFig();
  return { script: figScript("fig-pool", f) + figScript("fig-lease", g), body: [
    head(p, "proposed", "One feed keeper per broker connection subscribes once per symbol and fans each price out to every unit, guard and the router on that machine."),
    figCard({ id: "fig-pool", name: "Fig 4 · One cable, many readers", svg: f.svg }),
    chips("fig-pool", [
      ["proposed", "<b>One subscription per symbol</b>, never per unit: 200 units on 60 symbols = 60", "keeper"],
      ["proposed", "<b>Last-value cache</b>: a starting unit reads the latest price at once", "units"],
      ["proposed", "Warm-up comes from <b>our recorder</b>, keeping the broker's history limit for gap repair", "recorder"],
      ["proposed", "The router is <b>a reader</b>, never in the data path", "router"],
    ]),
    `<h2>PC and node take turns</h2><p>On cTrader, the PC and the node shouldn't both hold the live connection.</p>`,
    figCard({ id: "fig-lease", name: "Fig 5 · The lease", svg: g.svg }),
    chips("fig-lease", [
      ["found", "cTrader's docs say you <b>should</b> open one demo and one live connection per app: advice, not a hard cap", "ctrader"],
      ["found", "A second machine <b>refreshing the same sign-in</b> logs the first one out", "lease"],
      ["proposed", "Three ways: a <b>lease</b>, <b>two apps</b> (two sign-ins), or node = live and PC = demo", "pc"],
      ["improve", "A one-minute test on demo settles the socket question", null],
    ]),
    `<h2>Each platform's rule</h2>`,
    panel("", table(["Platform", "Rule", "Keeper shape"], [
      ["cTrader", "Advises 1 demo + 1 live per app; no symbol cap; 50 requests/s", "One keeper per app and environment; one live holder"],
      ["MT5", "One terminal per account; Windows only", "Keeper on a Windows machine"],
      ["Hyperliquid", "Per IP: 10 connections, 1,000 subscriptions", "Each machine subscribes on its own"],
      ["Binance", "1,024 streams per connection; cut every 24 h", "Rotate before the cut"],
      ["Futures feeds", "Paid per exchange subscription", "Price per feed, never per unit"],
    ])),
    `<h2>Three shapes for the bus</h2><p class="note">Technical, not your call. Settled by one demo test.</p>`,
    opts([
      ["A", "In one process", "Keeper and units share a process. Nothing to install; one crash takes its units down, so use a few worker processes."],
      ["B", "Local message bus", "Units, guards, router and recorder as separate processes on one machine."],
      ["C", "A feed service per machine", "The PC can read the node's live pool over the private network, for watching and research only."],
    ]),
    `<h2>Recording our own history</h2>`,
    panel("", flow([{ t: "Feed keeper", c: "node" }, { t: "Recorder" }, { t: "Price store", s: "the one QMB reads" }]) + `<div style="height:8px"></div>` + flow([{ t: "Feed keeper", c: "node" }, { t: "Roller" }, { t: "Market journal", s: "costs per minute" }])),
    chips("fig-pool", [
      ["found", "The node records spot ticks into the archive, but <b>no live collector</b> exists yet", "recorder"],
      ["proposed", "Our own recording is the way out if Dukascopy closes, and fixes Hyperliquid's short history", "recorder"],
    ]),
    `<h2>How much space</h2><p>200 units on 60 instruments. Prices are stored per instrument, never per unit.</p>`,
    panel("", bars([
      { label: "Ticks since 2003", value: 175, max: 200, text: "150–200 GB", c: "warn" },
      { label: "Live ticks, per broker per year", value: 15, max: 200, text: "10–20 GB" },
      { label: "1-minute bars since 2003", value: 14, max: 200, text: "≈14 GB", c: "ok" },
      { label: "Market journal per year", value: 1.5, max: 200, text: "1–2 GB", c: "ok" },
      { label: "Unit journals per year", value: 0.4, max: 200, text: "a few 100 MB", c: "ok" },
      { label: "Your PC's free disk", value: 20.3, max: 200, text: "12 + 8.3 GB", c: "mute" },
    ]) + `<p class="note" style="margin-top:10px">Estimates. Bars fit on the PC; ticks live on a storage machine and the PC caches the months a run needs. A bigger local disk is the only full fix for local-first ticks: your call.</p>`),
  ] };
});

// ---------------------------------------------------------------- journals
const spark = `<svg class="spark" viewBox="0 0 120 28" preserveAspectRatio="none" aria-hidden="true"><line x1="0" y1="18" x2="120" y2="18" stroke="var(--line)" stroke-width="1"/><polyline fill="none" stroke="var(--accent)" stroke-width="1.6" points="0,18 8,14 16,16 24,10 32,12 40,9 48,15 56,11 64,8 72,13 80,7 88,10 96,6 104,9 112,5 120,7"/><circle cx="120" cy="7" r="2" fill="var(--accent)"/></svg>`;
CONTENT["journals.html"] = page((p) => {
  const f = journalsFig();
  return { script: figScript("fig-jr", f), body: [
    head(p, "proposed", "The unit journal is the unit's DevOps layer: monitoring, logging, observability. Beside it, three more streams. Each has one writer; they join by keys, never by copies."),
    figCard({ id: "fig-jr", name: "Fig 6 · Four books, four writers", svg: f.svg }),
    chips("fig-jr", [
      ["proposed", "<b>Unit journal</b>: the unit's own trades, signals, fills and notes", "uj"],
      ["proposed", "<b>Market journal</b>: spread, fees, swap and sessions per market, once", "mj"],
      ["proposed", "<b>Router decision log</b>: every offer with its inputs, replayable", "rl"],
      ["proposed", "<b>Guard journal</b>: so automatic stops are monitored", "gj"],
    ]),
    `<h2>What the unit journal keeps</h2>`,
    panel("", cards([
      { k: "Taken", v: "Every trade", p: "Orders, fills, its own slippage, exits." },
      { k: "Seen, not taken", v: "With a reason", p: "Spread, session, max positions, guard, low strength, no offer." },
      { k: "Missed", v: "Found afterwards", p: "Would have fired, but offline or the feed was stale. Found by replay." },
      { k: "Calibration receipts", v: "Which number moved", p: "From which data, by which rule, inside which range." },
      { k: "Offer outcomes", v: "Taken · ignored · expired", p: "Lets us measure whether the router earns its keep." },
      { k: "Agent notes", v: "Notes and proposals only", p: "With evidence links and an expiry, written through a hook." },
    ])),
    `<h2>One id from source to trade</h2>`,
    panel("", flow([{ t: "Source", s: "video at 12:40" }, { t: "Idea record" }, { t: "Unit v1" }, { t: "Unit v2" }, { t: "Trade", s: "signal → checks → order → fill → exit" }]) + `<p class="note" style="margin-top:10px">The trade points into the market journal (broker, account, instrument, minute) and the router log by key. "Where do winners come from" becomes a simple count per source, with tries counted.</p>`),
    `<h2>Preview and detailed view</h2><p>One record, shown small or in full. The same record serves agents and your screen.</p>`,
    `<div class="mock"><div class="mk"><div class="k">Preview · example</div><h4>Asian-range reversion · EURUSD</h4><dl><dt>Stage</dt><dd>Paper</dd><dt>Origin</dt><dd>Video, 12:40</dd><dt>Family</dt><dd>Asian range · 4 units</dd><dt>Tries</dt><dd>37</dd><dt>Grade</dt><dd>Stressed</dd><dt>Guard</dt><dd>Green</dd><dt>Proposals</dt><dd>1 open</dd></dl>${spark}<div class="note" style="margin-top:2px">Last 30 trades, in R</div></div>
<div class="mk"><div class="k">Detailed view · example</div><h4>Same unit, every part</h4><div class="tabs"><span>Journal</span><span>Lineage</span><span>Market map</span><span>Runs</span><span>Calibrations</span><span>Proposals</span><span>Notes</span><span>Offers</span></div><p class="note" style="margin-top:8px">Family tree in preview: a small graph, coloured by stage, sized by trades. Tap any node for its detailed view.</p></div></div>`,
    `<h2>Three ways to store it</h2><p class="note">Technical, not your call.</p>`,
    opts([
      ["A", "Plain append-only files", "Monthly partitions, one writer each. Simplest on the PC."],
      ["B", "Observability traces", "Each trade is a trace. The node already ships this monitoring stack; an exporter still writes the files."],
      ["C", "Inside the Library", "Lineage, search and cards come free, but the catalogue grows with every trade."],
    ]),
    `<p class="note">A likely blend: A as the record, B for live dashboards, C for notes, proposals and calibration receipts.</p>`,
    `<h2>Where it lives</h2>`,
    panel("", table(["Data", "PC", "Storage machine", "Bucket"], [
      ["1-minute bars, active", "yes", "yes", "yes"],
      ["Ticks", "months a run needs", "all", "all"],
      ["Unit journals", "recent months", "all", "all"],
      ["Market journal", "last year", "all", "all"],
      ["Router and guard logs", "recent months", "all", "all"],
    ])),
    chips("fig-jr", [
      ["proposed", "Events by default; every bar on request; tick debug for a set time", "uj"],
      ["proposed", "Keep every losing trade's full trace, sample the winners (an option)", "uj"],
      ["proposed", "Stopped units keep journaling on paper so data keeps flowing", "uj"],
      ["proposed", "On any guard stop, save the last minutes of feed and decisions", "gj"],
    ]),
  ] };
});

// ---------------------------------------------------------------- ideas
CONTENT["ideas.html"] = page((p) => {
  const f = ideasFig();
  return { script: figScript("fig-id", f), body: [
    head(p, "proposed", "Every unit traces back to where it came from. An idea record sits in front of units, and families grow by versions, siblings and transplants."),
    figCard({ id: "fig-id", name: "Fig 7 · From source to family", svg: f.svg }),
    chips("fig-id", [
      ["found", "The Library has a <b>hypothesis</b> record with a statement and a source spot", "idea"],
      ["found", "It has 25 link types; <b>sibling, transplanted-from and rewritten-from</b> are missing", "famY"],
      ["proposed", "<b>Transplant</b>: move one named part across families; a try in the receiver", "block"],
      ["found", "Round 1's funnel dropped 'genetic crossover'. Your 26 August idea brings it back: record the overrule", "block"],
      ["proposed", "Plain Python, ML and mini apps are <b>never blocked</b>, only flagged", "kinds"],
    ]),
    `<h2>Where winners come from</h2>`,
    panel("", flow([{ t: "Every source", s: "kind, creator, model, workflow" }, { t: "Survivors" }, { t: "÷ ideas it fed" }, { t: "Next month's intake", s: "proposed; you approve" }]) + `<p class="note" style="margin-top:10px">It needs months of journals before it says much. Plan it now, expect value later.</p>`),
    `<h2>Three ways to hold ideas</h2>`,
    opts([
      ["A", "Grow the hypothesis record, add four links", "Class, claims with exact spots, origin. Links: sibling, transplanted, rewritten, composed. A small change."],
      ["B", "A new idea record; the child carries its edit", "The kind of edit (transplant, sibling, rewrite, composite, correction, version) sits on the child. 'New or same' is then read off the edit."],
      ["C", "No idea record", "Smallest. But the old backlog of ideas has no home, and 'where winners come from' needs ideas as rows."],
    ]),
    `<h2>"Is it new?" from the old design</h2><p>Held by you. The old Hermes design answered it by the kind of edit:</p>`,
    panel("", `<div class="nrows">${[
      ["Costs, data or tester changed", "Re-run", "same unit"],
      ["The extraction was wrong", "Corrected successor", "the old one marked wrong"],
      ["Two parents mixed", "Composite", "both parents named"],
      ["Logic or exit changed", "New version", "linked to its parent"],
      ["Same logic, new market", "Sibling", "same family, shared tries"],
    ].map(([a, b, c]) => `<div class="nrow"><span class="nwhen">${a}</span><span class="nar">&rarr;</span><span class="nwhat"><b>${b}</b><small>${c}</small></span></div>`).join("")}</div>`),
    `<h2>Free beside the standard</h2><p>The library and its schemas are a standard for agents, so cheaper models don't make big mistakes. They never stop you or a mini app.</p>`,
    panel("", cards([
      { k: "Kind", v: "Library graph or hooks", p: "The agent standard." },
      { k: "Kind", v: "Plain Python", p: "Any class with a per-bar step runs in QMB. Counted as tries." },
      { k: "Kind", v: "ML model, ensembler", p: "Retrained inside the backtest, versioned." },
      { k: "Rule", v: "Same check, two modes", p: "Refuses in agent mode, warns in human mode." },
    ])),
    chips("fig-id", [
      ["found", "The node refuses unchecked Python bots in a live seat: a tension for the node session", "kinds"],
      ["proposed", "A failure library per family: typed reasons, read by agents before they generate", "famX"],
      ["proposed", "Hooks write each step that made a unit (built, tested, mutated, crossed) into its journal", "famX"],
    ]),
  ] };
});
