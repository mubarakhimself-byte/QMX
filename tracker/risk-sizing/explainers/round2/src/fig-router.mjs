import { bench, svgOf, unitBlock, cardY, ledger, reset } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// Market traffic on the left, the router's offer board in the middle, four units on the right,
// the decision log and the correlation ledger in front. Offer cards fly from the board to a unit.
export function routerFig() {
  const BENCH = { x: -150, y: -78, w: 300, d: 160, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-44, -40, 56]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, lamp, dial, show } = B;
  const out = [B.base(BENCH, { h: 8 })];

  // units plinth and units (back-right; drawn first, they sit behind the board on screen)
  const UP = { x: 18, y: -72, w: 94, d: 104, r: 4 };
  out.push(hot("units", [box(UP, 0, 5, { tone: "mid", bevel: 0.7 }), L(k.planOutline(k.insetPlan(UP, 4), 5, P), { tone: "faint" })].join("")));
  const UY = [-66, -40, -14, 10];
  UY.forEach((y, i) => {
    out.push(hot("u" + i, [unitBlock(B, { x: 34, y, w: 50, d: 18, r: 2 }, 5, { h: 12, cls: "u" + i }), lamp("u" + i, 94, y + 9, 5, { r: 2.6 }), labelX("U" + (i + 1), 84, y + 9, 8, { px: 4.2 })].join("")));
  });

  // opportunities tray (left)
  const O = { x: -144, y: -62, w: 54, d: 96, r: 3 };
  out.push(hot("opps", [box(O, 0, 6, { tone: "mid", bevel: 0.6 }), labelY("MARKET TRAFFIC", O.x + O.w / 2, O.y + O.d, 1, { px: 3.8 })].join("")));
  [["EURUSD", "LONDON", -54], ["GBPUSD", "LONDON", -24], ["XAUUSD", "NEW YORK", 6]].forEach(([a, b, y], i) => {
    out.push(hot("opps", [box({ x: -138, y, w: 42, d: 22, r: 1.5 }, 6, 5, { tone: "hi", bevel: 0.4 }), labelTop(a, -117, y + 8, 11, { px: 3.8 }), labelTop(b, -117, y + 15, 11, { px: 3 })].join("")));
  });
  out.push(B.wire([-90, -14, 6], [-70, -14, 8], [[-80, -14, 1]], { tone: "mid", flow: true }));

  // the router board
  const R = { x: -70, y: -56, w: 50, d: 76, r: 3 };
  const EXP = dial("exp", -45, 2, 11, 30, { h: 3, value: 0, ticks: 20, every: 5 });
  out.push(hot("board", [box(R, 0, 30, { tone: "mid", bevel: 0.8, steps: 5 }), L(k.planOutline(k.insetPlan(R, 3.5), 30, P, 5), { tone: "faint" }),
    ...[-48, -38, -28].map((y) => box({ x: -64, y, w: 38, d: 6, r: 1 }, 30, 1.2, { tone: "lo" })), lamp("router", -30, -15, 30, { r: 2.8 }), labelY("ROUTER", -45, R.y + R.d, 9, { px: 5 })].join("")));
  out.push(hot("expiry", [EXP.svg, labelTop("EXPIRES", -45, 17, 30, { px: 3 })].join("")));
  out.push(B.wire([-20, -20, 16], [34, -20, 10], [[0, -20, 1], [18, -20, 6]], { tone: "faint" }));

  // decision log and correlation ledger (front)
  out.push(hot("log", ledger(B, { x: -70, y: 38, w: 50, d: 32, r: 2 }, 0, { h: 12, text: "DECISION LOG", px: 3.8 })));
  const CL = { x: 18, y: 42, w: 60, d: 30, r: 2 };
  out.push(hot("corr", [box(CL, 0, 10, { tone: "mid", bevel: 0.6 }), box({ x: 22, y: 45, w: 34, d: 24, r: 1 }, 10, 0.8, { tone: "lo", crease: "none" }), L([1, 2, 3].map((i) => k.lineOnTop([22 + i * 8.5, 45], [22 + i * 8.5, 69], 10.85, P)).join("") + [1, 2].map((i) => k.lineOnTop([22, 45 + i * 8], [56, 45 + i * 8], 10.85, P)).join(""), { tone: "mid" }), lamp("corr", 68, 57, 10, { r: 2.4 }), labelY("CORRELATION", 48, 72, 2, { px: 3.8 })].join("")));
  out.push(B.wire([18, 56, 6], [12, 26, 6], [[12, 56, 1]], { tone: "faint" }));

  // offer card, drawn last
  const C0 = { x: -60, y: -40, z: 31.2 };
  out.push(show("card", hot("card", move("card", cardY(B, { x: C0.x, y: C0.y, z: C0.z, w: 20, h: 12, text: "OFFER", px: 3, lines: 2 })))));
  const to = (i) => [59 - (C0.x + 10), UY[i] + 9 - C0.y, 17.2 - C0.z];

  const svg = svgOf(B, { label: "Market traffic on the left (EURUSD London, GBPUSD London, gold New York) feeds a router board with an expiry dial. Four units stand on the right. A decision log and a correlation ledger sit in front. Offer cards fly from the board to one unit; the router has no switch.", body: out });
  const labels = { opps: "Traffic: an instrument in a session window, at a broker.", board: "The router ranks opportunities and publishes offers.", expiry: "Every offer expires. After that it means nothing.", units: "Units pull offers. Nothing waits on the router.", u0: "Unit 1", u1: "Unit 2", u2: "Unit 3", u3: "Unit 4", card: "An offer: unit, market, why, grade, policy, expiry.", log: "Decision log: every offer with its inputs. Units log taken or ignored.", corr: "Correlation ledger: units' P&L and signals, instruments, long/short consensus." };
  const ids = ["u0", "u1", "u2", "u3"];
  const base = { lamps: { router: "ok", corr: "off", ...reset(ids, "off") }, dial: { exp: 0 }, move: { card: [0, 0, 0] }, show: { card: true }, cls: reset(ids, "") };
  const go = (i, extra = {}) => ({ move: { card: to(i) }, dial: { exp: 0.1 }, lamps: { ...reset(ids, "off"), [ids[i]]: "ok" }, ...extra });
  const back = { move: { card: [0, 0, 0] }, dial: { exp: 0 }, show: { card: true } };
  const modes = {
    offers: [
      { say: "Traffic: each opportunity is an instrument in a session window.", lit: ["opps"], ...back, ms: 2800 },
      { say: "The router ranks it and publishes an offer. It has no switch.", lit: ["board", "card"], ms: 3000 },
      { say: "Units pull offers. Unit 2 takes this one.", lit: ["u1", "card"], ...go(1), ms: 3000 },
      { say: "The offer ages. At its expiry it means nothing.", lit: ["expiry"], dial: { exp: 1 }, ms: 3200 },
      { say: "Gone. Unit 2 keeps trading on its own conditions.", lit: ["u1"], show: { card: false }, ms: 2600 },
      { say: "Each offer and its inputs go in the decision log.", lit: ["log"], ms: 2800 },
      { say: "The correlation ledger keeps look-alike units off one market.", lit: ["corr"], lamps: { corr: "ok" }, ms: 3000 },
    ],
    p2: [
      { say: "Power of two: pick two eligible units at random.", lit: ["u0", "u2"], ...back, lamps: { corr: "ok", ...reset(ids, "off") }, cls: { ...reset(ids, ""), u0: "warn", u2: "ok" }, ms: 3200 },
      { say: "Unit 1 moves with trades already open. Unit 3 doesn't.", lit: ["corr", "u0", "u2"], ms: 3200 },
      { say: "The offer goes to the less correlated one: Unit 3.", lit: ["u2", "card"], ...go(2), ms: 3200 },
      { say: "Cheap, and it stops units piling onto one bet.", lit: ["u2"], ms: 2600 },
    ],
    cost: [
      { say: "Least cost: like 'fastest server', but cheapest market now.", lit: ["opps"], ...back, cls: reset(ids, ""), ms: 3000 },
      { say: "From the market journal: spread against target, by broker and hour.", lit: ["log", "opps"], ms: 3200 },
      { say: "London GBPUSD is cheapest now: the offer goes to its unit.", lit: ["u3", "card"], ...go(3), ms: 3200 },
    ],
    affinity: [
      { say: "Affinity: a unit keeps its known markets.", lit: ["u0"], ...back, cls: reset(ids, ""), ms: 2800 },
      { say: "Same market, same unit, every time.", lit: ["u0", "card"], ...go(0), ms: 3000 },
      { say: "With several nodes, the same rule shards instruments to nodes.", lit: ["units"], ms: 3200 },
    ],
    rr: [
      { say: "Round robin: each unit in turn. Weak for live; useful for paper evidence.", lit: ["units"], ...back, cls: reset(ids, ""), ms: 3000 },
      { say: "Unit 1", lit: ["u0"], ...go(0), ms: 1600 }, { say: "Unit 2", lit: ["u1"], ...go(1), ms: 1600 }, { say: "Unit 3", lit: ["u2"], ...go(2), ms: 1600 }, { say: "Unit 4", lit: ["u3"], ...go(3), ms: 1600 },
    ],
    down: [
      { say: "All units trading their admitted markets.", lit: ["units"], ...back, show: { card: false }, lamps: { router: "ok", ...reset(ids, "ok") }, cls: reset(ids, ""), ms: 2600 },
      { say: "The router goes down.", lit: ["board"], lamps: { router: "off" }, ms: 2400 },
      { say: "No new offers. Old ones run out. Units keep trading.", lit: ["units", "expiry"], dial: { exp: 1 }, ms: 3200 },
      { say: "Its missing heartbeat is a yellow light, not a stop.", lit: ["board"], lamps: { router: "warn" }, ms: 3000 },
      { say: "Back up: it reads the feed and publishes fresh offers.", lit: ["board", "card"], lamps: { router: "ok" }, show: { card: true }, dial: { exp: 0 }, ms: 3000 },
    ],
  };
  return { svg, P, labels, init: base, dials: { exp: EXP.spec }, modes: modesOf(modes), ease: 0.5 };
}
