import { bench, svgOf, unitBlock, cardY, ledger } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// Four ledgers in a row, each with one writer in front. At the back, the trace: source → idea → unit → trade,
// with dashed joins from the trade into the market journal and the router log.
export function journalsFig() {
  const BENCH = { x: -152, y: -92, w: 304, d: 178, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-130, -84, 30]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];

  // the trace at the back
  const TY = -84;
  out.push(hot("trace", [box({ x: -146, y: TY - 4, w: 196, d: 24, r: 3 }, 0, 3, { tone: "lo" })].join("")));
  out.push(hot("trace", cardY(B, { x: -140, y: TY + 4, z: 3, w: 26, h: 18, text: "SOURCE", px: 3.2, lines: 3 })));
  out.push(hot("trace", cardY(B, { x: -100, y: TY + 4, z: 3, w: 26, h: 18, text: "IDEA", px: 3.2, lines: 3 })));
  out.push(hot("trace", [unitBlock(B, { x: -60, y: TY + 2, w: 28, d: 14, r: 1.5 }, 3, { h: 9 }), labelY("UNIT V2", -46, TY + 16, 4, { px: 3, plate: false })].join("")));
  out.push(hot("trace", [box({ x: -18, y: TY + 2, w: 24, d: 14, r: 2 }, 3, 6, { tone: "hi", bevel: 0.4 }), labelTop("TRADE", -6, TY + 9, 9, { px: 3.2 })].join("")));
  out.push(show("thread", B.wire([-114, TY + 8, 12], [6, TY + 9, 7], [[-108, TY + 8, 12], [-108, TY + 10, 3.4], [-62, TY + 10, 3.4], [-30, TY + 10, 3.4], [-20, TY + 9, 7]], { tone: "mid", flow: true })));

  // four ledgers
  const LX = [-144, -70, 4, 78];
  const NAMES = [["uj", "UNIT JOURNAL"], ["mj", "MARKET JOURNAL"], ["rl", "ROUTER LOG"], ["gj", "GUARD JOURNAL"]];
  // joins from the trade to the market journal and router log, drawn before the ledgers they land on
  out.push(show("joins", [B.wire([6, TY + 12, 6], [-42, -40, 12], [[12, TY + 12, 1], [12, -56, 1], [-42, -56, 1]], { tone: "lo", flow: true }), B.wire([6, TY + 6, 6], [32, -40, 12], [[20, TY + 6, 1], [20, -60, 1], [32, -60, 1]], { tone: "lo", flow: true })].join("")));
  NAMES.forEach(([id, name], i) => {
    const R = { x: LX[i], y: -44, w: 64, d: 40, r: 2.5 };
    const parts = [ledger(B, R, 0, { h: 14, text: name, px: 3.8 }), lamp(id, R.x + R.w - 6, R.y + R.d - 6, 14, { r: 2.2 })];
    if (id === "uj") ["TAKEN", "SEEN", "MISSED", "NOTES"].forEach((t, j) => parts.push(`<g data-cls="tab${j}">${box({ x: R.x + 2 + j * 15.4, y: R.y + R.d, w: 14.4, d: 5, r: 0.8 }, 1, 10, { tone: "hi", bevel: 0.2 })}</g>`, labelY(t, R.x + 9.2 + j * 15.4, R.y + R.d + 5, 4.2, { px: 2.5, plate: false })));
    out.push(hot(id, parts.join("")));
  });
  // writers in front
  const WRITERS = [["w0", "QMB + NODE"], ["w1", "FEED KEEPER"], ["w2", "ROUTER"], ["w3", "GUARDS"]];
  WRITERS.forEach(([id, name], i) => {
    const R = { x: LX[i] + 4, y: 34, w: 56, d: 30, r: 2.5 };
    out.push(hot(id, [box(R, 0, 9, { tone: "mid", bevel: 0.6 }), box({ x: R.x + 8, y: R.y + 6, w: 26, d: 12, r: 1 }, 9, 1.3, { tone: "lo" }), lamp(id, R.x + 46, R.y + 12, 9, { r: 2.4 }), labelY(name, R.x + R.w / 2, R.y + R.d, 1.4, { px: 3.8 })].join("")));
  });
  out.push(labelTop("ONE WRITER EACH · JOINED BY KEYS · NEVER COPIED", -4, 76, 0, { px: 3.6 }));
  // slips, drawn last
  WRITERS.forEach((_, i) => out.push(show("v" + i, move("s" + i, box({ x: LX[i] + 14, y: 41, w: 22, d: 10, r: 0.6 }, 10.4, 1.4, { tone: "hi", bevel: 0 })))));
  const up = () => [0, -70, 4];

  const svg = svgOf(B, { label: "Four ledgers in a row (unit journal with taken, seen, missed and notes tabs; market journal; router log; guard journal), each with its one writer in front: QMB and the node, the feed keeper, the router, the guards. At the back, a trace from source to idea to unit to trade, with dashed joins from the trade into the market journal and the router log.", body: out });
  const labels = { uj: "Unit journal: taken, seen-not-taken, missed, orders, fills, calibrations, offer outcomes, notes.", mj: "Market journal: spread, fees, swap, funding, sessions per broker, instrument and minute.", rl: "Router decision log: every offer, with its inputs and versions.", gj: "Guard journal: every block, stop and flatten, with level and reason.", w0: "QMB writes backtest and stress; the node writes paper and live.", w1: "The feed keeper's roller writes market facts once per market.", w2: "Only the router writes its log.", w3: "Each guard writes its own lines.", trace: "One id, minted at the source, carried to every trade." };
  const base = { lamps: { uj: "off", mj: "off", rl: "off", gj: "off", w0: "off", w1: "off", w2: "off", w3: "off" }, show: { thread: false, joins: false, v0: true, v1: true, v2: true, v3: true }, move: { s0: [0, 0, 0], s1: [0, 0, 0], s2: [0, 0, 0], s3: [0, 0, 0] }, cls: { tab0: "", tab1: "", tab2: "", tab3: "" } };
  const write = (i, say, extra = {}) => ({ say, lit: ["uj", "mj", "rl", "gj"].slice(i, i + 1).concat(["w" + i]), lamps: { ["w" + i]: "ok", [["uj", "mj", "rl", "gj"][i]]: "ok" }, move: { ["s" + i]: up(i) }, ms: 3000, ...extra });
  const modes = { main: [
    { say: "Four streams. Each has exactly one writer.", lit: ["uj", "mj", "rl", "gj"], ...base, ms: 2800 },
    write(0, "Unit journal: QMB writes backtest and stress; the node, paper and live."),
    { say: "It keeps trades taken, signals seen but not taken, and missed trades.", lit: ["uj"], show: { v0: false }, cls: { tab0: "ok", tab1: "warn", tab2: "bad" }, ms: 3400 },
    { say: "Agents write only notes and proposals, through a hook.", lit: ["uj"], cls: { tab0: "", tab1: "", tab2: "", tab3: "ok" }, ms: 3000 },
    write(1, "Market journal: spread, fees and sessions, written once per market.", { cls: { tab3: "" } }),
    write(2, "Router decision log: every offer with its inputs.", { show: { v1: false } }),
    write(3, "Guard journal: every block and stop, with its reason.", { show: { v2: false } }),
    { say: "One id runs from the source, through the idea and unit, to every trade.", lit: ["trace"], show: { thread: true, v3: false }, ms: 3400 },
    { say: "A trade points into the market journal and router log by key. No copies.", lit: ["trace", "mj", "rl"], show: { joins: true }, ms: 3600 },
  ] };
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.55 };
}
