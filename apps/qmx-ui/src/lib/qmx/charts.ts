/** Small geometry helpers shared by the SVG charts. */

export function extent(values: number[]): [number, number] {
  let lo = Infinity;
  let hi = -Infinity;
  for (const v of values) {
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  return lo === hi ? [lo - 1, hi + 1] : [lo, hi];
}

/** Path for a series scaled into a w×h box with optional shared y-domain. */
export function linePath(
  values: number[],
  w: number,
  h: number,
  domain?: [number, number],
  pad = 4,
): string {
  const [lo, hi] = domain ?? extent(values);
  return values
    .map((v, i) => {
      const x = (i / Math.max(values.length - 1, 1)) * w;
      const y = pad + (1 - (v - lo) / (hi - lo)) * (h - pad * 2);
      return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

/** Closed band between two series (e.g. Monte Carlo p5–p95). */
export function bandPath(
  lower: number[],
  upper: number[],
  w: number,
  h: number,
  domain: [number, number],
  pad = 4,
): string {
  const [lo, hi] = domain;
  const pt = (v: number, i: number, n: number) => {
    const x = (i / Math.max(n - 1, 1)) * w;
    const y = pad + (1 - (v - lo) / (hi - lo)) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  };
  const top = upper.map((v, i) => `${i ? "L" : "M"}${pt(v, i, upper.length)}`);
  const bottom = lower.map((v, i) => `L${pt(v, i, lower.length)}`).reverse();
  return `${top.join(" ")} ${bottom.join(" ")} Z`;
}

export function seeded(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

/** A random-walk equity curve starting at 100. */
export function equityWalk(
  seed: number,
  n: number,
  drift: number,
  vol = 0.012,
): number[] {
  const r = seeded(seed);
  let v = 100;
  return Array.from({ length: n }, () => {
    v *= 1 + (r() - 0.5) * 2 * vol + drift;
    return v;
  });
}
