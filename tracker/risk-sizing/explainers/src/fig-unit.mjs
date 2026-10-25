import { bench, svgOf } from "./parts.mjs";

// A unit cartridge in a pod tray, with the router's switches on the tray rail and the account guard beside it.
export function unitFig() {
  const BENCH = { x: -160, y: -70, w: 326, d: 140, r: 8 };
  const TRAY = { x: -150, y: -56, w: 228, d: 112, r: 5 };
  const SIB = { x: -142, y: -42, w: 54, d: 76, r: 3 };
  const HERO = { x: -76, y: -46, w: 142, d: 84, r: 4 };
  const HZ = 6, HT = 48;
  const RAIL = { x: -146, y: 42, w: 220, d: 10, r: 2 };
  const GUARD = { x: 90, y: -34, w: 58, d: 66, r: 4 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-52, -28, 74], [GUARD.x, GUARD.y, 52], [-142, -42, 40]], { width: 400, pad: 10 });
  const { box, cyl, hot, move, L, D, k, P, at, labelY, labelX, labelTop, lamp, dial } = B;
  const out = [];
  out.push(B.base(BENCH, { h: 8 }));
  // pod tray
  out.push(hot("pod", [box(TRAY, 0, HZ, { tone: "mid", bevel: 0.8, steps: 6 }), L(k.planOutline(k.insetPlan(TRAY, 3), HZ, P), { tone: "faint" }), labelTop("POD = THE TRAY · ONE SHARED BUDGET", -36, 63, 0, { px: 6 })].join("")));
  // pod budget dial on tray, front-left
  // sibling unit
  out.push(hot("sibling", [box(SIB, HZ, 28, { tone: "mid", bevel: 0.7 }), cyl(-115, -4, 9, HZ + 28, 3, { tone: "mid" }), L(k.ring(-115, -4, 6, HZ + 31, P, 24), { tone: "lo" }), labelY("SIBLING", -115, SIB.y + SIB.d, HZ + 9, { px: 7 })].join("")));
  // hero unit body
  out.push(hot("unit", [box(HERO, HZ, HT - HZ, { tone: "hi", bevel: 0.9, steps: 5 }), L(k.planOutline(k.insetPlan(HERO, 3.5), HT, P, 5), { tone: "faint" }), labelY("ONE UNIT = ONE ALGORITHM", -5, HERO.y + HERO.d, HZ + 13, { px: 7 }), D(k.corners(HERO, 6).map(([x, y]) => [x, y, HT]), { size: 0.5 })].join("")));
  // journal drum (back-left)
  out.push(hot("journal", [cyl(-52, -27, 15, HT, 2, { tone: "lo" }), cyl(-52, -27, 13, HT + 2, 22, { tone: "hi", steps: 40 }), L([HT + 8, HT + 13, HT + 18].map((z) => k.sideArc(-52, -27, 13, z, P, 28)).join(""), { tone: "faint" }), cyl(-52, -27, 4, HT + 24, 2, { tone: "mid" }), labelTop("JOURNAL", -52, -4, HT, { px: 7 })].join("")));
  // exam card in holder
  out.push(hot("exam", [box({ x: -30, y: -42, w: 32, d: 8, r: 1 }, HT, 4, { tone: "mid" }), box({ x: -28, y: -39, w: 28, d: 1.6, r: 0.3 }, HT + 4, 22, { tone: "hi", bevel: 0 }), labelY("EXAM", -14, -37.4, HT + 14, { px: 5.5, plate: false }), L([[-26, -6], [-26, -12], [-26, -18]].map(([x, dl], i) => k.segment([x, -37.35, HT + 11 - i * 2.4], [x + 20 + dl / 2 + 4, -37.35, HT + 11 - i * 2.4], P)).join(""), { tone: "lo", free: true })].join("")));
  // session profile bars
  const sess = [[10, 21], [25, 6], [40, 3]];
  out.push(hot("sessions", [box({ x: 6, y: -42, w: 48, d: 14, r: 1.5 }, HT, 2, { tone: "lo" }), ...sess.map(([x, h]) => box({ x, y: -40, w: 11, d: 10, r: 1 }, HT + 2, h, { tone: "hi", bevel: 0.4 })), labelTop("SESSIONS", 30, -21, HT, { px: 7 })].join("")));
  // needs pegs
  out.push(hot("needs", [box({ x: -22, y: -18, w: 34, d: 10, r: 1.5 }, HT, 2, { tone: "lo" }), ...[-15, -5, 5].map((x, i) => cyl(x, -13, 2.8, HT + 2, [7, 4, 9][i], { tone: "hi", steps: 18 })), labelTop("NEEDS", -5, 1, HT, { px: 7 })].join("")));
  // size dial
  const SIZE = dial("size", 38, 8, 18, HT, { value: 0.8 });
  out.push(hot("size", [SIZE.svg, labelTop("SIZE", 38, 31, HT, { px: 7 })].join("")));
  // entry trigger
  out.push(hot("entry", [cyl(-50, 16, 8.5, HT, 2, { tone: "lo" }), move("entryBtn", cyl(-50, 16, 6, HT + 2, 4, { tone: "hi", bevel: 0.5 })), labelTop("ENTRY", -50, 31, HT, { px: 7 })].join("")));
  // exit slider
  const SLOT = { x: -32, y: 12, w: 32, d: 6, r: 3 };
  out.push(hot("exits", [box(k.insetPlan(SLOT, -1.5), HT, 1.2, { tone: "lo" }), L(k.planOutline(SLOT, HT + 1.2, P, 4), { tone: "mid" }), move("exitKnob", box({ x: -32, y: 11.5, w: 7, d: 7, r: 1.5 }, HT + 1.2, 5, { tone: "hi", bevel: 0.4 })), labelTop("EXITS", -16, 29, HT, { px: 7 })].join("")));
  // router rail with switches and lamps
  const sw = (id, cx) => [box(k.insetPlan({ x: cx - 9, y: 45, w: 18, d: 4, r: 2 }, -1), 12, 0.8, { tone: "lo", crease: "none" }), L(k.planOutline({ x: cx - 9, y: 45, w: 18, d: 4, r: 2 }, 12.8, P, 3), { tone: "mid" }), move(id + "Knob", box({ x: cx - 9, y: 44, w: 6, d: 6, r: 1.4 }, 12.8, 4, { tone: "hi" }), [12, 0, 0]), lamp(id, cx + 15, 47, 12, { r: 2.6 })].join("");
  out.push(hot("router", [box(RAIL, HZ, 6, { tone: "mid", bevel: 0.5 }), sw("sib", -115), sw("hero", 10), labelY("ROUTER: ON / OFF", -50, RAIL.y + RAIL.d, HZ + 0.3, { px: 4.8, plate: false })].join("")));
  // wire guard -> tray
  out.push(B.wire([GUARD.x, -2, 14], [TRAY.x + TRAY.w, -2, 3], [[83, -2, 14], [83, -2, 3]]));
  // guard box
  out.push(hot("guard", [box(GUARD, 0, 44, { tone: "mid", bevel: 0.8 }), L(k.planOutline(k.insetPlan(GUARD, 4), 44, P), { tone: "faint" }), cyl(119, -2, 13, 44, 2, { tone: "lo" }), `<g data-cls="kill">${move("killBtn", cyl(119, -2, 9.5, 46, 5, { tone: "hi", bevel: 0.6 }))}</g>`, lamp("armed", 138, 20, 44, { r: 2.6 }), labelY("ACCOUNT GUARD", 119, GUARD.y + GUARD.d, 14, { px: 7 }), labelX("STOPS ONLY", GUARD.x + GUARD.w, 0, 22, { px: 5 })].join("")));
  const svg = svgOf(B, { label: "A unit is a cartridge with its entry button, exit slider, size dial, condition pegs, session bars, exam card and journal drum all on one body. It sits in a pod tray beside a sibling. The router's switches sit on the tray rail. The account guard stands beside the tray with a kill button.", body: out });
  const labels = {
    unit: "The unit: one complete algorithm, tested and traded as one.",
    entry: "Entry: decides when to open a trade.",
    exits: "Exits: its own, frozen when it is compiled.",
    size: "Size: calibrates itself from its own journal.",
    needs: "Needs: the market conditions it requires.",
    sessions: "Session profile, e.g. Tokyo 70 · London 20 · NY 10.",
    exam: "Exam baseline: its own backtest and stress behaviour.",
    journal: "Journal: one per unit, from creation to live.",
    sibling: "A sibling: same logic, another market. Its own unit.",
    router: "Router: switches units on or off. Nothing else.",
    pod: "Pod: shared budget, limits on same-bet units.",
    guard: "Account guard: can stop trading. Never resizes.",
  };
  const on = { sib: "ok", hero: "ok", armed: "ok" };
  const modes = `{main:[
 {say:"A unit is one complete trading algorithm. No separate parts.",lit:["unit"],lamps:${JSON.stringify(on)},ms:3200},
 {say:"Entry: it decides when to open a trade.",lit:["entry"],move:{entryBtn:[0,0,-3]},ms:2400},
 {say:"Exits belong to the unit and are tested with it.",lit:["exits"],move:{entryBtn:[0,0,0],exitKnob:[25,0,0]},ms:2600},
 {say:"Size: it calibrates itself from its own journal.",lit:["size","journal"],move:{exitKnob:[0,0,0]},dial:{size:0.45},ms:3000},
 {say:"Needs: the market conditions it requires before it fits.",lit:["needs"],dial:{size:0.62},ms:2600},
 {say:"Session profile: e.g. Tokyo 70 · London 20 · NY 10.",lit:["sessions"],ms:2600},
 {say:"Exam baseline: live is judged against its own exam.",lit:["exam"],ms:2600},
 {say:"One journal, from creation through stress, paper and live.",lit:["journal"],ms:2600},
 {say:"Outside 1: the router switches a unit on or off.",lit:["router","sibling"],lamps:{sib:"off"},move:{sibKnob:[0,0,0]},ms:3000},
 {say:"Outside 2: the pod shares one budget across its units.",lit:["pod"],lamps:{sib:"ok"},move:{sibKnob:[12,0,0]},ms:2800},
 {say:"Outside 3: the guard stops all trading. Size untouched.",lit:["guard","size"],lamps:{sib:"off",hero:"off",armed:"bad"},cls:{kill:"bad"},move:{killBtn:[0,0,-3],sibKnob:[12,0,0]},ms:3400},
 {say:"Guard reset. The unit carries on its own way.",lit:["unit"],lamps:${JSON.stringify(on)},cls:{kill:""},move:{killBtn:[0,0,0]},ms:2400}
]}`;
  return { svg, P, dials: { size: SIZE.spec }, labels, modes, init: { move: { sibKnob: [12, 0, 0], heroKnob: [12, 0, 0] } } };
}
