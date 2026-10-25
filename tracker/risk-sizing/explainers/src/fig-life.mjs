import { bench, svgOf } from "./parts.mjs";

// A conveyor of six stations on two benches (QMB world, node world). The unit rides it; a clamp freezes it after stress.
export function lifeFig() {
  const QB = { x: -196, y: -34, w: 236, d: 68, r: 6 };
  const NB = { x: 58, y: -34, w: 138, d: 68, r: 6 };
  const ST = [["SOURCE", -170], ["BUILD", -112], ["BACKTEST", -52], ["STRESS", 8], ["PAPER", 92], ["LIVE", 160]];
  const pts = [[QB.x, QB.y, -12], [NB.x + NB.w, NB.y + NB.d, -12], [QB.x, QB.y + QB.d, -12], [NB.x + NB.w, NB.y, -12], [-52, -10, 60], [160, -20, 60]];
  const B = bench(pts, { width: 400, pad: 8, azimuth: 60 });
  const { box, cyl, hot, move, L, D, k, P, labelY, labelTop, lamp, show } = B;
  const out = [B.base(QB, { h: 8 }), B.base(NB, { h: 8 })];
  out.push(labelY("QMB WORLD", QB.x + 40, QB.y + QB.d, -7, { px: 5, plate: false, tone: "mid" }));
  out.push(labelY("NODE WORLD", NB.x + 40, NB.y + NB.d, -7, { px: 5, plate: false, tone: "mid" }));
  // rails
  out.push(box({ x: QB.x + 6, y: 12, w: QB.w - 12, d: 6, r: 1 }, 0, 3, { tone: "lo" }));
  out.push(box({ x: NB.x + 6, y: 12, w: NB.w - 12, d: 6, r: 1 }, 0, 3, { tone: "lo" }));
  const deco = {
    SOURCE: (x) => [0, 1, 2].map((i) => box({ x: x - 14 + i * 2, y: -24 + i * 3, w: 20, d: 14, r: 0.5 }, 20 + i * 2.2, 1.6, { tone: "hi", bevel: 0 })).join(""),
    BUILD: (x) => [box({ x: x - 12, y: -24, w: 24, d: 18, r: 2 }, 20, 12, { tone: "mid", bevel: 0.5 }), cyl(x - 4, -15, 3, 32, 3, { tone: "hi" }), cyl(x + 5, -15, 3, 32, 3, { tone: "hi" })].join(""),
    BACKTEST: (x) => [box({ x: x - 16, y: -26, w: 4, d: 4, r: 0.6 }, 20, 26, { tone: "mid" }), box({ x: x + 12, y: -26, w: 4, d: 4, r: 0.6 }, 20, 26, { tone: "mid" }), box({ x: x - 17, y: -27, w: 34, d: 6, r: 1 }, 46, 4, { tone: "mid", bevel: 0.4 }), lamp("bt", x, -24, 50, { r: 2.6 })].join(""),
    STRESS: (x) => [box({ x: x - 16, y: -26, w: 4, d: 4, r: 0.6 }, 20, 26, { tone: "mid" }), box({ x: x + 12, y: -26, w: 4, d: 4, r: 0.6 }, 20, 26, { tone: "mid" }), box({ x: x - 17, y: -27, w: 34, d: 6, r: 1 }, 46, 4, { tone: "mid", bevel: 0.4 }), move("weight", box({ x: x - 8, y: -25, w: 16, d: 2, r: 0.4 }, 34, 10, { tone: "hi" })), lamp("st", x + 10, -24, 50, { r: 2.6 })].join(""),
    PAPER: (x) => [box({ x: x - 14, y: -26, w: 28, d: 6, r: 1 }, 20, 4, { tone: "lo" }), box({ x: x - 12, y: -24, w: 24, d: 2, r: 0.4 }, 24, 18, { tone: "hi", bevel: 0 }), lamp("pp", x + 18, -18, 20, { r: 2.6 })].join(""),
    LIVE: (x) => [cyl(x, -16, 9, 20, 3, { tone: "lo" }), `<g data-cls="key">${cyl(x, -16, 6, 23, 4, { tone: "hi", bevel: 0.5 })}</g>`, box({ x: x - 1.2, y: -20, w: 2.4, d: 8, r: 0.6 }, 27, 3, { tone: "mid" }), lamp("lv", x + 14, -6, 20, { r: 2.6 })].join(""),
  };
  for (const [name, x] of ST) {
    const id = name.toLowerCase();
    out.push(hot(id, [box({ x: x - 22, y: -30, w: 44, d: 22, r: 2 }, 0, 20, { tone: "mid", bevel: 0.6 }), deco[name](x), labelY(name, x, -8, 4, { px: 4.6 })].join("")));
  }
  // the unit token on the rail, with its freeze clamp
  const T = { x: -8, y: 9, w: 16, d: 12, r: 1.5 };
  const token = [box(T, 3, 10, { tone: "hi", bevel: 0.5 }), show("clamp", [box({ x: -9.5, y: 7.5, w: 3, d: 15, r: 0.6 }, 2.5, 11.5, { tone: "mid" }), box({ x: 6.5, y: 7.5, w: 3, d: 15, r: 0.6 }, 2.5, 11.5, { tone: "mid" }), box({ x: -9.5, y: 7.5, w: 19, d: 15, r: 1 }, 14, 2, { tone: "mid" })].join(""))].join("");
  out.push(hot("token", move("unit", token, [-170, 0, 0])));
  const svg = svgOf(B, { label: "Six stations on two benches: source, build, backtest and stress on the QMB bench; paper and live on the node bench. A unit rides the rail; a clamp locks it after stress; live needs your key.", body: out });
  const labels = {
    source: "Source: an article, a video, a chat or your own idea.", build: "Build: the library turns a spec into a unit. Logic still open.", backtest: "Backtest (and optimise). Every run counts as a try.",
    stress: "Stress: cost ×2, sealed months, worst days. Then frozen.", paper: "Paper on the node. Written by the node only.", live: "Live: your click admits it.", token: "The unit. Stages move one way.",
  };
  const xs = Object.fromEntries(ST.map(([n, x]) => [n, x]));
  const modes = `{main:[
 {say:"Source: an idea from an article, a video, a chat or you.",lit:["source","token"],move:{unit:[${xs.SOURCE},0,0]},show:{clamp:false},ms:2800},
 {say:"Build: the library makes it a unit. Logic is still open.",lit:["build","token"],move:{unit:[${xs.BUILD},0,0]},ms:2800},
 {say:"Backtest and optimise in QMB. Each run counts as a try.",lit:["backtest"],move:{unit:[${xs.BACKTEST},0,0]},lamps:{bt:"ok"},ms:3000},
 {say:"Stress test. Its results become the unit's exam baseline.",lit:["stress"],move:{unit:[${xs.STRESS},0,0],weight:[0,0,-6]},lamps:{st:"ok"},ms:3000},
 {say:"Compiled: logic and exits frozen. Only its numbers self-tune.",lit:["token"],show:{clamp:true},move:{weight:[0,0,0]},ms:3000},
 {say:"Paper on the node. QMB never writes here.",lit:["paper"],move:{unit:[${xs.PAPER},0,0]},lamps:{pp:"ok"},ms:3000},
 {say:"Live only after your click.",lit:["live"],cls:{key:"warn"},ms:2600},
 {say:"Live. Stages only move forward; a fall-back means paper again.",lit:["live","token"],move:{unit:[${xs.LIVE},0,0]},cls:{key:"ok"},lamps:{lv:"ok"},ms:3200}
]}`;
  return { svg, P, labels, modes, init: { move: { unit: [xs.SOURCE, 0, 0] } }, ease: 0.6 };
}
