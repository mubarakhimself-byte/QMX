import { bench, svgOf } from "./parts.mjs";

// Size column with a draggable ceiling stop; an account-floor ratchet beside an equity float; a house-money switch; a skip tray.
export function sizingFig() {
  const BENCH = { x: -140, y: -56, w: 280, d: 112, r: 8 };
  const SZ = (pct) => (pct / 0.6) * 80; // carriage lift per % risk
  const EZ = (eq) => (eq - 60) * 1.3; // equity % of start -> lift
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-122, -34, 104], [-12, -34, 100]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, D, k, P, labelY, labelX, labelTop, liveY, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  // journal feeding the column
  out.push(hot("journal", [box({ x: -66, y: -52, w: 34, d: 24, r: 2 }, 0, 24, { tone: "mid", bevel: 0.5 }), labelY("JOURNAL", -49, -28, 8, { px: 4.2 })].join("")));
  out.push(B.wire([-66, -38, 12], [-78, -30, 12], [[-72, -38, 12], [-72, -30, 12]]));
  // size column
  out.push(hot("column", [box({ x: -128, y: -38, w: 56, d: 18, r: 2 }, 0, 6, { tone: "lo" }), box({ x: -122, y: -34, w: 44, d: 10, r: 1.5 }, 6, 98, { tone: "mid", bevel: 0.6 }), ...[0.1, 0.3, 0.5].map((p) => labelX(p.toFixed(1) + "%", -78, -29, 8 + SZ(p) + 1, { px: 3.6 }))].join("")));
  out.push(hot("size", move("size", [box({ x: -121, y: -24, w: 42, d: 12, r: 1.5 }, 2, 14, { tone: "hi", bevel: 0.5 }), labelY("SIZE", -100, -12, 5.5, { px: 5, plate: false })].join(""), [0, 0, SZ(0.5)])));
  out.push(hot("ceiling", move("ceil", [box({ x: -125, y: -25, w: 50, d: 15, r: 1.5 }, 16, 10, { tone: "mid", bevel: 0.5 }), cyl(-78, -17, 3.4, 18, 6, { tone: "hi", steps: 16 }), liveY("ceil", "CEILING 0.50%", -101, -10, 18.6, { px: 4.2 })].join(""), [0, 0, SZ(0.5)]), ' style="touch-action:none"'));
  // fresh evidence counter
  out.push(hot("fresh", [box({ x: -130, y: 4, w: 60, d: 24, r: 2 }, 0, 16, { tone: "mid", bevel: 0.5 }), liveY("fresh", "FRESH TRADES —", -100, 28, 6, { px: 3.8 })].join("")));
  // floor ratchet
  const teeth = Array.from({ length: 14 }, (_, i) => box({ x: -12, y: -24, w: 12, d: 2.2, r: 0.4 }, 6 + i * 7, 3.4, { tone: "mid", bevel: 0 })).join("");
  out.push(hot("ratchet", [box({ x: -16, y: -36, w: 20, d: 14, r: 1.5 }, 0, 6, { tone: "lo" }), box({ x: -12, y: -34, w: 12, d: 10, r: 1 }, 6, 98, { tone: "mid", bevel: 0.4 }), teeth].join("")));
  out.push(hot("equity", [cyl(22, -28, 1.8, 0, 104, { tone: "mid", steps: 14 }), cyl(22, -28, 5, 0, 3, { tone: "lo" })].join("")));
  out.push(hot("equity", move("eq", [box({ x: 14, y: -35, w: 16, d: 14, r: 1.5 }, 0, 6, { tone: "hi", bevel: 0.4 }), labelY("EQUITY", 22, -21, 1, { px: 3, plate: false })].join(""), [0, 0, EZ(100)])));
  out.push(hot("floor", move("floor", [`<g data-cls="floorc">${box({ x: -19, y: -22, w: 26, d: 9, r: 1.2 }, 0, 6, { tone: "hi", bevel: 0.4 })}</g>`, labelY("FLOOR", -6, -13, 1, { px: 3.2, plate: false })].join(""), [0, 0, EZ(80)])));
  out.push(hot("ratchet", [box({ x: -32, y: 4, w: 70, d: 24, r: 2 }, 0, 12, { tone: "mid", bevel: 0.5 }), labelY("FLOOR ONLY RISES", 3, 28, 3.5, { px: 4 })].join("")));
  // house money switch
  out.push(hot("house", [box({ x: 58, y: -40, w: 66, d: 42, r: 2.5 }, 0, 22, { tone: "mid", bevel: 0.6 }), lamp("house", 108, -26, 22, { r: 3.2 }), box(k.insetPlan({ x: 66, y: -32, w: 24, d: 8, r: 3 }, -1), 22, 0.8, { tone: "lo", crease: "none" }), move("houseKnob", box({ x: 66, y: -33, w: 8, d: 10, r: 1.5 }, 22.8, 4, { tone: "hi" })), labelY("HOUSE MONEY", 91, 2, 7, { px: 4.2 })].join("")));
  // skip tray
  out.push(hot("skip", [box({ x: 58, y: 12, w: 66, d: 32, r: 2.5 }, 0, 4, { tone: "mid" }), box(k.insetPlan({ x: 58, y: 12, w: 66, d: 32, r: 2.5 }, 3), 4, 4, { tone: "lo" }), show("skipT", move("skipTok", box({ x: 80, y: 20, w: 12, d: 10, r: 1 }, 4, 5, { tone: "hi", bevel: 0.4 }), [0, 0, 30])), labelY("SKIPPED", 91, 44, 0.5, { px: 3.6, plate: false })].join("")));
  const svg = svgOf(B, { label: "A size column whose carriage marks risk per trade under a ceiling stop you can drag; a fresh-trades counter at its foot fed by the journal. Beside it a ratchet rack whose floor marker only climbs, next to an equity float. A house-money switch and a tray for skipped trades.", body: out });
  const labels = { size: "Size: risk per trade the unit uses now.", ceiling: "Your ceiling. Drag it up or down.", column: "Size scale in % risk per trade.", fresh: "Fresh trades since the cut that still show the edge.", journal: "Calibrates from its own journal.", floor: "Account floor: follows the best level, never falls.", ratchet: "One-way ratchet: on the account floor, not on size.", equity: "Equity: goes up and down.", house: "House money: on only if the record shows streaks.", skip: "Skipped: the minimum lot can't size it safely." };
  const st = (o) => JSON.stringify(o).slice(1, -1);
  const modes = `{main:[
 {say:"Size sits at your ceiling: 0.5% risk per trade (example).",lit:["size","ceiling"],move:{size:[0,0,${SZ(0.5)}],eq:[0,0,${EZ(100)}],floor:[0,0,${EZ(80)}],skipTok:[0,0,30],houseKnob:[0,0,0]},text:{fresh:"FRESH TRADES —"},show:{skipT:false},ms:3200},
 {say:"A good run: equity makes new highs, the floor ratchets up.",lit:["equity","floor"],move:{eq:[0,0,${EZ(118)}],floor:[0,0,${EZ(98)}]},ms:3200},
 {say:"A bad week: size snaps down fast, 0.5% → 0.3%.",lit:["size"],move:{size:[0,0,${SZ(0.3)}],eq:[0,0,${EZ(104)}]},ms:3000},
 {say:"The floor stays where it was. It never falls back.",lit:["floor","ratchet"],ms:3000},
 {say:"Growing back needs fresh trades that still show the edge.",lit:["fresh","journal"],text:{fresh:"FRESH TRADES 30/60"},move:{size:[0,0,${SZ(0.36)}],eq:[0,0,${EZ(108)}]},ms:3200},
 {say:"60 fresh trades later (example): back to 0.5%, no higher.",lit:["size","fresh"],text:{fresh:"FRESH TRADES 60/60"},move:{size:[0,0,${SZ(0.5)}],eq:[0,0,${EZ(121)}],floor:[0,0,${EZ(101)}]},ms:3400},
 {say:"Your ceiling caps it. Drag the ceiling to try.",lit:["ceiling"],ms:3600},
 {say:"A trade the minimum lot can't size safely is skipped and logged.",lit:["skip"],show:{skipT:true},move:{skipTok:[0,0,0]},ms:3000},
 {say:"House money only switches on if its record shows streaks.",lit:["house"],lamps:{house:"ok"},move:{houseKnob:[14,0,0]},ms:3200}
]}`;
  const extra = `after:(s,api)=>{const c=api.movers.ceil.to[2],m=api.movers.size;if(m.to[2]>c)m.to[2]=c;},
setup:(api,ctl)=>{const g=api.root.querySelector('[data-hot="ceiling"]');const vb=${B.width};const rise=${k.screenRise(1, P)};let y0=null,z0=0;
const z2p=(z)=>z/80*0.6;
g.addEventListener('pointerdown',(e)=>{ctl.pause();y0=e.clientY;z0=api.movers.ceil.to[2];g.setPointerCapture(e.pointerId);e.preventDefault();});
g.addEventListener('pointermove',(e)=>{if(y0===null)return;const r=api.svg.getBoundingClientRect();const dz=-(e.clientY-y0)/(rise*r.width/vb);const z=Math.max(${SZ(0.2)},Math.min(${SZ(0.6)},z0+dz));api.movers.ceil.to[2]=z;api.movers.ceil.cur[2]=z;const m=api.movers.size;if(m.to[2]>z)m.to[2]=z;
api.setText('ceil','CEILING '+z2p(z).toFixed(2)+'%');api.say('Ceiling '+z2p(z).toFixed(2)+'%. Size can never go above it.');api.draw();api.run();});
const end=()=>{y0=null;};g.addEventListener('pointerup',end);g.addEventListener('pointercancel',end);}`;
  return { svg, P, labels, modes, extra, ease: 0.55 };
}
