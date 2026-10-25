import { bench, svgOf } from "./parts.mjs";

// Left: a fuse board, one fuse per session (loss points, acts at once). Right: the nightly console with four meters and three lamps.
export function decayFig() {
  const BENCH = { x: -134, y: -58, w: 268, d: 116, r: 8 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [60, -40, 50]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, D, k, P, labelY, labelX, labelTop, liveY, lamp, dial, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  // fuse board
  const FB = { x: -124, y: -40, w: 104, d: 60, r: 3 };
  out.push(hot("fast", [box(FB, 0, 12, { tone: "mid", bevel: 0.7 }), L(k.planOutline(k.insetPlan(FB, 3), 12, P), { tone: "faint" }), labelY("LOSS POINTS · ACTS NOW", FB.x + FB.w / 2, FB.y + FB.d, 2.4, { px: 4.3 })].join("")));
  const SESS = [["TOKYO", -102], ["LONDON", -72], ["NY", -42]];
  SESS.forEach(([name, x], i) => {
    out.push(hot("fuse", [box({ x: x - 7, y: -32, w: 14, d: 6, r: 1 }, 12, 9, { tone: "mid" }), box({ x: x - 7, y: -4, w: 14, d: 6, r: 1 }, 12, 9, { tone: "mid" }),
      show("f" + i, `<g data-cls="fz${i}">${box({ x: x - 4.5, y: -27, w: 9, d: 24, r: 3.5 }, 14, 6, { tone: "hi", bevel: 0.4 })}</g>`), labelTop(name, x, 9, 12, { px: 3.8 })].join("")));
  });
  // nightly console
  const NC = { x: 2, y: -48, w: 122, d: 70, r: 3 };
  out.push(hot("slow", [box(NC, 0, 26, { tone: "mid", bevel: 0.8 }), L(k.planOutline(k.insetPlan(NC, 3.5), 26, P), { tone: "faint" }), labelY("NIGHTLY CHECK · INFORMS", NC.x + NC.w / 2, NC.y + NC.d, 6, { px: 4.6 })].join("")));
  const meters = [["edge", "EDGE", 24, -30, 11], ["cone", "CONE", 56, -30, 9], ["cost", "COST", 84, -30, 9], ["rate", "RATE", 108, -30, 8]];
  const specs = {};
  for (const [id, name, x, y, r] of meters) {
    const d = dial(id, x, y, r, 26, { h: 3, value: 0.05, ticks: 20, every: 5 });
    specs[id] = d.spec;
    out.push(hot("m-" + id, [d.svg, labelTop(name, x, y + r + 6, 26, { px: 3.6 })].join("")));
  }
  // night counter and state lamps
  out.push(hot("night", [box({ x: 10, y: -4, w: 34, d: 18, r: 1.5 }, 26, 6, { tone: "hi", bevel: 0.4 }), liveY("night", "NIGHT 1", 27, 14, 27.4, { px: 3.4 })].join("")));
  [["ok", "OK", 62], ["watch", "WATCH", 86], ["alarm", "ALARM", 110]].forEach(([id, name, x]) => out.push(hot("state", [lamp(id, x, 4, 26, { r: 4.2 }), labelTop(name, x, 16, 26, { px: 3.6 })].join(""))));
  const svg = svgOf(B, { label: "Left, a fuse board with one fuse per session; a session that hits its loss points blows its fuse at once. Right, a nightly console with four meters (edge alarm, cone, cost drift, trade rate), a night counter and three lamps: OK, Watch, Alarm.", body: out });
  const labels = { fast: "Fast rules on the node: act at once, no statistics.", fuse: "One fuse per session: its loss points, with a day cap.", slow: "Nightly job over the unit's journal. It informs, never acts.", "m-edge": "Edge alarm (CUSUM on R) vs the exam baseline.", "m-cone": "Live R vs the Monte Carlo cone from stress.", "m-cost": "Cost and fill drift vs the baseline card.", "m-rate": "Trade rate and replay match vs the card.", night: "Runs once a day after the last session closes.", state: "OK, Watch or Alarm. States, not a score." };
  const modes = `{main:[
 {say:"Two kinds of protection: fast rules and a slow check.",lit:["fast","slow"],lamps:{ok:"ok"},show:{f0:true,f1:true,f2:true},cls:{fz0:"",fz1:"",fz2:""},dial:{edge:0.05,cone:0.05,cost:0.05,rate:0.05},text:{night:"NIGHT 1"},ms:3000},
 {say:"London hits its loss points: its fuse blows. No more trades this session.",lit:["fuse"],cls:{fz1:"bad"},ms:3200},
 {say:"Next session it resets. Loss points protect today.",lit:["fuse"],cls:{fz1:""},ms:2600},
 {say:"Three sessions in a row hit → back to paper (example).",lit:["fuse","fast"],cls:{fz0:"bad",fz1:"bad",fz2:"bad"},ms:3200},
 {say:"Slow: every night a job reads the journal against the exam baseline.",lit:["slow","night"],cls:{fz0:"",fz1:"",fz2:""},text:{night:"NIGHT 12"},dial:{edge:0.3},ms:3200},
 {say:"The edge alarm adds up how far live R falls short.",lit:["m-edge"],text:{night:"NIGHT 30"},dial:{edge:0.55,cone:0.2},ms:3000},
 {say:"Past 70% of its limit: WATCH. Hold size, no new markets.",lit:["m-edge","state"],lamps:{ok:"off",watch:"warn"},text:{night:"NIGHT 41"},dial:{edge:0.74,cost:0.35},ms:3400},
 {say:"Limit hit: ALARM. Back to paper; the journal keeps running.",lit:["state"],lamps:{watch:"off",alarm:"bad"},text:{night:"NIGHT 52"},dial:{edge:1,cone:0.7},ms:3400},
 {say:"It only informs. The unit's rules, the Book door or you act.",lit:["slow"],ms:3000},
 {say:"Back to live only on new evidence, after a minimum time, by your click.",lit:["state"],lamps:{alarm:"off",ok:"ok"},dial:{edge:0.05,cone:0.05,cost:0.05},text:{night:"NIGHT 1"},ms:3400}
]}`;
  return { svg, P, labels, modes, dials: specs, ease: 0.5 };
}
