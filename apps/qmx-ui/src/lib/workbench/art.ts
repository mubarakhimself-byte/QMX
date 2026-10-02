/**
 * Background art for the workbench. Each style turns a small config into a
 * scene of SVG paths (strokes and fills) drawn in the theme's ink colour.
 * Pure functions so a config always draws the same picture, and presets
 * stay a few numbers rather than an image.
 */

export const W = 1600;
export const H = 1000;

export const ART_STYLES = [
  { id: "fractal", label: "Fractal", note: "Self-similar price walks" },
  {
    id: "contour",
    label: "Contours",
    note: "Topographic lines of a price surface",
  },
  { id: "candles", label: "Candles", note: "A faded candlestick tape" },
  {
    id: "halftone",
    label: "Halftone",
    note: "A printed dot screen of a curve",
  },
  { id: "liquidity", label: "Liquidity", note: "Order-book heat bands" },
] as const;
export type ArtStyle = (typeof ART_STYLES)[number]["id"];

export const GLOWS = ["left", "center", "right", "off"] as const;
export type Glow = (typeof GLOWS)[number];

export type ArtConfig = {
  style: ArtStyle;
  seed: number;
  /** 0.5 (sparse) to 2 (dense). */
  density: number;
  /** 0.3 (faint) to 1.6 (bold). */
  strength: number;
  glow: Glow;
};

export type ArtPreset = { id: string; name: string; config: ArtConfig };

export const DEFAULT_ART: ArtConfig = {
  style: "fractal",
  seed: 4,
  density: 1,
  strength: 1,
  glow: "right",
};

export const BUILTIN_PRESETS: ArtPreset[] = [
  { id: "b-ink", name: "Ink map", config: DEFAULT_ART },
  {
    id: "b-survey",
    name: "Survey",
    config: {
      style: "contour",
      seed: 21,
      density: 1,
      strength: 0.9,
      glow: "left",
    },
  },
  {
    id: "b-tape",
    name: "Old tape",
    config: {
      style: "candles",
      seed: 9,
      density: 1,
      strength: 0.8,
      glow: "right",
    },
  },
  {
    id: "b-print",
    name: "Print",
    config: {
      style: "halftone",
      seed: 13,
      density: 1.1,
      strength: 1,
      glow: "center",
    },
  },
  {
    id: "b-book",
    name: "Depth",
    config: {
      style: "liquidity",
      seed: 5,
      density: 1,
      strength: 0.9,
      glow: "off",
    },
  },
];

const clamp = (v: number, lo: number, hi: number) =>
  Math.min(hi, Math.max(lo, v));

/** Accept anything (stored JSON, a copilot edit) and return a valid config. */
export function parseArt(raw: unknown): ArtConfig {
  const o = (raw && typeof raw === "object" ? raw : {}) as Record<
    string,
    unknown
  >;
  const num = (v: unknown, d: number) =>
    typeof v === "number" && Number.isFinite(v) ? v : d;
  return {
    style: ART_STYLES.some((s) => s.id === o.style)
      ? (o.style as ArtStyle)
      : DEFAULT_ART.style,
    seed: Math.round(clamp(num(o.seed, DEFAULT_ART.seed), 0, 99999)),
    density: clamp(num(o.density, 1), 0.5, 2),
    strength: clamp(num(o.strength, 1), 0.3, 1.6),
    glow: GLOWS.includes(o.glow as Glow) ? (o.glow as Glow) : DEFAULT_ART.glow,
  };
}

export function parsePresets(raw: unknown): ArtPreset[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter(
      (p): p is { id: string; name: string; config: unknown } =>
        !!p &&
        typeof p === "object" &&
        typeof (p as ArtPreset).id === "string" &&
        typeof (p as ArtPreset).name === "string",
    )
    .slice(0, 24)
    .map((p) => ({
      id: p.id,
      name: p.name.slice(0, 40),
      config: parseArt(p.config),
    }));
}

export function rng(seed: number) {
  let s = seed >>> 0 || 1;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

/** Midpoint displacement: n+1 values of a self-similar walk. */
export function fractalSeries(
  seed: number,
  n: number,
  base: number,
  amp: number,
  hurst = 0.6,
): number[] {
  const r = rng(seed);
  let size = 1;
  while (size < n) size *= 2;
  const ys = new Array<number>(size + 1).fill(0);
  ys[0] = base + (r() - 0.5) * amp;
  ys[size] = base + (r() - 0.5) * amp;
  let step = size;
  let scale = amp;
  while (step > 1) {
    const half = step / 2;
    for (let i = half; i < size; i += step) {
      ys[i] = (ys[i - half] + ys[i + half]) / 2 + (r() - 0.5) * scale;
    }
    step = half;
    scale *= Math.pow(0.5, hurst);
  }
  return Array.from(
    { length: n + 1 },
    (_, i) => ys[Math.round((i / n) * size)],
  );
}

/** Smooth 2D value noise with a few octaves, roughly in 0..1. */
function noise2(seed: number) {
  const r = rng(seed);
  const perm = Array.from({ length: 512 }, () => r());
  const at = (x: number, y: number) =>
    perm[(((x * 73856093) ^ (y * 19349663)) >>> 0) % 512];
  const smooth = (t: number) => t * t * (3 - 2 * t);
  const one = (x: number, y: number) => {
    const x0 = Math.floor(x);
    const y0 = Math.floor(y);
    const tx = smooth(x - x0);
    const ty = smooth(y - y0);
    const a = at(x0, y0) + (at(x0 + 1, y0) - at(x0, y0)) * tx;
    const b = at(x0, y0 + 1) + (at(x0 + 1, y0 + 1) - at(x0, y0 + 1)) * tx;
    return a + (b - a) * ty;
  };
  return (x: number, y: number) => {
    let v = 0;
    let amp = 0.5;
    let f = 1;
    for (let o = 0; o < 4; o++) {
      v += one(x * f, y * f) * amp;
      amp *= 0.5;
      f *= 2;
    }
    return v / 0.9375;
  };
}

const f1 = (v: number) => v.toFixed(1);
const line = (pts: [number, number][]) =>
  pts.map(([x, y], i) => `${i ? "L" : "M"}${f1(x)},${f1(y)}`).join("");

export type Stroke = { d: string; o: number; w: number };
export type Fill = { d: string; o: number };
export type ArtScene = { strokes: Stroke[]; fills: Fill[] };

function fractalScene(c: ArtConfig): ArtScene {
  const count = Math.round(16 * c.density);
  const strokes: Stroke[] = Array.from({ length: count }, (_, k) => {
    const ys = fractalSeries(
      c.seed + 11 + k * 7,
      256,
      120 + (k * 830) / count,
      120 + k * 6,
      0.62,
    );
    return {
      d: line(ys.map((y, i) => [(i / 256) * W, y])),
      o: 0.05 + (k % 4) * 0.025,
      w: 1,
    };
  });
  const main = line(
    fractalSeries(c.seed, 256, 560, 420, 0.55).map((y, i) => [
      (i / 256) * W,
      y,
    ]),
  );
  strokes.push({ d: main, o: 0.45, w: 1.4 });
  return { strokes, fills: [{ d: `${main}L${W},${H}L0,${H}Z`, o: 0.07 }] };
}

/** Marching squares over a noise field shaped by a price ridge. */
function contourScene(c: ArtConfig): ArtScene {
  const n = noise2(c.seed);
  const ridge = fractalSeries(c.seed + 3, 64, 0.5, 0.5, 0.5);
  const cols = 96;
  const rows = 60;
  const cw = W / cols;
  const ch = H / rows;
  const field: number[][] = [];
  for (let j = 0; j <= rows; j++) {
    const row: number[] = [];
    for (let i = 0; i <= cols; i++) {
      const ry = ridge[Math.round((i / cols) * 64)];
      const d = j / rows - ry;
      row.push(n(i * 0.06, j * 0.06) * 0.7 + Math.exp(-d * d * 18) * 0.6);
    }
    field.push(row);
  }
  const SEG: Record<number, [number, number][]> = {
    1: [[3, 2]],
    2: [[2, 1]],
    3: [[3, 1]],
    4: [[0, 1]],
    5: [
      [3, 0],
      [2, 1],
    ],
    6: [[0, 2]],
    7: [[3, 0]],
    8: [[3, 0]],
    9: [[0, 2]],
    10: [
      [0, 1],
      [3, 2],
    ],
    11: [[0, 1]],
    12: [[3, 1]],
    13: [[2, 1]],
    14: [[3, 2]],
  };
  const levels = Math.round(14 * c.density);
  const strokes: Stroke[] = [];
  for (let l = 1; l <= levels; l++) {
    const lv = 0.15 + (l / (levels + 1)) * 0.95;
    let d = "";
    for (let j = 0; j < rows; j++) {
      for (let i = 0; i < cols; i++) {
        const tl = field[j][i];
        const tr = field[j][i + 1];
        const br = field[j + 1][i + 1];
        const bl = field[j + 1][i];
        const k =
          (tl > lv ? 8 : 0) |
          (tr > lv ? 4 : 0) |
          (br > lv ? 2 : 0) |
          (bl > lv ? 1 : 0);
        const segs = SEG[k];
        if (!segs) continue;
        const t = (a: number, b: number) => (lv - a) / (b - a || 1e-6);
        const x = i * cw;
        const y = j * ch;
        const edge = (e: number): [number, number] =>
          e === 0
            ? [x + t(tl, tr) * cw, y]
            : e === 1
              ? [x + cw, y + t(tr, br) * ch]
              : e === 2
                ? [x + t(bl, br) * cw, y + ch]
                : [x, y + t(tl, bl) * ch];
        for (const [a, b] of segs) {
          const [ax, ay] = edge(a);
          const [bx, by] = edge(b);
          d += `M${f1(ax)},${f1(ay)}L${f1(bx)},${f1(by)}`;
        }
      }
    }
    if (d)
      strokes.push({
        d,
        o: l % 4 === 0 ? 0.3 : 0.13,
        w: l % 4 === 0 ? 1.3 : 0.9,
      });
  }
  return { strokes, fills: [] };
}

function candleScene(c: ArtConfig): ArtScene {
  const count = Math.round(84 * c.density);
  const r = rng(c.seed + 1);
  const closes = fractalSeries(c.seed, count, 520, 520, 0.5);
  const step = W / count;
  const body = step * 0.58;
  let wicks = "";
  let up = "";
  let down = "";
  let vol = "";
  const ma: [number, number][] = [];
  for (let i = 1; i <= count; i++) {
    const o = closes[i - 1];
    const cl = closes[i];
    const hi = Math.min(o, cl) - r() * step * 0.9;
    const lo = Math.max(o, cl) + r() * step * 0.9;
    const x = (i - 0.5) * step;
    wicks += `M${f1(x)},${f1(hi)}L${f1(x)},${f1(lo)}`;
    const top = Math.min(o, cl);
    const h = Math.max(2, Math.abs(o - cl));
    const rect = `M${f1(x - body / 2)},${f1(top)}h${f1(body)}v${f1(h)}h${f1(-body)}Z`;
    if (cl < o) up += rect;
    else down += rect;
    const vh = 20 + r() * 90 + Math.abs(o - cl) * 0.6;
    vol += `M${f1(x - body / 2)},${f1(H - vh)}h${f1(body)}v${f1(vh)}h${f1(-body)}Z`;
    const win = closes.slice(Math.max(0, i - 12), i + 1);
    ma.push([x, win.reduce((a, b) => a + b, 0) / win.length]);
  }
  return {
    strokes: [
      { d: wicks, o: 0.3, w: 1 },
      { d: down, o: 0.35, w: 1 },
      { d: line(ma), o: 0.4, w: 1.6 },
    ],
    fills: [
      { d: up, o: 0.22 },
      { d: vol, o: 0.06 },
    ],
  };
}

function halftoneScene(c: ArtConfig): ArtScene {
  const n = noise2(c.seed + 7);
  const curve = fractalSeries(c.seed, 128, 520, 460, 0.55);
  const gap = 22 / c.density;
  const maxR = gap * 0.46;
  let d = "";
  for (let y = gap / 2; y < H; y += gap) {
    for (let x = gap / 2; x < W; x += gap) {
      const cy = curve[Math.round((x / W) * 128)];
      const below = y - cy;
      const band =
        below < 0 ? Math.exp(below / 30) : 1 - Math.min(1, below / 520);
      const v = band * (0.55 + n(x * 0.004, y * 0.004) * 0.6);
      const rad = maxR * Math.min(1, v);
      if (rad < 0.6) continue;
      d += `M${f1(x - rad)},${f1(y)}a${f1(rad)},${f1(rad)} 0 1,0 ${f1(rad * 2)},0a${f1(rad)},${f1(rad)} 0 1,0 ${f1(-rad * 2)},0`;
    }
  }
  const main = line(curve.map((y, i) => [(i / 128) * W, y]));
  return { strokes: [{ d: main, o: 0.4, w: 1.4 }], fills: [{ d, o: 0.2 }] };
}

/** Bookmap-style heat: horizontal liquidity bands over time, price on top. */
function liquidityScene(c: ArtConfig): ArtScene {
  const n = noise2(c.seed);
  const cols = Math.round(72 * c.density);
  const rows = Math.round(56 * c.density);
  const cw = W / cols;
  const ch = H / rows;
  const price = fractalSeries(c.seed + 5, cols, 500, 420, 0.5);
  const buckets = ["", "", "", "", ""];
  for (let i = 0; i < cols; i++) {
    for (let j = 0; j < rows; j++) {
      const y = (j + 0.5) * ch;
      const dist = Math.abs(y - price[i]) / H;
      let v = Math.pow(n(i * 0.025, j * 0.3), 2.2) * 1.6;
      v *= 0.55 + Math.exp(-dist * dist * 40) * 0.8;
      const b = Math.min(4, Math.floor(v * 5));
      if (v < 0.2) continue;
      buckets[b] +=
        `M${f1(i * cw)},${f1(j * ch)}h${f1(cw + 0.5)}v${f1(ch - 1)}h${f1(-cw - 0.5)}Z`;
    }
  }
  const fills = buckets
    .map((d, b) => ({ d, o: 0.04 + b * 0.05 }))
    .filter((f) => f.d);
  const path = line(price.map((y, i) => [(i + 0.5) * cw, y]));
  return { strokes: [{ d: path, o: 0.5, w: 1.6 }], fills };
}

const BUILDERS: Record<ArtStyle, (c: ArtConfig) => ArtScene> = {
  fractal: fractalScene,
  contour: contourScene,
  candles: candleScene,
  halftone: halftoneScene,
  liquidity: liquidityScene,
};

export function buildScene(c: ArtConfig): ArtScene {
  return BUILDERS[c.style](c);
}

export const GLOW_X: Record<Glow, string> = {
  left: "24%",
  center: "50%",
  right: "70%",
  off: "50%",
};
