// Shared small parts for round 2 figures, built on round 1's bench().
export { bench, svgOf } from "../../src/parts.mjs";

// A unit: a bright block with a dial knob and a small knob, as on the round 1 hub.
export function unitBlock(B, U, z, { h = 14, cls } = {}) {
  const { box, cyl } = B;
  const body = [box(U, z, h, { tone: "hi", bevel: 0.6 }), cyl(U.x + U.w - Math.min(10, U.w / 3), U.y + U.d / 2, Math.min(4.6, U.d / 4.4), z + h, 2, { tone: "mid" }), cyl(U.x + Math.min(9, U.w / 4), U.y + U.d / 2, Math.min(3, U.d / 6), z + h, 3, { tone: "mid" })].join("");
  return cls ? `<g data-cls="${cls}">${body}</g>` : body;
}

// A thin standing card facing +y (front-left), with a title and rule lines.
export function cardY(B, { x, y, z, w, h, text, px = 3.4, lines = 2 }) {
  const { box, L, k, P, labelY } = B;
  const out = [box({ x, y, w, d: 1.6, r: 0.3 }, z, h, { tone: "hi", bevel: 0 })];
  if (text) out.push(labelY(text, x + w / 2, y, z + h - px * 1.9, { px, plate: false }));
  const fy = y + 1.65;
  if (lines) out.push(L(Array.from({ length: lines }, (_, i) => k.segment([x + 3, fy, z + h - px * 2.6 - 2.6 - i * 2.6], [x + w - 3 - i * 4, fy, z + h - px * 2.6 - 2.6 - i * 2.6], P)).join(""), { tone: "lo", free: true }));
  return out.join("");
}

// A book / ledger seen from above: covers, page block, seams, a label on its top.
export function ledger(B, R, z, { h = 12, text, px = 4.6 } = {}) {
  const { box, L, k, P, labelTop } = B;
  return [box(R, z, 2.5, { tone: "lo" }), box(k.insetPlan(R, 1.4), z + 2.5, h - 5, { tone: "hi", bevel: 0.3 }), L([0.35, 0.65].map((f) => k.sideSeam(k.insetPlan(R, 1.4), z + 2.5 + (h - 5) * f, P, 4)).join(""), { tone: "faint" }), box(R, z + h - 2.5, 2.5, { tone: "mid", bevel: 0.5 }), text ? labelTop(text, R.x + R.w / 2, R.y + R.d / 2, z + h, { px }) : ""].join("");
}

// A socket on a top face: ring, hole and a lamp beside it.
export function socket(B, id, cx, cy, z, { r = 7, lampAt } = {}) {
  const { cyl, L, k, P, lamp } = B;
  const [lx, ly] = lampAt || [cx + r + 6, cy];
  return [cyl(cx, cy, r, z, 1.2, { tone: "lo" }), L(k.ring(cx, cy, r * 0.55, z + 1.2, P, 20), { tone: "mid" }), L(k.ring(cx, cy, r * 0.2, z + 1.2, P, 10), { tone: "mid" }), lamp(id, lx, ly, z, { r: 2.6 })].join("");
}

// Scene helpers
export const reset = (ids, v) => Object.fromEntries(ids.map((i) => [i, v]));
