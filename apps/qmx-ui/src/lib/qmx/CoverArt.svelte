<script lang="ts" module>
  import type { EntityKind } from "./entities";

  /** Duotone per kind: saturated ground, light ink (Hermes / print-plate look). */
  export const DUOTONE: Record<EntityKind, { ground: string; ink: string }> = {
    bot: { ground: "#2430e8", ink: "#e9ebff" },
    model: { ground: "#16924c", ink: "#eafff1" },
    app: { ground: "#c9831a", ink: "#fff6e6" },
    workflow: { ground: "#6a35d8", ink: "#f2ebff" },
  };
</script>

<script lang="ts">
  /**
   * Generated cover art for an entity. Deterministic: the same entity always
   * draws the same plate. Bots and models draw their own series as a
   * halftone; workflows draw their step graph; apps draw their views.
   */
  let {
    kind,
    seed,
    series,
    steps = 0,
    tint,
    class: className = "",
  }: {
    kind: EntityKind;
    seed: string;
    series?: number[];
    steps?: number;
    /** Ground colour by family (e.g. scalpers gold), overriding the kind's. */
    tint?: string;
    class?: string;
  } = $props();

  const W = 320;
  const H = 140;

  function hash(s: string) {
    let h = 2166136261;
    for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
    return h >>> 0;
  }
  function rng(n: number) {
    let s = n;
    return () => {
      s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  const art = $derived.by(() => {
    const r = rng(hash(seed));
    const pts =
      series && series.length > 1
        ? series
        : Array.from(
            { length: 48 },
            (_, i) => 50 + Math.sin(i / 5 + r() * 2) * 18 + r() * 8,
          );
    const min = Math.min(...pts);
    const max = Math.max(...pts);
    const yAt = (x: number) => {
      const t = (x / W) * (pts.length - 1);
      const i = Math.floor(t);
      const f = t - i;
      const v =
        pts[i] * (1 - f) + (pts[Math.min(i + 1, pts.length - 1)] ?? pts[i]) * f;
      return H - 18 - ((v - min) / (max - min || 1)) * (H - 40);
    };
    // Halftone: dot size falls off with distance below the curve.
    const dots: { x: number; y: number; r: number }[] = [];
    const step = 7;
    for (let x = step / 2; x < W; x += step) {
      const cy = yAt(x);
      for (let y = step / 2; y < H; y += step) {
        const d = y - cy;
        let rad = 0;
        if (d >= 0) rad = Math.max(0, 2.9 - d / 22);
        else if (d > -10) rad = 1.2;
        if (kind === "model") {
          const dx = x - W * 0.72;
          const dy = y - H * 0.42;
          const ring = Math.abs(Math.sin(Math.hypot(dx, dy) / 9));
          rad = Math.max(rad * 0.6, ring > 0.85 ? 1.6 : 0);
        }
        if (rad > 0.25) dots.push({ x, y, r: rad });
      }
    }
    const line = Array.from({ length: 81 }, (_, i) => {
      const x = (i / 80) * W;
      return `${i ? "L" : "M"}${x.toFixed(1)},${yAt(x).toFixed(1)}`;
    }).join(" ");
    // Workflow: a small node chain; app: a tile grid.
    const count = Math.max(steps, 3);
    const nodes = Array.from({ length: count }, (_, i) => ({
      x: 34 + (i * (W - 68)) / (count - 1),
      y: 40 + (i % 2) * 34 + r() * 12,
    }));
    const tiles = Array.from({ length: 6 }, (_, i) => ({
      x: 196 + (i % 3) * 38,
      y: 26 + Math.floor(i / 3) * 38,
      o: 0.35 + r() * 0.55,
    }));
    return { dots, line, nodes, tiles };
  });
  const tone = $derived(
    tint ? { ground: tint, ink: DUOTONE[kind].ink } : DUOTONE[kind],
  );
</script>

<svg
  viewBox="0 0 {W} {H}"
  preserveAspectRatio="xMidYMid slice"
  class="block {className}"
  role="img"
  aria-label="Generated cover"
>
  <rect width={W} height={H} fill={tone.ground} />
  <g fill={tone.ink} opacity="0.9">
    {#each art.dots as d, i (i)}<circle cx={d.x} cy={d.y} r={d.r} />{/each}
  </g>
  {#if kind === "bot" || kind === "model"}
    <path d={art.line} fill="none" stroke={tone.ink} stroke-width="1.6" />
  {/if}
  {#if kind === "workflow"}
    <path
      d={art.nodes.map((n, i) => `${i ? "L" : "M"}${n.x},${n.y}`).join(" ")}
      fill="none"
      stroke={tone.ink}
      stroke-width="1.4"
      stroke-dasharray="4 3"
    />
    {#each art.nodes as n, i (i)}
      <rect
        x={n.x - 12}
        y={n.y - 8}
        width="24"
        height="16"
        rx="3"
        fill={tone.ground}
        stroke={tone.ink}
        stroke-width="1.4"
      />
    {/each}
  {/if}
  {#if kind === "app"}
    {#each art.tiles as t, i (i)}
      <rect
        x={t.x}
        y={t.y}
        width="32"
        height="32"
        rx="4"
        fill={tone.ink}
        opacity={t.o}
      />
    {/each}
  {/if}
  <!-- Print-plate scanlines -->
  <g stroke={tone.ground} stroke-width="1" opacity="0.35">
    {#each Array.from({ length: Math.ceil(H / 3) }) as _, i (i)}
      <line x1="0" x2={W} y1={i * 3 + 1.5} y2={i * 3 + 1.5} />
    {/each}
  </g>
</svg>
