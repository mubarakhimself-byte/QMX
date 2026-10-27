import { bench, svgOf, unitBlock, cardY, socket, reset } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// A key lock (his click), a fenced tray (the envelope) with three market sockets and the unit,
// a paper tray outside the fence, and the router's offer board at the back. An offer card travels.
export function envelopeFig() {
  const BENCH = { x: -132, y: -86, w: 264, d: 172, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-106, -62, 60], [80, -70, 50]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];

  // lock pedestal: his click
  const LK = { x: -124, y: -78, w: 38, d: 30, r: 2.5 };
  out.push(hot("lock", [box(LK, 0, 22, { tone: "mid", bevel: 0.7 }), L(k.planOutline(k.insetPlan(LK, 3), 22, P), { tone: "faint" }), cyl(-110, -63, 8.5, 22, 1.6, { tone: "lo" }), L(k.ring(-110, -63, 6, 23.6, P, 24), { tone: "mid" }), box({ x: -111.6, y: -66.5, w: 3.2, d: 7, r: 0.4 }, 23.6, 0.3, { tone: "lo", bevel: 0 }),
    move("key", [box({ x: -111, y: -64.6, w: 2, d: 3.2, r: 0.3 }, 23.8, 12, { tone: "hi", bevel: 0 }), box({ x: -114.5, y: -64.6, w: 9, d: 3.2, r: 1.4 }, 35.8, 9, { tone: "hi", bevel: 0.4 })].join(""), [0, 0, 9]),
    lamp("admit", -94, -56, 22, { r: 2.6 }), labelX("YOUR CLICK", LK.x + LK.w, LK.y + LK.d / 2, 7, { px: 4.2 })].join("")));

  // router offer board
  const RB = { x: 34, y: -80, w: 86, d: 22, r: 2.5 };
  out.push(hot("router", [box(RB, 0, 30, { tone: "mid", bevel: 0.7 }), box({ x: 40, y: -74, w: 60, d: 6, r: 1 }, 30, 1.6, { tone: "lo" }), lamp("router", 110, -69, 30, { r: 2.8 }), labelY("ROUTER · OFFERS", 74, RB.y + RB.d, 10, { px: 4.6 })].join("")));

  // envelope tray with fence
  const E = { x: -100, y: -36, w: 124, d: 104, r: 4 };
  const posts = [];
  for (const x of [E.x + 3, E.x + E.w / 2, E.x + E.w - 3]) for (const y of [E.y + 3, E.y + E.d / 2, E.y + E.d - 3]) if (!(x === E.x + E.w / 2 && y === E.y + E.d / 2)) posts.push([x, y]);
  const post = ([x, y]) => [cyl(x, y, 1.9, 6, 13, { tone: "mid", steps: 16 }), cyl(x, y, 2.5, 19, 1.4, { tone: "mid", steps: 16 })].join("");
  const railX = (y) => box({ x: E.x + 3, y: y - 0.7, w: E.w - 6, d: 1.4, r: 0.4 }, 15, 1.6, { tone: "lo", bevel: 0 });
  const railY = (x) => box({ x: x - 0.7, y: E.y + 3, w: 1.4, d: E.d - 6, r: 0.4 }, 15, 1.6, { tone: "lo", bevel: 0 });
  const backPosts = posts.filter(([x, y]) => y === E.y + 3 || x === E.x + 3).sort((a, b) => a[0] + a[1] - b[0] - b[1]);
  const frontPosts = posts.filter((p) => !backPosts.includes(p)).sort((a, b) => a[0] + a[1] - b[0] - b[1]);
  out.push(hot("envelope", [box(E, 0, 6, { tone: "mid", bevel: 0.8 }), L(k.planOutline(k.insetPlan(E, 6), 6, P), { tone: "faint" }), ...backPosts.map(post), railX(E.y + 3), railY(E.x + 3)].join("")));
  // sockets: three admitted markets
  const MK = [["m0", "EURUSD · HOME", -72, -14], ["m1", "GBPUSD", -6, -14], ["m2", "XAUUSD", -72, 36]];
  for (const [id, name, x, y] of MK) out.push(hot(id, [socket(B, id, x, y, 6, { r: 8 }), labelTop(name, x + 2, y - 13, 6, { px: 3.8 })].join("")));
  // sessions + broker plate
  out.push(hot("envelope", [box({ x: -30, y: 26, w: 40, d: 20, r: 1.5 }, 6, 3, { tone: "lo" }), labelTop("LDN · NY", -10, 32.5, 9, { px: 3.6 }), labelTop("IC · CTRADER", -10, 40, 9, { px: 3.2 })].join("")));
  // the unit, wired to its sockets
  const U = { x: -50, y: 8, w: 30, d: 20, r: 2 };
  out.push(B.wire([-62, -14, 7.2], [-50, 14, 10], [[-58, -2, 7.2], [-58, 14, 7.2]], { tone: "lo" }));
  out.push(hot("unit", unitBlock(B, U, 6)));
  out.push(hot("envelope", [...frontPosts.map(post), railX(E.y + E.d - 3), railY(E.x + E.w - 3)].join("")));
  out.push(labelY("ENVELOPE · ADMITTED", E.x + 40, E.y + E.d, 0.8, { px: 4.4 }));

  // paper tray outside
  const T = { x: 48, y: -36, w: 76, d: 104, r: 4 };
  out.push(hot("paper", [box(T, 0, 5, { tone: "lo", bevel: 0.6 }), L(k.planOutline(k.insetPlan(T, 5), 5, P), { tone: "faint" }), socket(B, "nas", 70, -14, 5, { r: 8 }), labelTop("NAS100", 72, -1, 5, { px: 3.8 }), labelY("OUTSIDE · PAPER ONLY", T.x + T.w / 2, T.y + T.d, 0.6, { px: 4 })].join("")));
  out.push(show("sib", hot("sib", `<g data-cls="sibc">${unitBlock(B, { x: 64, y: 12, w: 26, d: 18, r: 2 }, 5, { h: 10 })}</g>`)));
  out.push(show("prop", hot("prop", cardY(B, { x: 96, y: 40, z: 5, w: 22, h: 20, text: "PROPOSAL", px: 3.2, lines: 3 }))));

  // the offer card (drawn last so it flies over everything)
  const C0 = { x: 64, y: -71, z: 31.6 };
  out.push(show("offer", hot("offer", move("offer", cardY(B, { x: C0.x, y: C0.y, z: C0.z, w: 18, h: 13, text: "OFFER", px: 3, lines: 2 }), [0, 0, 0]))));
  const to = (x, y) => [x - (C0.x + 9), y - C0.y - 6, 6 + 1.4 - C0.z];
  const toGBP = to(-6, -14), toNAS = to(70, -14);

  const svg = svgOf(B, { label: "A key lock marked 'your click', a fenced tray marked 'envelope' holding the unit and three market sockets (EURUSD home, GBPUSD, gold) plus a sessions and broker plate, a paper-only tray outside the fence with a NAS100 socket, and a router offer board at the back. An offer card travels from the board to a socket.", body: out });
  const labels = { lock: "Your click. The only thing that admits a unit to live.", envelope: "The envelope: the markets, sessions and brokers your click covers.", m0: "Home market: never the router's to give or take.", m1: "GBPUSD: inside the envelope.", m2: "Gold: inside the envelope.", unit: "The unit. Its own conditions decide every trade.", router: "Router: publishes offers that expire. Never switches.", offer: "An offer: market, session, why, grade, expiry.", paper: "Outside the envelope: paper only, never live.", sib: "A paper sibling: the same logic on the new market.", prop: "A proposal card. Your click decides." };
  const base = { lamps: { admit: "off", router: "off", m0: "off", m1: "off", m2: "off", nas: "off" }, move: { key: [0, 0, 9], offer: [0, 0, 0] }, show: { offer: false, sib: false, prop: false }, cls: { sibc: "" } };
  const walk = [
    { say: "Your click admits a unit. Nothing else can.", lit: ["lock"], move: { key: [0, 0, 0] }, lamps: { admit: "ok" }, ms: 3000 },
    { say: "With it you tick an envelope: markets, sessions, brokers.", lit: ["envelope"], lamps: { m0: "ok", m1: "ok", m2: "ok" }, ms: 3000 },
    { say: "Inside, the unit trades on its own conditions.", lit: ["unit", "m0"], ms: 2800 },
    { say: "The router offers: GBPUSD fits this London session.", lit: ["router", "offer"], lamps: { router: "ok" }, show: { offer: true }, ms: 3000 },
    { say: "Inside the envelope it is live advice. The unit still decides.", lit: ["offer", "m1"], move: { offer: toGBP }, ms: 3200 },
    { say: "Next offer: NAS100. It sits outside the envelope.", lit: ["offer", "paper"], move: { offer: toNAS }, lamps: { nas: "warn" }, ms: 3200 },
    { say: "Outside, it never trades live: a paper sibling plus a proposal for you.", lit: ["sib", "prop"], show: { sib: true, prop: true }, cls: { sibc: "warn" }, ms: 3600 },
    { say: "Only your click can widen the envelope.", lit: ["lock", "prop"], ms: 2800 },
  ];
  const off = (say2, lampsOn, extra = {}) => [
    { say: "The router goes down. Its lamp goes dark.", lit: ["router"], move: { key: [0, 0, 0] }, lamps: { admit: "ok", router: "off", m0: "ok", m1: "ok", m2: "ok" }, show: { offer: false }, ms: 2600 },
    { say: say2, lit: lampsOn, lamps: { m0: "ok", m1: lampsOn.includes("m1") ? "ok" : "off", m2: lampsOn.includes("m2") ? "ok" : "off" }, ...extra, ms: 3600 },
  ];
  const modes = {
    walk,
    home: off("Option a: the unit trades its home market only.", ["m0"]),
    env: off("Option b: the whole envelope, on the unit's own conditions.", ["m0", "m1", "m2"]),
    last: [...off("Option c: it follows its last offers until they expire.", ["m0", "m1"], { show: { offer: true }, move: { offer: toGBP } }), { say: "The GBPUSD offer expires. Back to the home market.", lit: ["m0"], show: { offer: false }, lamps: { m1: "off" }, ms: 3200 }],
  };
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.55 };
}
