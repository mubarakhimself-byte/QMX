import { bench, svgOf } from "./parts.mjs";

// A tabbed ledger. QMB slides slips into the backtest and stress tabs, the node into paper and live. Readers sit behind it.
export function journalFig() {
  const BENCH = { x: -112, y: -92, w: 224, d: 180, r: 8 };
  const BOOK = { x: -78, y: -40, w: 156, d: 66, r: 3 };
  const TABS = [["BACKTEST", "qmb"], ["STRESS", "qmb"], ["PAPER", "node"], ["LIVE", "node"], ["EVENTS", "both"], ["NOTES", "both"]];
  const TX = (i) => BOOK.x + 3 + i * 25.2;
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [50, -30, 44], [-60, -84, 24]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, D, k, P, labelY, labelTop, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  // readers at the back
  const READERS = [["REGISTRY", -76], ["ROUTER", -26], ["YOUR PAGE", 24], ["CALIBRATOR", 74]];
  for (const [name, x] of READERS) {
    out.push(B.wire([x, -64, 6], [x, -40, 10], [[x, -52, 1], [x, -40, 1]], { tone: "faint" }));
    out.push(hot("readers", [box({ x: x - 22, y: -86, w: 44, d: 22, r: 2 }, 0, 18, { tone: "mid", bevel: 0.5 }), labelY(name, x, -64, 4, { px: 4.3 })].join("")));
  }
  // the book
  out.push(hot("book", [box(BOOK, 0, 3, { tone: "lo" }), box(k.insetPlan(BOOK, 1.5), 3, 12, { tone: "hi", bevel: 0.3 }), L([6, 9, 12].map((z) => k.sideSeam(k.insetPlan(BOOK, 1.5), z, P, 4)).join(""), { tone: "faint" }), box(BOOK, 15, 3, { tone: "mid", bevel: 0.6 })].join("")));
  out.push(hot("front", [box({ x: -70, y: -34, w: 88, d: 40, r: 1.5 }, 18, 0.8, { tone: "lo", crease: "none" }), labelTop("FRONT PAGE", -26, -8, 18.8, { px: 6.5 }), L([0, 1, 2].map((i) => k.lineOnTop([-62, -28 + i * 5], [-62 + 50 - i * 12, -28 + i * 5], 18.85, P)).join(""), { tone: "lo", free: true })].join("")));
  out.push(hot("exam", [box({ x: 34, y: -30, w: 36, d: 8, r: 1 }, 18, 3, { tone: "mid" }), box({ x: 36, y: -27.5, w: 32, d: 1.6, r: 0.3 }, 21, 22, { tone: "hi", bevel: 0 }), labelY("EXAM", 52, -25.9, 33, { px: 5, plate: false }), L([0, 1].map((i) => k.segment([40, -25.85, 28 - i * 3], [64 - i * 6, -25.85, 28 - i * 3], P)).join(""), { tone: "lo", free: true })].join("")));
  TABS.forEach(([name, who], i) => {
    const x = TX(i);
    out.push(hot("tab-" + who, [`<g data-cls="tab${i}">${box({ x, y: BOOK.y + BOOK.d, w: 24, d: 7, r: 1 }, 3, 13, { tone: "hi", bevel: 0.3 })}</g>`, labelY(name, x + 12, BOOK.y + BOOK.d + 7, 7, { px: 3.7, plate: false })].join("")));
  });
  // writers in front
  const WQ = { x: -100, y: 52, w: 80, d: 30, r: 3 };
  const WN = { x: 20, y: 52, w: 80, d: 30, r: 3 };
  out.push(hot("qmb", [box(WQ, 0, 9, { tone: "mid", bevel: 0.7 }), box({ x: WQ.x + 10, y: WQ.y + 6, w: 30, d: 12, r: 1 }, 9, 1.5, { tone: "lo" }), lamp("qw", WQ.x + 66, WQ.y + 12, 9), labelY("QMB WRITES", WQ.x + WQ.w / 2, WQ.y + WQ.d, 1.2, { px: 4.6 })].join("")));
  out.push(hot("node", [box(WN, 0, 9, { tone: "mid", bevel: 0.7 }), box({ x: WN.x + 10, y: WN.y + 6, w: 30, d: 12, r: 1 }, 9, 1.5, { tone: "lo" }), lamp("nw", WN.x + 66, WN.y + 12, 9), labelY("NODE WRITES", WN.x + WN.w / 2, WN.y + WN.d, 1.2, { px: 4.6 })].join("")));
  // slips: built at the writer's tray, moved to their tab
  const slip = (id, x0) => move(id, box({ x: x0, y: WQ.y + 7, w: 20, d: 10, r: 0.5 }, 10.5, 1.4, { tone: "hi", bevel: 0 }));
  out.push(slip("s0", WQ.x + 15), slip("s1", WN.x + 15));
  const svg = svgOf(B, { label: "A ledger with six tabs: backtest, stress, paper, live, events and notes. QMB's writer slides slips into backtest and stress; the node's writer into paper and live. The front page and the exam card sit on the cover. Four readers behind it read the same book.", body: out });
  const to = (slipX0, i) => [TX(i) + 2 - slipX0, BOOK.y + BOOK.d + 1 - (WQ.y + 7), 6];
  const labels = { book: "One journal per unit, from creation to retirement.", front: "Front page: computed. Best markets, risk now, tries, stage.", exam: "Exam baseline: frozen from stress. Live is judged on it.", "tab-qmb": "Backtest and stress: written by QMB only.", "tab-node": "Paper and live: written by the node only.", "tab-both": "Events (promotions, calibrations, pauses) and notes.", qmb: "QMB writes only backtest and stress.", node: "The node writes only paper and live.", readers: "Readers. None keeps a copy." };
  const modes = `{main:[
 {say:"One journal per unit, from creation to retirement.",lit:["book"],ms:2600},
 {say:"QMB writes the backtest tab. Nobody else can.",lit:["qmb","tab-qmb"],lamps:{qw:"ok"},cls:{tab0:"ok"},move:{s0:${JSON.stringify(to(WQ.x + 15, 0))}},ms:3000},
 {say:"…and the stress tab. Stress results freeze the exam baseline.",lit:["qmb","exam"],cls:{tab0:"",tab1:"ok"},move:{s0:${JSON.stringify(to(WQ.x + 15, 1))}},ms:3000},
 {say:"The node writes paper trades. QMB never touches them.",lit:["node","tab-node"],lamps:{qw:"off",nw:"ok"},cls:{tab1:"",tab2:"ok"},move:{s0:[0,0,0],s1:${JSON.stringify(to(WN.x + 15, 2))}},ms:3000},
 {say:"…and live trades. Same journal, a different writer.",lit:["node","tab-node"],cls:{tab2:"",tab3:"ok"},move:{s1:${JSON.stringify(to(WN.x + 15, 3))}},ms:3000},
 {say:"Events: promotions, calibrations, pauses, each with a reason.",lit:["tab-both"],lamps:{nw:"off"},cls:{tab3:"",tab4:"ok"},move:{s1:[0,0,0]},ms:2800},
 {say:"The front page is computed from the tabs. Never typed.",lit:["front"],cls:{tab4:""},ms:2800},
 {say:"Registry, router, your page and the calibrator all read it.",lit:["readers"],ms:3000}
]}`;
  return { svg, P, labels, modes, ease: 0.5 };
}
