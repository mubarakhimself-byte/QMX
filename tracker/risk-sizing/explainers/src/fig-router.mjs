import { bench, svgOf } from "./parts.mjs";

// PC planner on the left, node on the right: plan holder with an age dial, four live checks, three lanes with gates, local kill switch.
export function routerFig() {
  const BENCH = { x: -150, y: -60, w: 300, d: 120, r: 8 };
  const NODE = { x: -40, y: -52, w: 182, d: 104, r: 5 };
  const NZ = 10;
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-118, -40, 56]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, D, k, P, labelY, labelX, labelTop, liveY, lamp, dial, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  // PC
  const PC = { x: -142, y: -50, w: 50, d: 44, r: 3 };
  out.push(hot("pc", [box(PC, 0, 46, { tone: "mid", bevel: 0.8 }), L(k.planOutline(k.insetPlan(PC, 4), 46, P), { tone: "faint" }), box({ x: PC.x + 10, y: PC.y + 10, w: 30, d: 20, r: 1 }, 46, 2, { tone: "lo" }), move("plan", box({ x: PC.x + 12, y: PC.y + 12, w: 26, d: 16, r: 0.6 }, 48, 1.4, { tone: "hi", bevel: 0 })), lamp("pc", PC.x + 42, PC.y + 38, 46, { r: 2.6 }), labelY("PC PLANNER", PC.x + PC.w / 2, PC.y + PC.d, 20, { px: 5.2 }), labelX("SLOW LANE", PC.x + PC.w, PC.y + 22, 28, { px: 3.8 })].join("")));
  // cable: plugged in, or lying unplugged on the bench
  out.push(show("cableOn", B.wire([PC.x + PC.w, -28, 12], [NODE.x, -28, 6], [[-80, -28, 1], [-52, -28, 1]], { tone: "mid", flow: true })));
  out.push(show("cableOff", B.wire([PC.x + PC.w, -28, 12], [-64, -14, 1.2], [[-80, -28, 1], [-74, -18, 1]], { tone: "lo" })));
  // node plinth
  out.push(hot("node", [box(NODE, 0, NZ, { tone: "mid", bevel: 1, steps: 6 }), L(k.planOutline(k.insetPlan(NODE, 3.5), NZ, P, 6), { tone: "faint" }), labelY("NODE · FAST LANE", NODE.x + 60, NODE.y + NODE.d, 1.5, { px: 4.8 })].join("")));
  // plan holder with age dial
  const AGE = dial("age", -14, -32, 12, NZ + 14, { h: 3, value: 0, from: -0.75 * Math.PI, span: 1.5 * Math.PI, ticks: 18, every: 6 });
  out.push(hot("plan", [box({ x: -34, y: -48, w: 40, d: 32, r: 2 }, NZ, 14, { tone: "mid", bevel: 0.5 }), AGE.svg, show("planCard", box({ x: -32, y: -46, w: 6, d: 26, r: 0.5 }, NZ + 14, 12, { tone: "hi", bevel: 0 })), labelY("PLAN + AGE", -14, -16, NZ + 3, { px: 3.8 })].join("")));
  // four live checks
  [["spread", "SPREAD"], ["news", "NEWS"], ["feed", "FEED"], ["session", "SESSION"]].forEach(([id, name], i) => {
    out.push(hot("checks", [lamp(id, -26 + (i % 2) * 22, -2 + Math.floor(i / 2) * 22, NZ, { r: 3.4 }), labelTop(name, -26 + (i % 2) * 22, 7 + Math.floor(i / 2) * 22, NZ, { px: 3.2 })].join("")));
  });
  // three lanes with gates
  const LANES = [-36, -6, 24];
  LANES.forEach((y, i) => {
    out.push(hot("lanes", [box({ x: 16, y, w: 112, d: 18, r: 1.5 }, NZ, 2, { tone: "lo" }), L(k.lineOnTop([16, y + 9], [128, y + 9], NZ + 2, P), { tone: "faint" })].join("")));
  });
  // tokens: waiting units (before the gate) and open trades (past it). Built at x = 0 and moved.
  const tok = (id, y, x0) => move(id, box({ x: -5, y: y + 4, w: 10, d: 10, r: 1.5 }, NZ + 2, 7, { tone: "hi", bevel: 0.4 }), [x0, 0, 0]);
  LANES.forEach((y, i) => out.push(hot("units", tok("wait" + i, y, 30))));
  LANES.forEach((y, i) => {
    out.push(hot("gates", [box({ x: 50, y: y - 2, w: 4, d: 3, r: 0.5 }, NZ, 22, { tone: "mid" }), box({ x: 50, y: y + 17, w: 4, d: 3, r: 0.5 }, NZ, 22, { tone: "mid" }), box({ x: 49.5, y: y - 2.5, w: 5, d: 23, r: 0.8 }, NZ + 22, 3, { tone: "mid" }), move("gate" + i, `<g data-cls="gt${i}">${box({ x: 50.8, y: y + 1, w: 2.4, d: 16, r: 0.3 }, NZ + 2, 9, { tone: "hi", bevel: 0 })}</g>`, [0, 0, 11])].join("")));
  });
  LANES.forEach((y, i) => out.push(hot("trades", tok("open" + i, y, 74))));
  // kill switch
  out.push(hot("kill", [cyl(132, 38, 9, NZ, 3, { tone: "lo" }), `<g data-cls="kill">${cyl(132, 38, 6, NZ + 3, 4, { tone: "hi", bevel: 0.5 })}</g>`, lamp("killArmed", 116, 46, NZ, { r: 2.4 }), labelTop("KILL (LOCAL)", 128, 51, NZ, { px: 3.4 })].join("")));
  const svg = svgOf(B, { label: "A PC planner on the left, cabled to a node on the right. On the node: a plan holder with an age dial, four live-check lamps (spread, news, feed, session), three lanes each with a gate that drops to block new entries, waiting units before the gates and open trades past them, and a local kill switch.", body: out });
  const labels = { pc: "Planner on the PC: proof + slow regimes → a plan.", plan: "Cached plan with version, 'fresh until' and 'stop after'.", checks: "Cheap live checks: spread, news, feed, session…", lanes: "One lane per seat: a unit on a market.", gates: "Gate: closes to new entries only.", units: "Units waiting to open a trade.", trades: "Open trades: always finish under the unit's own exits.", kill: "Kill switch: local, independent of the plan.", node: "The node: the fast lane, near the broker." };
  const gatesUp = `gate0:[0,0,11],gate1:[0,0,11],gate2:[0,0,11]`;
  const bm = `${gatesUp},wait0:[30,0,0],wait1:[30,0,0],wait2:[30,0,0],open0:[74,0,0],open1:[74,0,0],open2:[74,0,0]`;
  const lm = `spread:"ok",news:"ok",feed:"ok",session:"ok",killArmed:"ok"`;
  const online = `[
 {say:"The planner on the PC turns proof and slow regimes into a plan.",lit:["pc"],show:{cableOn:true,cableOff:false,planCard:true},lamps:{pc:"ok",${lm}},dial:{age:0.05},cls:{gt0:"",gt1:"",gt2:""},move:{plan:[0,0,4],${bm}},ms:3200},
 {say:"It pushes the plan: seats, windows, tolerances and an expiry.",lit:["plan"],move:{plan:[0,0,0]},ms:3200},
 {say:"Every bar, cheap checks. All clear: gates open.",lit:["checks","gates"],move:{open0:[118,0,0],open1:[118,0,0]},ms:3200},
 {say:"Spread too wide on lane 2: its gate closes to new entries.",lit:["gates"],lamps:{spread:"bad"},move:{gate1:[0,0,0]},cls:{gt1:"bad"},ms:3400},
 {say:"Its open trade carries on under the unit's own exits.",lit:["trades"],move:{open1:[118,0,0]},ms:3000},
 {say:"Spread back to normal: the gate reopens.",lit:["gates"],lamps:{spread:"ok"},move:{gate1:[0,0,11]},cls:{gt1:""},ms:2800},
 {say:"The gate never sizes, never exits, never changes a unit.",lit:["units","trades"],ms:3000}
]`;
  const offline = `[
 {say:"The PC goes offline. Nothing changes at that moment.",lit:["pc"],show:{cableOn:false,cableOff:true,planCard:true},lamps:{pc:"off",${lm}},dial:{age:0.05},cls:{gt0:"",gt1:"",gt2:""},move:{plan:[0,0,0],${bm}},ms:3200},
 {say:"The node keeps trading from its cached plan. Same code.",lit:["plan","node"],dial:{age:0.25},move:{open0:[118,0,0]},ms:3200},
 {say:"Past 'fresh until' (e.g. 24 h): still used. You see 'plan 30 h old'.",lit:["plan"],dial:{age:0.55},lamps:{feed:"warn"},ms:3400},
 {say:"Past 'stop after' (e.g. 5 trading days): no new entries anywhere.",lit:["gates","plan"],dial:{age:1},move:{gate0:[0,0,0],gate1:[0,0,0],gate2:[0,0,0]},cls:{gt0:"bad",gt1:"bad",gt2:"bad"},ms:3600},
 {say:"Open trades finish under their own exits. The kill switch stays armed.",lit:["trades","kill"],move:{open0:[118,0,0],open1:[118,0,0],open2:[118,0,0]},ms:3400},
 {say:"PC back: node uploads its journal, the PC replays it, pushes a new plan.",lit:["pc","plan"],show:{cableOn:true,cableOff:false},lamps:{pc:"ok",feed:"ok"},dial:{age:0.05},move:{${gatesUp},open0:[74,0,0],open1:[74,0,0],open2:[74,0,0]},cls:{gt0:"",gt1:"",gt2:""},ms:3600}
]`;
  return { svg, P, labels, dials: { age: AGE.spec }, modes: `{online:${online},offline:${offline}}`, ease: 0.6 };
}
