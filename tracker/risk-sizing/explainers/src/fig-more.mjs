import { bench, svgOf } from "./parts.mjs";

// ---- Markets: a socket panel. Each market type lights the backend pieces it needs: green = exists, red = missing.
export const SOCKETS = [["costs", "COSTS"], ["swap", "SWAP"], ["funding", "FUNDING"], ["expiry", "EXPIRY+ROLL"], ["divs", "DIVIDENDS"], ["sessions", "SESSIONS"], ["replay", "REPLAY"], ["venue", "VENUE"]];
export const MARKETS = [
  ["fx", "FX CFD", { costs: "ok", swap: "ok", sessions: "ok", replay: "ok", venue: "ok" }, "FX: the one market the backend models end to end."],
  ["metal", "METALS", { costs: "ok", swap: "ok", sessions: "bad", replay: "ok", venue: "ok" }, "Gold and silver: own daily break, no calendar for it yet."],
  ["index", "INDEX CFD", { costs: "ok", swap: "ok", divs: "bad", sessions: "bad", replay: "ok", venue: "ok" }, "Index CFDs: dividend adjustments and index hours missing."],
  ["cmdty", "COMMODITY", { costs: "ok", swap: "ok", expiry: "bad", sessions: "bad", replay: "ok", venue: "ok" }, "Commodity CFDs expire 2 working days early and are never rolled."],
  ["stock", "STOCK CFD", { costs: "ok", swap: "ok", divs: "bad", sessions: "bad", replay: "ok", venue: "bad" }, "Stock CFDs at IC are MT5 only. cTrader can't trade them."],
  ["fut", "FUTURES", { costs: "warn", expiry: "bad", sessions: "bad", replay: "warn", venue: "bad" }, "CME futures: expiry and roll, sessions and a venue all missing."],
  ["perp", "PERPS", { costs: "ok", funding: "bad", sessions: "ok", replay: "bad", venue: "bad" }, "Hyperliquid perps: hourly funding, no replay, CCXT is spot only."],
  ["spot", "SPOT CRYPTO", { costs: "ok", sessions: "ok", replay: "bad", venue: "ok" }, "Spot crypto: venue works; QMB can't replay it (quotes only)."],
];
export function marketsFig() {
  const BENCH = { x: -122, y: -64, w: 244, d: 134, r: 8 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-84, -46, 40]], { width: 400, pad: 8 });
  const { box, cyl, hot, L, k, P, labelY, liveY, lamp } = B;
  const out = [B.base(BENCH, { h: 8 })];
  out.push(box({ x: -112, y: -56, w: 224, d: 96, r: 4 }, 0, 8, { tone: "mid", bevel: 0.8 }));
  SOCKETS.forEach(([id, name], i) => {
    const row = Math.floor(i / 4), col = i % 4;
    const cx = -81 + col * 54, y = row ? 4 : -48, h = row ? 12 : 26;
    const top = 8 + h;
    out.push(hot("s-" + id, [box({ x: cx - 24, y, w: 48, d: 30, r: 2 }, 8, h, { tone: "mid", bevel: 0.6 }), cyl(cx - 8, y + 15, 7, top, 1.2, { tone: "lo" }), L(k.ring(cx - 8, y + 15, 3.5, top + 1.2, P, 18), { tone: "mid" }), L(k.ring(cx - 8, y + 15, 1.2, top + 1.2, P, 10), { tone: "mid" }), lamp(id, cx + 12, y + 15, top, { r: 3.6 }), labelY(name, cx, y + 30, 8 + (row ? 2 : 6), { px: 3.6 })].join("")));
  });
  out.push(hot("market", [box({ x: -112, y: 44, w: 110, d: 20, r: 2 }, 0, 14, { tone: "hi", bevel: 0.5 }), liveY("mkt", "FX CFD", -57, 64, 4, { px: 5.5 })].join("")));
  const svg = svgOf(B, { label: "A socket panel with eight backend pieces: costs, swap, funding, expiry and roll, dividends, sessions, replay and venue. Pick a market type and each socket it needs lights green if the backend has it, red if it is missing.", body: out });
  const labels = { "s-costs": "Costs: spread, commission, fees.", "s-swap": "Daily swap or financing.", "s-funding": "Hourly funding (perps). Missing.", "s-expiry": "Contract expiry and roll. Missing.", "s-divs": "Dividend adjustments. Missing.", "s-sessions": "Session calendars beyond forex and 24/7. Missing.", "s-replay": "QMB replay: bid/ask quotes only.", "s-venue": "A venue connector that can trade it.", market: "The market type you picked." };
  const all = Object.fromEntries(SOCKETS.map(([id]) => [id, "off"]));
  const one = (id, name, need, say) => `{say:${JSON.stringify(say)},lit:${JSON.stringify(Object.entries(need).filter(([, v]) => v === "bad").map(([s]) => "s-" + s))},lamps:${JSON.stringify({ ...all, ...need })},text:{mkt:${JSON.stringify(name)}},ms:3400}`;
  const modes = "{all:[" + MARKETS.map((m) => one(...m)).join(",") + "]," + MARKETS.map(([id, name, need, say]) => `${id}:[{say:${JSON.stringify(say)},lit:${JSON.stringify(Object.entries(need).filter(([, v]) => v === "bad").map(([s]) => "s-" + s))},lamps:${JSON.stringify({ ...all, ...need })},text:{mkt:${JSON.stringify(name)}},ms:999999}]`).join(",") + "}";
  return { svg, P, labels, modes };
}

// ---- Library: a press with six buttons, a spec card and a hooks card, a stage dial and a try counter.
export function libraryFig() {
  const BENCH = { x: -132, y: -58, w: 264, d: 116, r: 8 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-60, -40, 64]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, liveY, lamp, dial, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  // input tray with spec + hooks cards
  out.push(hot("inputs", [box({ x: -124, y: -40, w: 40, d: 44, r: 2 }, 0, 8, { tone: "mid" }), move("spec", [box({ x: -118, y: -30, w: 28, d: 1.6, r: 0.3 }, 8, 24, { tone: "hi", bevel: 0 }), labelY("SPEC", -104, -28.4, 22, { px: 3.8, plate: false }), L([0, 1, 2].map((i) => k.segment([-114, -28.35, 19 - i * 3], [-94 - i * 3, -28.35, 19 - i * 3], P)).join(""), { tone: "lo", free: true })].join("")), move("hooks", [box({ x: -118, y: -10, w: 28, d: 1.6, r: 0.3 }, 8, 20, { tone: "hi", bevel: 0 }), labelY("HOOKS", -104, -8.4, 18, { px: 3.8, plate: false }), L([0, 1].map((i) => k.segment([-114, -8.35, 15 - i * 3], [-96 - i * 2, -8.35, 15 - i * 3], P)).join(""), { tone: "lo", free: true })].join(""))].join("")));
  // machine body
  const M = { x: -70, y: -48, w: 112, d: 78, r: 4 };
  out.push(hot("body", [box(M, 0, 34, { tone: "mid", bevel: 0.9, steps: 5 }), L(k.planOutline(k.insetPlan(M, 3.5), 34, P, 5), { tone: "faint" }), labelY("UNIT LIBRARY", M.x + 40, M.y + M.d, 8, { px: 5 }), box({ x: -64, y: -44, w: 36, d: 6, r: 1 }, 34, 1, { tone: "lo" }), liveY("tries", "TRIES 12", M.x + 92, M.y + M.d, 10, { px: 3.6 })].join("")));
  // refusal slip popping from the top slot
  out.push(show("slip", move("slipMv", [box({ x: -62, y: -42.5, w: 32, d: 1.6, r: 0.3 }, 20, 16, { tone: "hi", bevel: 0 }), labelY("LOOK-AHEAD", -46, -40.9, 30, { px: 3, plate: false }), labelY("BAR 1,204", -46, -40.9, 24.5, { px: 3, plate: false })].join(""), [0, 0, 0])));
  // six buttons
  const VERBS = [["new", "NEW"], ["check", "CHECK"], ["test", "TEST"], ["promote", "PROMOTE"], ["watch", "WATCH"], ["find", "FIND"]];
  VERBS.forEach(([id, name], i) => {
    const cx = -50 + (i % 3) * 34, cy = -18 + Math.floor(i / 3) * 28;
    out.push(hot("v-" + id, [cyl(cx, cy, 8, 34, 1.4, { tone: "lo" }), move("b-" + id, cyl(cx, cy, 6, 35.4, 4, { tone: "hi", bevel: 0.5 })), labelTop(name, cx, cy + 13, 34, { px: 3.6 })].join("")));
  });
  // stage dial on a pedestal
  const STG = dial("stage", 86, -6, 22, 26, { h: 4, value: 0, from: -0.75 * Math.PI, span: 1.5 * Math.PI, ticks: 25, every: 5 });
  out.push(hot("stage", [box({ x: 58, y: -34, w: 56, d: 56, r: 3 }, 0, 26, { tone: "mid", bevel: 0.6 }), STG.svg, labelY("STAGE: ONE WAY", 86, 22, 6, { px: 3.8 })].join("")));
  out.push(B.wire([42, -6, 16], [58, -6, 16], [], { tone: "mid" }));
  const svg = svgOf(B, { label: "A press called the unit library: a spec card and a hooks card go in on the left; six buttons on top (new, check, test, promote, watch, find); a refusal slip can pop out of the top; a try counter on its face; a stage dial on the right that only turns one way.", body: out });
  const labels = { inputs: "What you write: one spec and two hooks, entry() and exit().", body: "Everything hard hides behind six verbs.", "v-new": "new: build a unit from a spec and hooks.", "v-check": "check: contract, look-ahead, smoke run. Refusals name the fix.", "v-test": "test: backtest or stress through QMB. Always a try.", "v-promote": "promote: moves the stage one way. Live needs your click.", "v-watch": "watch: the journal's front page.", "v-find": "find: search units, templates and blocks first.", stage: "research → backtest → optimise → stress → paper → live.", slip: "A refusal that names the fix." };
  const press = (id) => `move:{"b-${id}":[0,0,-2.5]}`;
  const rel = `"b-new":[0,0,0],"b-check":[0,0,0],"b-test":[0,0,0],"b-promote":[0,0,0],"b-watch":[0,0,0],"b-find":[0,0,0]`;
  const modes = `{main:[
 {say:"You write one spec and two hooks: entry() and exit().",lit:["inputs"],show:{slip:false},text:{tries:"TRIES 12"},dial:{stage:0},move:{spec:[0,0,0],hooks:[0,0,0],${rel}},ms:3200},
 {say:"new: the library builds a unit from them.",lit:["v-new","inputs"],move:{spec:[44,0,8],hooks:[44,0,8],"b-new":[0,0,-2.5]},ms:3000},
 {say:"check: it refuses with the fix, e.g. 'look-ahead at bar 1,204'.",lit:["v-check","slip"],show:{slip:true},move:{"b-new":[0,0,0],"b-check":[0,0,-2.5],slipMv:[0,0,14]},ms:3600},
 {say:"test: backtest or stress through QMB. Every call is a try.",lit:["v-test","body"],show:{slip:false},text:{tries:"TRIES 13"},move:{"b-check":[0,0,0],"b-test":[0,0,-2.5],slipMv:[0,0,0]},dial:{stage:0.4},ms:3400},
 {say:"promote: the stage moves one way. Live needs your click.",lit:["v-promote","stage"],move:{"b-test":[0,0,0],"b-promote":[0,0,-2.5]},dial:{stage:0.8},ms:3400},
 {say:"watch: where it works, tries, exam vs now, health.",lit:["v-watch"],move:{"b-promote":[0,0,0],"b-watch":[0,0,-2.5]},ms:3000},
 {say:"find: search existing units and blocks before writing new code.",lit:["v-find"],move:{"b-watch":[0,0,0],"b-find":[0,0,-2.5]},ms:3000}
]}`;
  return { svg, P, labels, dials: { stage: STG.spec }, modes, ease: 0.5 };
}

// ---- Build order: a staircase of ten foundation blocks; the reference unit climbs it to a demo flag.
export const FOUND = [["RULES", "Record the overrules", "S"], ["READER", "QMB windowed reader", "M"], ["SCHEMAS", "Unit spec + journal schemas", "M"], ["TRIES", "Tries counted at the QMB door", "M"], ["MARKETS", "Instrument spec v1", "M"], ["COSTS", "Published-cost calibration", "S-M"], ["MIS", "MIS labelers in QMB", "M"], ["VERBS", "Library v1: first verbs", "M-L"], ["EXITS", "Exits + scalper indicators", "M"], ["REF UNIT", "One reference unit, end to end", "M"]];
export function buildFig() {
  const W = 30, Y0 = -16, D0 = 30;
  const BENCH = { x: -160, y: -30, w: 320, d: 64, r: 6 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [140, -10, 110]], { width: 400, pad: 8, azimuth: 60 });
  const { box, cyl, hot, move, L, k, P, labelY, labelTop } = B;
  const out = [B.base(BENCH, { h: 8 })];
  const xOf = (i) => -150 + i * W;
  const hOf = (i) => 10 + i * 9;
  FOUND.forEach(([name], i) => {
    out.push(hot("f" + i, [`<g data-cls="c${i}">${box({ x: xOf(i), y: Y0, w: W - 1, d: D0, r: 1.5 }, 0, hOf(i), { tone: "mid", bevel: 0.5 })}</g>`, labelY(String(i + 1), xOf(i) + W / 2, Y0 + D0, 2.5, { px: 6, plate: false })].join("")));
  });
  // flag on top of the last step
  const fx = xOf(9) + 22, top = hOf(9);
  out.push(hot("flag", [cyl(fx, Y0 + 8, 1.2, top, 34, { tone: "mid", steps: 12 }), box({ x: fx + 1.2, y: Y0 + 7.4, w: 18, d: 1.2, r: 0.2 }, top + 22, 11, { tone: "hi", bevel: 0 }), labelY("DEMO", fx + 10.2, Y0 + 8.6, top + 25, { px: 2.8, plate: false })].join("")));
  // the reference unit token, built on the bench and lifted per step
  out.push(hot("unit", move("unit", box({ x: -7, y: Y0 + 9, w: 14, d: 12, r: 1.5 }, 0, 8, { tone: "hi", bevel: 0.4 }), [xOf(0) + W / 2, 0, hOf(0)])));
  const svg = svgOf(B, { label: "A staircase of ten foundation blocks, numbered in build order, rising to a demo flag. A small unit block climbs one step at a time.", body: out });
  const labels = Object.fromEntries(FOUND.map(([, long, cost], i) => ["f" + i, `${i + 1}. ${long} (size ${cost})`]));
  labels.flag = "Paper on the cTrader demo, with demo-fill costs.";
  labels.unit = "The reference unit: proof the whole chain works.";
  const steps = FOUND.map(([, long], i) => `{say:${JSON.stringify(`${i + 1}. ${long}`)},lit:["f${i}"],cls:{c${i}:"ok"},move:{unit:[${xOf(i) + W / 2},0,${hOf(i)}]},ms:2600}`);
  const modes = `{main:[${steps.join(",")},{say:"Reference unit on paper on the cTrader demo. The chain works.",lit:["flag","unit"],ms:3600}]}`;
  return { svg, P, labels, modes, init: { cls: {} }, ease: 0.45 };
}
