// Shared isometric parts for the QMX unit-system site.
// Every figure builds a "bench" from these helpers, then wraps parts in
// data-hot (tap/hover target), data-move (eased mover), data-lamp (state lamp),
// data-dial (needle) and data-show (can be hidden by a scene).
import * as k from "file:///C:/Users/Mubarak/.claude/skills/anatomy/kit/iso-kit.mjs";

export { k };

export function bench(points, { width = 400, height = 0, pad = 12, azimuth = 45, elevation = 30 } = {}) {
  let P = k.fitProjection(points, width, height || 2000, { pad, azimuth, elevation });
  if (!height) {
    const ys = points.map((p) => k.iso(p, P)[1]);
    const top = Math.min(...ys), bottom = Math.max(...ys);
    height = Math.ceil(bottom - top + pad * 2);
    P = { ...P, origin: [P.origin[0], P.origin[1] - top + pad] };
  }
  const K = P.scale * Math.sqrt(1.6);
  const at = (p) => k.iso(p, P);
  const S = (paths, o = {}) => k.solidSvg(paths, o);
  const L = (d, o = {}) => k.lineSvg(d, o);
  const D = (pts, o = {}) => k.dotsSvg(pts.map(at), o);
  const byDepth = (pts) => [...pts].sort((a, b) => k.depthOf([a[0], a[1], a[2] || 0], P) - k.depthOf([b[0], b[1], b[2] || 0], P));
  // world font size for a wanted viewBox px glyph height on a vertical face
  const fs = (px) => px / (0.866 * K) / 0.72;

  const box = (plan, z, h, o = {}) => S(k.slabOf(plan, z, h, P, o.steps ?? 4, o.bevel ?? 0.5), { tone: o.tone ?? "mid", crease: o.crease, lit: o.lit, inner: o.inner });
  const cyl = (x, y, r, z, h, o = {}) => S(k.cylinder(x, y, r, z, h, P, o.steps ?? 28, o.bevel ?? 0), { tone: o.tone ?? "mid", crease: o.crease, lit: o.lit, inner: o.inner });

  function base(plan, { h = 8, feet = true, screws = true, groove = true } = {}) {
    const z0 = -h - (feet ? 4 : 0);
    const out = [`<path class="iso-halo" d="${k.haloOf(plan, z0, h, P)}"/>`];
    if (feet) {
      for (const [x, y] of byDepth(k.corners(plan, Math.min(18, plan.w / 6)))) {
        out.push(cyl(x, y, 5.5, z0, 1.4, { tone: "lo", steps: 24 }));
        out.push(cyl(x, y, 4.2, z0 + 1.4, 2.6, { tone: "mid", steps: 24 }));
      }
    }
    out.push(S(k.slabOf(plan, -h, h, P, 8, 1.2), { tone: "mid" }));
    if (groove) out.push(L(k.planOutline(k.insetPlan(plan, 4), 0, P), { tone: "faint" }));
    if (screws) {
      const sc = k.corners(plan, 8);
      out.push(L(sc.map(([x, y]) => k.ring(x, y, 1.9, 0, P, 14)).join(""), { tone: "lo" }));
      out.push(D(sc.map(([x, y]) => [x, y, 0]), { size: 0.5 }));
    }
    return out.join("");
  }

  // label plate on the +y face (front-left) of a part: centre x, face y, bottom z
  function labelY(text, cx, y, z, { px = 11, w, h, tone = "hi", plate = true } = {}) {
    const s = fs(px);
    const tw = text.length * s * 0.62;
    const W = w ?? tw + s * 1.2;
    const H = h ?? s * 1.35;
    const out = [];
    if (plate) out.push(S(k.slabOf({ x: cx - W / 2, y, w: W, d: 0.7, r: 0.2 }, z, H, P, 2), { tone: "lo", crease: "none" }));
    const zt = z + (H - s * 0.72) / 2;
    out.push(k.faceTextSvg(k.sideMatrix([cx, y + (plate ? 0.7 : 0.05)], zt, P, "left"), text, { size: s.toFixed(2), tone, anchor: "middle" }));
    return out.join("");
  }
  // label plate on the +x face (front-right): face x, centre y, bottom z
  function labelX(text, x, cy, z, { px = 11, w, h, tone = "hi", plate = true } = {}) {
    const s = fs(px);
    const tw = text.length * s * 0.62;
    const W = w ?? tw + s * 1.2;
    const H = h ?? s * 1.35;
    const out = [];
    if (plate) out.push(S(k.slabOf({ x, y: cy - W / 2, w: 0.7, d: W, r: 0.2 }, z, H, P, 2), { tone: "lo", crease: "none" }));
    const zt = z + (H - s * 0.72) / 2;
    out.push(k.faceTextSvg(k.sideMatrix([x + (plate ? 0.7 : 0.05), cy], zt, P, "right"), text, { size: s.toFixed(2), tone, anchor: "middle" }));
    return out.join("");
  }
  // flat text on a top face (reads along +x)
  function labelTop(text, cx, cy, z, { px = 7, tone = "hi" } = {}) {
    const s = fs(px) * 0.95;
    return k.faceTextSvg(k.topMatrix([cx, cy], z + 0.05, P, "x"), text, { size: s.toFixed(2), tone, anchor: "middle" });
  }
  // text that a scene can rewrite (counter windows): same as labelY without plate
  function liveY(id, text, cx, y, z, { px = 11, tone = "hi" } = {}) {
    const s = fs(px);
    return k.faceTextSvg(k.sideMatrix([cx, y + 0.05], z, P, "left"), text, { size: s.toFixed(2), tone, anchor: "middle" }).replace("<text ", `<text data-text="${id}" `);
  }

  // a lamp on a top face
  function lamp(id, x, y, z, { r = 3 } = {}) {
    return `<g class="lamp" data-lamp="${id}">${cyl(x, y, r + 1.2, z, 1, { tone: "lo", steps: 24 })}${cyl(x, y, r, z + 1, 1.8, { tone: "mid", steps: 24 })}</g>`;
  }
  // a lamp seen on a +y face: a short horizontal stub is impossible, so a dome-ish puck on a bracket
  const screws = (pts) => D(pts, { size: 0.45 });

  // a dial lying face-up; the needle is a data-dial path the client rebuilds
  function dial(id, cx, cy, r, z, { h = 4, value = 0, from = -0.75 * Math.PI, span = 1.5 * Math.PI, ticks = 30, every = 5 } = {}) {
    const top = z + h;
    const out = [cyl(cx, cy, r, z, h, { tone: "hi", crease: "lo", steps: 48, bevel: 0.6 })];
    out.push(L(k.ring(cx, cy, r - 1.6, top, P, 48), { tone: "lo" }));
    const t = k.radialTicks(cx, cy, r - 2.2, ticks, every, top, [1, 2.2], P, from + Math.PI / 2 * 0, span);
    out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
    out.push(L(k.ring(cx, cy, 1.2, top, P, 14), { tone: "mid" }));
    const a = from + span * value;
    out.push(`<path class="iso-line qx-needle" data-tone="lit" data-free="start" data-dial="${id}" d="${needle(cx, cy, r, top, a)}"/>`);
    return { svg: out.join(""), spec: { cx, cy, r, z: top, from, span, value } };
  }
  function needle(cx, cy, r, z, a) {
    // radialTicks: angle 0 points to -y, clockwise from above
    return k.lineOnTop([cx - Math.sin(a) * 2.2, cy + Math.cos(a) * 2.2], [cx + Math.sin(a) * (r - 3), cy - Math.cos(a) * (r - 3)], z + 0.2, P);
  }

  const hot = (id, svg, extra = "") => `<g data-hot="${id}"${extra}>${svg}</g>`;
  const move = (id, svg, at0 = [0, 0, 0]) => `<g data-move="${id}" data-at="${at0.join(",")}" transform="${k.translateAlong(P, at0)}">${svg}</g>`;
  const show = (id, svg) => `<g data-show="${id}">${svg}</g>`;
  const wire = (a, b, via = [], o = {}) => k.wireSvg(at(a), at(b), { via: via.map(at), tone: o.tone ?? "lo", ends: o.ends ?? "both", size: o.size ?? 1.1, flow: o.flow });

  return { P, K, width, height, at, S, L, D, k, byDepth, fs, box, cyl, base, labelY, labelX, labelTop, liveY, lamp, screws, dial, needle, hot, move, show, wire };
}

export function svgOf(B, { label, body, width = B.width, height = B.height }) {
  return k.figureSvg({ width, height, label, body: Array.isArray(body) ? body.join("") : body });
}
