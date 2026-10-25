import { bench, svgOf } from "./parts.mjs";

// The QMB test line: a carriage runs past a tries counter and five test stations, then a baseline card crosses to the node bench.
export function testingFig() {
  const QB = { x: -204, y: -36, w: 336, d: 74, r: 6 };
  const LB = { x: 146, y: -30, w: 58, d: 62, r: 5 };
  const ST = [["tries", "TRIES", -178], ["cost", "COST ×2", -124], ["sealed", "SEALED", -70], ["plateau", "PLATEAU", -16], ["family", "FAMILY", 38], ["mc", "SIZE CONE", 92]];
  const B = bench([[QB.x, QB.y, -12], [LB.x + LB.w, LB.y + LB.d, -12], [QB.x, QB.y + QB.d, -12], [LB.x + LB.w, LB.y, -12], [-124, -20, 56], [160, -20, 40]], { width: 400, pad: 8, azimuth: 60 });
  const { box, cyl, hot, move, L, D, k, P, labelY, labelTop, liveY, lamp, show } = B;
  const out = [B.base(QB, { h: 8 }), B.base(LB, { h: 8 })];
  out.push(box({ x: QB.x + 6, y: 12, w: QB.w - 12, d: 6, r: 1 }, 0, 3, { tone: "lo" }));
  // R ruler along the rail (proposed only)
  const ticks = k.topTicks(QB.x + 10, QB.x + QB.w - 10, 6, 5, 21, 0.6, [1.6, 3], P);
  out.push(show("ruler", [box({ x: QB.x + 6, y: 20.5, w: QB.w - 12, d: 5, r: 0.6 }, 0, 0.6, { tone: "lo", crease: "none" }), L(ticks.minor, { tone: "lo" }), L(ticks.major, { tone: "mid" })].join("")));
  const ped = (x) => box({ x: x - 22, y: -30, w: 44, d: 22, r: 2 }, 0, 18, { tone: "mid", bevel: 0.6 });
  const deco = {
    tries: (x) => [box({ x: x - 16, y: -26, w: 32, d: 12, r: 1.5 }, 18, 12, { tone: "hi", bevel: 0.4 }), liveY("tries", "37", x, -14, 21, { px: 5.5 }), lamp("fix", x + 13, -26 + 4, 30, { r: 2 })].join(""),
    cost: (x) => [box({ x: x - 13, y: -27, w: 26, d: 16, r: 1.5 }, 18, 16, { tone: "mid", bevel: 0.4 }), show("costFill", box({ x: x - 10, y: -24, w: 20, d: 10, r: 1 }, 34, 2.5, { tone: "hi" })), L(k.planOutline({ x: x - 10, y: -24, w: 20, d: 10, r: 1 }, 34, P, 3), { tone: "lo" }), lamp("p1", x + 17, -12, 18, { r: 2.2 })].join(""),
    sealed: (x) => [box({ x: x - 14, y: -27, w: 28, d: 17, r: 1.5 }, 18, 20, { tone: "hi", bevel: 0.5 }), cyl(x, -18.5, 5, 38, 2, { tone: "mid" }), L(k.ring(x, -18.5, 3, 40, P, 18), { tone: "lo" }), lamp("p2", x + 17, -12, 18, { r: 2.2 })].join(""),
    plateau: (x) => [box({ x: x - 16, y: -26, w: 32, d: 12, r: 1 }, 18, 2, { tone: "lo" }), ...[9, 13, 16, 14, 10].map((h, i) => cyl(x - 12 + i * 6, -20, 2.2, 20, h, { tone: "hi", steps: 16 })), lamp("p3", x + 17, -12, 18, { r: 2.2 })].join(""),
    family: (x) => [show("famRack", [box({ x: x - 17, y: -27, w: 34, d: 16, r: 1 }, 18, 2, { tone: "lo" }), ...[0, 1, 2, 3, 4, 5].map((i) => box({ x: x - 15 + (i % 3) * 10.5, y: -25 + Math.floor(i / 3) * 7, w: 8, d: 5, r: 0.6 }, 20, 6 + (i % 2) * 3, { tone: "hi" }))].join("")), lamp("p4", x + 17, -12, 18, { r: 2.2 })].join(""),
    mc: (x) => [cyl(x, -19, 13, 18, 3, { tone: "lo", steps: 40 }), cyl(x, -19, 11, 21, 3, { tone: "hi", steps: 40, bevel: 0.4 }), L(k.radialTicks(x, -19, 9.5, 24, 6, 24, [1, 2], P).major + k.radialTicks(x, -19, 9.5, 24, 6, 24, [1, 2], P).minor, { tone: "lo" }), lamp("p5", x + 17, -12, 18, { r: 2.2 })].join(""),
  };
  for (const [id, name, x] of ST) out.push(hot(id, [ped(x), deco[id](x), labelY(name, x, -8, 3.2, { px: 4.2 })].join("")));
  // card tray at the end of the QMB bench
  out.push(hot("card", [box({ x: 116, y: -24, w: 12, d: 40, r: 1.5 }, 0, 8, { tone: "mid" }), show("cardOut", move("cardMv", box({ x: 117, y: -18, w: 10, d: 24, r: 0.6 }, 8, 1.5, { tone: "hi", bevel: 0 })))].join("")));
  // node bench across the gap
  out.push(hot("live", [box({ x: LB.x + 6, y: LB.y + 6, w: 46, d: 42, r: 3 }, 0, 30, { tone: "mid", bevel: 0.7 }), lamp("nodeL", LB.x + 40, LB.y + 18, 30), labelY("NODE", LB.x + 29, LB.y + 48, 8, { px: 5.5 })].join("")));
  // carriage with its cargo of trades
  const cart = [box({ x: -9, y: 8, w: 18, d: 14, r: 1.5 }, 3, 6, { tone: "hi", bevel: 0.5 }), show("cargo", [0, 1, 2].map((i) => box({ x: -6, y: 10, w: 12, d: 10, r: 0.6 }, 9 + i * 2.2, 1.6, { tone: "mid", bevel: 0 })).join(""))].join("");
  out.push(hot("unit", move("cart", cart, [-178, 0, 0])));
  const svg = svgOf(B, { label: "The QMB test line: a carriage carrying trades runs past a tries counter and stations for cost stress, sealed months, plateau, family check and the size cone, then a baseline card crosses a gap to the node bench.", body: out });
  const labels = {
    tries: "Tries ledger: every run counts. Best of N gets corrected.", cost: "Cost stress: still profitable at 2× calibrated cost?", sealed: "Out-of-sample in R, plus sealed months never searched.", plateau: "Plateau: the neighbours of the best setting must profit too.",
    family: "Family check (PBO): did we just pick the luckiest variant?", mc: "Block-bootstrap Monte Carlo: sets size and the live cone. Not a gate.", card: "Baseline card: frozen when a unit passes.", live: "Node: paper and live. A separate world.", unit: "The unit under test, with its trades in R.",
  };
  const xs = Object.fromEntries(ST.map(([id, , x]) => [id, x]));
  const today = `[
 {say:"Today an agent's backtest is refused: no door yet.",lit:["unit"],show:{ruler:false,costFill:false,famRack:false,cardOut:false,cargo:false},text:{tries:"37"},move:{cart:[${xs.tries},0,0]},ms:3000},
 {say:"Tries are counted, but no correction is applied.",lit:["tries"],text:{tries:"38"},ms:2800},
 {say:"The only runner is silent: no trades, no equity.",lit:["unit"],move:{cart:[${xs.cost},0,0]},ms:2800},
 {say:"Cost calibration is empty, so nothing counts as proof.",lit:["cost"],ms:2800},
 {say:"Replays bid/ask quotes only: no crypto, no perps.",lit:["sealed","unit"],move:{cart:[${xs.sealed},0,0]},ms:2800},
 {say:"Results in money, not R. No pass marks anywhere.",lit:["plateau"],move:{cart:[${xs.plateau},0,0]},ms:2800},
 {say:"The family check (PBO) was deferred. Not in the set.",lit:["family"],move:{cart:[${xs.family},0,0]},ms:2800},
 {say:"Shuffle Monte Carlo exists, as 'robustness only'.",lit:["mc"],move:{cart:[${xs.mc},0,0]},ms:2800},
 {say:"No baseline card comes out. Nothing crosses to the node.",lit:["card"],ms:3000}
]`;
  const proposed = `[
 {say:"Every run is a try in the unit's family. Best of N is corrected.",lit:["tries"],show:{ruler:true,costFill:true,famRack:true,cardOut:false,cargo:true},lamps:{fix:"ok"},text:{tries:"38"},move:{cart:[${xs.tries},0,0],cardMv:[0,0,0]},ms:3200},
 {say:"T1 cost stress: still positive at 2× calibrated cost.",lit:["cost"],move:{cart:[${xs.cost},0,0]},lamps:{p1:"ok"},ms:3000},
 {say:"T2 out-of-sample: ≥ +0.15R over ≥ 200 trades; sealed months > 0.",lit:["sealed"],move:{cart:[${xs.sealed},0,0]},lamps:{p2:"ok"},ms:3200},
 {say:"T3 plateau: the median of nearby settings still profits.",lit:["plateau"],move:{cart:[${xs.plateau},0,0]},lamps:{p3:"ok"},ms:3000},
 {say:"T4 family check: PBO ≤ 0.25 passes, > 0.50 is dead.",lit:["family"],move:{cart:[${xs.family},0,0]},lamps:{p4:"ok"},ms:3200},
 {say:"T5 Monte Carlo sets size and the live cone. Not pass/fail.",lit:["mc"],move:{cart:[${xs.mc},0,0]},lamps:{p5:"ok"},ms:3000},
 {say:"Pass: QMB freezes one baseline card for the unit.",lit:["card"],show:{cardOut:true},ms:2800},
 {say:"Only the card crosses. Paper and live stay on the node.",lit:["card","live"],move:{cardMv:[44,0,0]},lamps:{nodeL:"ok"},ms:3200}
]`;
  return { svg, P, labels, modes: `{today:${today},proposed:${proposed}}`, ease: 0.6 };
}
