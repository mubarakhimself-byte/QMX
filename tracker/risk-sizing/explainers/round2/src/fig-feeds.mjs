import { bench, svgOf, unitBlock, ledger, reset } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// One broker cable into a feed keeper; a local bus rail fans out to a grid of units, the guards and the router;
// the recorder and the market journal sit in front of the keeper.
export function poolFig() {
  const BENCH = { x: -152, y: -80, w: 304, d: 162, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-134, -60, 70]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  // broker tower with mast
  const BR = { x: -146, y: -74, w: 26, d: 26, r: 2 };
  out.push(hot("broker", [box(BR, 0, 48, { tone: "lo", bevel: 0.6 }), L([12, 24, 36].map((z) => k.sideSeam(BR, z, P, 4)).join(""), { tone: "faint" }), cyl(-133, -61, 1.6, 48, 18, { tone: "mid", steps: 12 }), cyl(-133, -61, 3.2, 66, 1.4, { tone: "mid", steps: 16 }), labelX("BROKER", BR.x + BR.w, BR.y + BR.d / 2, 18, { px: 4 })].join("")));
  // keeper
  const K = { x: -110, y: -74, w: 44, d: 34, r: 2.5 };
  out.push(B.wire([-120, -58, 34], [-110, -58, 20], [[-115, -58, 30]], { tone: "mid", flow: true }));
  out.push(hot("keeper", [box(K, 0, 26, { tone: "mid", bevel: 0.8 }), L(k.planOutline(k.insetPlan(K, 3), 26, P), { tone: "faint" }), box({ x: K.x + 6, y: K.y + 6, w: 22, d: 12, r: 1 }, 26, 1.2, { tone: "lo" }), lamp("keeper", K.x + 36, K.y + 24, 26, { r: 2.8 }), labelY("FEED KEEPER", K.x + K.w / 2, K.y + K.d, 9, { px: 4.4 })].join("")));
  // bus rail
  const BUS = { x: -66, y: -62, w: 206, d: 8, r: 1.5 };
  const COLS = [-50, -20, 10, 40, 70];
  out.push(hot("bus", [box(BUS, 0, 6, { tone: "lo", bevel: 0.4 }), L(k.lineOnTop([BUS.x + 3, BUS.y + 4], [BUS.x + BUS.w - 3, BUS.y + 4], 6, P), { tone: "mid" }), ...[...COLS, 118].map((x) => box({ x: x - 3, y: BUS.y - 1, w: 6, d: 10, r: 0.8 }, 6, 2, { tone: "mid" })), labelTop("LOCAL BUS", -40, -68, 0, { px: 3.6 })].join("")));
  // pulse on the bus
  out.push(show("pulse", move("pulse", box({ x: -64, y: -61, w: 6, d: 6, r: 1.5 }, 8, 3, { tone: "hi", bevel: 0.3 }))));
  // unit grid
  const ROWS = [-46, -22, 2];
  const grid = [];
  for (const y of ROWS) for (const x of COLS) grid.push(unitBlock(B, { x: x - 11, y, w: 22, d: 16, r: 1.5 }, 0, { h: 8 }));
  out.push(...COLS.map((x) => B.wire([x, -54, 8], [x, -46, 6], [[x, -50, 8]], { tone: "faint", ends: "to" })));
  out.push(hot("units", `<g data-cls="ug">${grid.join("")}</g>`));
  out.push(labelTop("200+ UNITS · ONE SUBSCRIPTION PER SYMBOL", 10, 28, 0, { px: 3.8 }));
  // readers on the right: guards and router
  out.push(B.wire([118, -54, 8], [118, -40, 10], [[118, -48, 8]], { tone: "faint", ends: "to" }));
  out.push(hot("guards", [box({ x: 100, y: -40, w: 40, d: 28, r: 2 }, 0, 18, { tone: "mid", bevel: 0.6 }), `<g data-cls="gb">${cyl(114, -26, 5.5, 18, 3, { tone: "hi", bevel: 0.4 })}</g>`, lamp("guards", 130, -26, 18, { r: 2.4 }), labelY("GUARDS", 120, -12, 6, { px: 4 })].join("")));
  out.push(B.wire([140, -26, 10], [140, 4, 8], [[146, -26, 1], [146, 4, 1]], { tone: "faint" }));
  out.push(hot("router", [box({ x: 100, y: -2, w: 40, d: 28, r: 2 }, 0, 14, { tone: "mid", bevel: 0.6 }), lamp("router", 130, 12, 14, { r: 2.4 }), labelY("ROUTER", 120, 26, 4, { px: 4 }), labelTop("A READER", 112, 12, 14, { px: 2.8 })].join("")));
  // recorder + market journal in front of the keeper
  out.push(B.wire([-100, -40, 8], [-112, -14, 16], [[-100, -30, 1], [-112, -30, 1]], { tone: "mid" }));
  out.push(hot("recorder", [...[0, 1, 2].map((i) => cyl(-120, -2, 13, i * 7, 6, { tone: i === 2 ? "hi" : "mid", bevel: 0.4 })), L(k.ring(-120, -2, 4, 21, P, 20), { tone: "lo" }), labelY("RECORDER", -120, 11, 1, { px: 3.8 })].join("")));
  out.push(B.wire([-84, -40, 8], [-90, 30, 10], [[-84, 30, 1]], { tone: "mid" }));
  out.push(hot("mj", [ledger(B, { x: -142, y: 30, w: 52, d: 32, r: 2 }, 0, { h: 12, text: "MARKET JOURNAL", px: 3.6 })].join("")));

  const svg = svgOf(B, { label: "A broker tower cabled to one feed keeper. A local bus rail runs from the keeper past a grid of fifteen units standing for 200 or more, to the guards and the router at the right end. A recorder (a stack of disks) and the market journal sit in front of the keeper.", body: out });
  const labels = { broker: "One connection per broker account type.", keeper: "Feed keeper: owns the socket, sign-in, reconnects, gap repair.", bus: "Local bus on this machine. Sequence numbers catch drops.", units: "Every unit reads the bus. One subscription per symbol, not per unit.", guards: "Guards read the bus directly.", router: "The router reads it like any unit. It owns nothing here.", recorder: "Recorder: our own price history, in the store QMB reads.", mj: "Market journal: spread, fees, swap, sessions per minute.", pulse: "A price, fanned out." };
  const base = { lamps: { keeper: "off", guards: "off", router: "off" }, move: { pulse: [0, 0, 0] }, show: { pulse: false }, cls: { ug: "", gb: "" } };
  const modes = { main: [
    { say: "One connection to the broker.", lit: ["broker"], lamps: { keeper: "ok", guards: "ok", router: "ok" }, move: { pulse: [0, 0, 0] }, show: { pulse: false }, cls: { ug: "", gb: "" }, ms: 2600 },
    { say: "One subscription per symbol: 200 units on 60 symbols = 60 subscriptions.", lit: ["keeper"], ms: 3400 },
    { say: "The keeper fans each price out on a local bus.", lit: ["bus", "pulse"], show: { pulse: true }, move: { pulse: [196, 0, 0] }, ms: 3000 },
    { say: "Every unit on this machine reads it.", lit: ["units"], show: { pulse: false }, cls: { ug: "ok" }, ms: 2600 },
    { say: "Guards read the same bus. Not through the router.", lit: ["guards"], move: { pulse: [0, 0, 0] }, ms: 2800 },
    { say: "The router is a reader like any unit. It owns nothing here.", lit: ["router"], ms: 3000 },
    { say: "The recorder writes our own price history.", lit: ["recorder"], ms: 2800 },
    { say: "The market journal gets spread, fees and sessions per minute.", lit: ["mj"], ms: 3000 },
    { say: "Router stops: nothing changes in the feed.", lit: ["router", "units"], lamps: { router: "off" }, ms: 3000 },
    { say: "Keeper stops: its symbols go stale. No new entries; open trades keep broker stops.", lit: ["keeper", "units"], lamps: { keeper: "bad", router: "ok" }, cls: { ug: "warn" }, ms: 3800 },
    { say: "Keeper restarts: units carry on from the last-value cache.", lit: ["keeper", "units"], lamps: { keeper: "ok" }, cls: { ug: "ok" }, ms: 3000 },
  ] };
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.7 };
}

// PC and node taking turns on the one live cTrader connection: a lease tag sits on whoever holds it.
export function leaseFig() {
  const BENCH = { x: -118, y: -60, w: 236, d: 112, r: 8 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [0, -54, 40], [-108, -10, 36], [-62, -10, 36], [108, 34, 28]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  // cTrader box with two ports
  const CT = { x: -24, y: -54, w: 48, d: 30, r: 2.5 };
  out.push(hot("ctrader", [box(CT, 0, 36, { tone: "mid", bevel: 0.8 }), L(k.planOutline(k.insetPlan(CT, 3), 36, P), { tone: "faint" }), labelY("CTRADER", 0, CT.y + CT.d, 22, { px: 4.6 }), labelY("LIVE", -10, CT.y + CT.d, 6, { px: 3.2 }), labelY("DEMO", 10, CT.y + CT.d, 6, { px: 3.2 })].join("")));
  // cables
  out.push(show("liveN", B.wire([-10, -24, 4], [62, 0, 12], [[-10, -16, 1], [50, -16, 1], [50, 0, 1]], { tone: "mid", flow: true })));
  out.push(show("liveP", B.wire([-10, -24, 4], [-62, 0, 12], [[-10, -12, 1], [-50, -12, 1], [-50, 0, 1]], { tone: "mid", flow: true })));
  out.push(show("demoP", B.wire([10, -24, 4], [-62, 12, 12], [[10, -6, 1], [-48, -6, 1], [-48, 12, 1]], { tone: "faint", flow: true })));
  out.push(show("pool", B.wire([62, 24, 12], [-62, 24, 12], [[50, 34, 1], [-50, 34, 1]], { tone: "faint", flow: true })));
  // PC and node
  const PC = { x: -108, y: -10, w: 46, d: 44, r: 3 };
  out.push(hot("pc", [box(PC, 0, 32, { tone: "mid", bevel: 0.8 }), box({ x: PC.x + 7, y: PC.y + 7, w: 26, d: 18, r: 1 }, 32, 1.4, { tone: "lo" }), lamp("pc", PC.x + 38, PC.y + 34, 32, { r: 2.6 }), labelY("PC · HOME", PC.x + PC.w / 2, PC.y + PC.d, 10, { px: 4.4 })].join("")));
  const ND = { x: 62, y: -10, w: 46, d: 44, r: 3 };
  out.push(hot("node", [box(ND, 0, 24, { tone: "mid", bevel: 0.8 }), L([8, 16].map((z) => k.sideSeam(ND, z, P, 4)).join(""), { tone: "faint" }), lamp("node", ND.x + 38, ND.y + 34, 24, { r: 2.6 }), labelY("NODE", ND.x + ND.w / 2, ND.y + ND.d, 6, { px: 4.4 })].join("")));
  // lease tag, built on the node
  const tag = [box({ x: 76, y: 2, w: 18, d: 12, r: 2 }, 24, 3, { tone: "hi", bevel: 0.4 }), L(k.ring(80.5, 8, 1.6, 27, P, 12), { tone: "mid" }), labelTop("LEASE", 87, 8, 27, { px: 2.8 })].join("");
  out.push(hot("lease", move("lease", tag, [0, 0, 0])));
  const toPC = [-170, 0, 8];
  const svg = svgOf(B, { label: "A cTrader box with a live and a demo port, the PC on the left and the node on the right. A lease tag sits on whichever machine holds the one live connection; cables show who is connected and the PC reading the node's pool.", body: out });
  const labels = { ctrader: "cTrader advises one live and one demo connection per app.", pc: "The PC: home. Research and paper can use the demo port.", node: "The node: trades when the laptop is closed.", lease: "Lease: one holder of the live connection at a time." };
  const base = { lamps: { pc: "ok", node: "ok" }, move: { lease: [0, 0, 0] }, show: { liveN: true, liveP: false, demoP: false, pool: false } };
  const modes = { main: [
    { say: "The node holds the live connection, and the lease.", lit: ["node", "lease"], lamps: { pc: "ok", node: "ok" }, move: { lease: [0, 0, 0] }, show: { liveN: true, liveP: false, demoP: false, pool: false }, ms: 3000 },
    { say: "The PC reads the node's pool for live prices.", lit: ["pc"], show: { pool: true }, ms: 2800 },
    { say: "Research on the PC can use the demo connection.", lit: ["pc", "ctrader"], show: { demoP: true }, ms: 3000 },
    { say: "The node goes down.", lit: ["node"], lamps: { node: "bad" }, show: { liveN: false, pool: false }, ms: 2600 },
    { say: "Your click, or a timeout you set, moves the lease to the PC.", lit: ["lease", "pc"], move: { lease: toPC }, show: { liveP: true }, ms: 3400 },
    { say: "The real risk: two machines refreshing one sign-in log each other out.", lit: ["lease"], ms: 3400 },
  ] };
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.6 };
}
