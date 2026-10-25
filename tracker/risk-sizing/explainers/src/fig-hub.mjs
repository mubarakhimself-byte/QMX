import { bench, svgOf } from "./parts.mjs";

// The whole system on one bench. Every part links to its page.
export function hubFig() {
  const BENCH = { x: -152, y: -150, w: 294, d: 268, r: 10 };
  const LIB = { x: -144, y: 34, w: 52, d: 46, r: 3 };
  const QMB = { x: -128, y: -50, w: 76, d: 52, r: 3 };
  const JOUR = { x: -70, y: -104, w: 46, d: 36, r: 2 };
  const PC = { x: 26, y: -142, w: 46, d: 38, r: 3 };
  const NODE = { x: -22, y: -54, w: 156, d: 116, r: 5 };
  const MKT = { x: -60, y: 76, w: 58, d: 34, r: 3 };
  const NZ = 12;
  const pts = [[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [PC.x, PC.y, 56], [-120, 40, 40]];
  const B = bench(pts, { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, D, k, P, labelY, labelX, labelTop, lamp } = B;
  const link = (id, href, svg) => hot(id, svg, ` data-href="${href}" role="link" tabindex="0" aria-label="${id}"`);
  const out = [B.base(BENCH, { h: 8 })];
  // wires on the bench top
  const W = (a, b, via) => B.wire(a, b, via, { tone: "mid", flow: true });
  out.push(W([-92, 50, 6], [-90, -2, 6], [[-70, 50, 1], [-70, 10, 1], [-90, 10, 1]]));
  out.push(W([-80, -50, 6], [-47, -68, 4], [[-80, -60, 1], [-47, -60, 1]]));
  out.push(W([-22, -20, 6], [-24, -86, 4], [[-28, -20, 1], [-28, -86, 1]]));
  out.push(W([49, -104, 6], [-9, -48, 8], [[49, -76, 1], [-9, -76, 1]]));
  out.push(W([-2, 76, 5], [-2, 62, 6], [[-2, 70, 1]]));
  // journal binder
  out.push(link("journal", "journal.html", [box(JOUR, 0, 4, { tone: "mid" }), box(k.insetPlan(JOUR, 2), 4, 10, { tone: "hi", bevel: 0.4 }), box(JOUR, 14, 3, { tone: "mid" }), ...[0, 1, 2, 3].map((i) => box({ x: JOUR.x + 6 + i * 9, y: JOUR.y + JOUR.d - 1, w: 6, d: 4, r: 0.6 }, 6 + (i % 2) * 2, 6, { tone: "hi" })), labelTop("JOURNAL", JOUR.x + JOUR.w / 2, JOUR.y + 14, 17, { px: 7.5 })].join("")));
  // PC planner
  out.push(link("planner", "router.html", [box(PC, 0, 44, { tone: "mid", bevel: 0.8 }), L(k.planOutline(k.insetPlan(PC, 3.5), 44, P), { tone: "faint" }), box({ x: PC.x + 8, y: PC.y + 8, w: 28, d: 18, r: 1 }, 44, 2, { tone: "lo" }), move("plan", box({ x: PC.x + 10, y: PC.y + 10, w: 24, d: 14, r: 0.8 }, 46, 1.4, { tone: "hi" })), lamp("pc", PC.x + PC.w - 6, PC.y + PC.d - 6, 44, { r: 2.4 }), labelY("PC PLANNER", PC.x + PC.w / 2, PC.y + PC.d, 20, { px: 7 })].join("")));
  // QMB test bench
  const RAILY = QMB.y + 22;
  out.push(link("qmb", "testing.html", [box(QMB, 0, 22, { tone: "mid", bevel: 0.8 }), box({ x: QMB.x + 4, y: RAILY, w: QMB.w - 8, d: 6, r: 1 }, 22, 2, { tone: "lo" }), ...[QMB.x + 18, QMB.x + 40, QMB.x + 60].map((x) => [box({ x: x - 1.5, y: RAILY - 9, w: 3, d: 3, r: 0.5 }, 22, 14, { tone: "mid" }), box({ x: x - 1.5, y: RAILY + 12, w: 3, d: 3, r: 0.5 }, 22, 14, { tone: "mid" }), box({ x: x - 2, y: RAILY - 9, w: 4, d: 24, r: 0.8 }, 36, 3, { tone: "mid" })].join("")), move("cart", box({ x: QMB.x + 6, y: RAILY - 2, w: 10, d: 10, r: 1.2 }, 24, 6, { tone: "hi", bevel: 0.4 })), labelY("QMB TESTS", QMB.x + QMB.w / 2, QMB.y + QMB.d, 6, { px: 7 })].join("")));
  // library press
  out.push(link("library", "library.html", [box(LIB, 0, 30, { tone: "mid", bevel: 0.8 }), ...[0, 1, 2].map((i) => cyl(LIB.x + 12 + i * 14, LIB.y + 18, 4, 30, 3, { tone: "hi" })), box({ x: LIB.x + 8, y: LIB.y + 30, w: 36, d: 8, r: 1 }, 30, 2, { tone: "lo" }), labelY("LIBRARY", LIB.x + LIB.w / 2, LIB.y + LIB.d, 9, { px: 7 })].join("")));
  // markets socket board
  out.push(link("markets", "instruments.html", [box(MKT, 0, 10, { tone: "mid", bevel: 0.6 }), ...[0, 1, 2, 3].map((i) => [cyl(MKT.x + 10 + i * 13, MKT.y + 12, 4.4, 10, 1, { tone: "lo" }), L(k.ring(MKT.x + 10 + i * 13, MKT.y + 12, 2, 11, P, 14), { tone: "mid" })].join("")), labelTop("MARKETS", MKT.x + MKT.w / 2, MKT.y + 26, 10, { px: 7 })].join("")));
  // node plinth
  out.push(link("node", "router.html", [box(NODE, 0, NZ, { tone: "mid", bevel: 1, steps: 6 }), L(k.planOutline(k.insetPlan(NODE, 3.5), NZ, P, 6), { tone: "faint" }), labelY("NODE · PAPER + LIVE", NODE.x + 62, NODE.y + NODE.d, 1.5, { px: 6.5 })].join("")));
  // router gate on node (back edge)
  const GATE = { x: -14, y: -46, w: 10, d: 96, r: 1.5 };
  out.push(link("gate", "router.html", [box(GATE, NZ, 18, { tone: "mid", bevel: 0.6 }), ...[0, 1, 2].map((i) => lamp("g" + i, GATE.x + 5, -28 + i * 30, NZ + 18, { r: 2.4 })), labelTop("GATE", GATE.x + 5, 56, NZ, { px: 6 })].join("")));
  // pod tray with three units
  const TRAY = { x: 6, y: -46, w: 64, d: 92, r: 3 };
  out.push(link("pod", "unit.html", [box(TRAY, NZ, 4, { tone: "mid" }), labelTop("POD", 38, 54, NZ, { px: 6 })].join("")));
  for (let i = 0; i < 3; i++) {
    const U = { x: 12, y: -40 + i * 28, w: 52, d: 22, r: 2 };
    out.push(link("unit" + i, "unit.html", [box(U, NZ + 4, 16, { tone: "hi", bevel: 0.6 }), cyl(U.x + 38, U.y + 11, 5, NZ + 20, 2, { tone: "mid" }), cyl(U.x + 14, U.y + 11, 3.4, NZ + 20, 3, { tone: "mid" })].join("")));
  }
  // size gauge (sizing page)
  out.push(link("size", "sizing.html", [box({ x: 84, y: 4, w: 16, d: 16, r: 1.5 }, NZ, 4, { tone: "lo" }), box({ x: 86, y: 9, w: 12, d: 4, r: 0.6 }, NZ + 4, 30, { tone: "mid" }), move("sizeCar", box({ x: 85, y: 7, w: 14, d: 8, r: 1 }, NZ + 22, 5, { tone: "hi" })), labelTop("SIZE", 92, 28, NZ, { px: 6 })].join("")));
  // guard
  const GD = { x: 84, y: -48, w: 38, d: 38, r: 2.5 };
  out.push(link("guard", "unit.html", [box(GD, NZ, 26, { tone: "mid", bevel: 0.6 }), `<g data-cls="kill">${cyl(103, -29, 7.5, NZ + 26, 3, { tone: "hi", bevel: 0.4 })}</g>`, labelY("GUARD", 103, GD.y + GD.d, NZ + 6, { px: 6 })].join("")));
  // nightly check tower
  out.push(link("decay", "decay.html", [cyl(116, 38, 9, NZ, 3, { tone: "lo" }), cyl(116, 38, 6, NZ + 3, 30, { tone: "mid" }), lamp("ok", 116, 38, NZ + 33, { r: 4.4 }), labelTop("NIGHTLY", 116, 54, NZ, { px: 5.5 })].join("")));
  const svg = svgOf(B, { label: "The QMX unit system on one bench: the library builds units, QMB tests them, the journal records them, the PC planner writes a plan, and the node runs units in pods behind a router gate, an account guard, a size gauge and a nightly check. Each part links to its page.", body: out });
  const labels = {
    library: "Library: agents build units here → page", qmb: "QMB: backtest and stress → page", journal: "Journal: one per unit → page", planner: "PC planner: writes the placement plan → page",
    node: "Node: runs paper and live near the broker → page", gate: "Router gate: cheap checks each bar → page", pod: "Pod: units sharing one budget → page", unit0: "A unit → page", unit1: "A unit → page", unit2: "A unit → page",
    guard: "Account guard: stops, never resizes → page", size: "Risk and sizing → page", decay: "Nightly decay check → page", markets: "Markets and backend gaps → page",
  };
  const modes = `{main:[
 {say:"The library builds a unit from a spec and two hooks.",lit:["library"],lamps:{pc:"ok",g0:"ok",g1:"ok",g2:"ok",ok:"ok"},ms:2800},
 {say:"QMB backtests and stress-tests it. Every run counts as a try.",lit:["qmb"],move:{cart:[48,0,0]},ms:3000},
 {say:"Results go into the unit's one journal.",lit:["journal"],move:{cart:[0,0,0]},ms:2600},
 {say:"The PC planner turns proof into a placement plan.",lit:["planner"],move:{plan:[0,0,3]},ms:2800},
 {say:"The plan goes to the node. It keeps working if the PC is off.",lit:["node","planner"],move:{plan:[0,0,0]},ms:3000},
 {say:"The router gate checks cheap facts every bar.",lit:["gate"],lamps:{g1:"bad"},ms:2800},
 {say:"Units trade their own way, inside a pod's budget.",lit:["unit0","unit1","unit2","pod"],lamps:{g1:"ok"},ms:2800},
 {say:"Each unit sizes itself, never above your ceiling.",lit:["size"],move:{sizeCar:[0,0,-8]},ms:2800},
 {say:"The account guard can stop everything.",lit:["guard"],cls:{kill:"bad"},move:{sizeCar:[0,0,0]},ms:2600},
 {say:"Each night a check reads every journal: OK, Watch or Alarm.",lit:["decay"],cls:{kill:""},lamps:{ok:"warn"},ms:2800},
 {say:"Markets differ. The backend still lacks several pieces.",lit:["markets"],lamps:{ok:"ok"},ms:2800}
]}`;
  return { svg, P, labels, modes };
}
