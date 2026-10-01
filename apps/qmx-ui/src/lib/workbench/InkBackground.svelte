<script lang="ts">
  /**
   * Decorative ink map behind the workbench: layered fractal price paths
   * (fractional-Brownian midpoint displacement), an ink wash and grain.
   * Colours come from the theme (--ink, --glow). Purely visual; hidden on
   * trading surfaces so nothing competes with live prices.
   */
  const W = 1600;
  const H = 1000;

  function rng(seed: number) {
    let s = seed >>> 0;
    return () => {
      s = (s * 1664525 + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  /** Midpoint displacement: a self-similar path like a price series. */
  function fractalPath(seed: number, base: number, amp: number, hurst = 0.62) {
    const r = rng(seed);
    const n = 256;
    const ys = new Array<number>(n + 1).fill(0);
    ys[0] = base + (r() - 0.5) * amp;
    ys[n] = base + (r() - 0.5) * amp;
    let step = n;
    let scale = amp;
    while (step > 1) {
      const half = step / 2;
      for (let i = half; i < n; i += step) {
        ys[i] = (ys[i - half] + ys[i + half]) / 2 + (r() - 0.5) * scale;
      }
      step = half;
      scale *= Math.pow(0.5, hurst);
    }
    return ys
      .map(
        (y, i) =>
          `${i === 0 ? "M" : "L"}${((i / n) * W).toFixed(1)},${y.toFixed(1)}`,
      )
      .join(" ");
  }

  const layers = Array.from({ length: 16 }, (_, k) => ({
    d: fractalPath(11 + k * 7, 120 + k * 52, 120 + k * 6),
    o: 0.05 + (k % 4) * 0.025,
  }));
  const main = fractalPath(4, 560, 420, 0.55);
  const area = `${main} L${W},${H} L0,${H} Z`;
</script>

<svg
  class="pointer-events-none fixed inset-0 -z-10 h-full w-full"
  viewBox="0 0 {W} {H}"
  preserveAspectRatio="xMidYMid slice"
  aria-hidden="true"
>
  <defs>
    <radialGradient id="ink-glow" cx="68%" cy="30%" r="60%">
      <stop offset="0" style="stop-color: var(--glow); stop-opacity: 0.5" />
      <stop offset="1" style="stop-color: var(--glow); stop-opacity: 0" />
    </radialGradient>
    <linearGradient id="ink-area" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" style="stop-color: var(--ink); stop-opacity: 0.14" />
      <stop offset="1" style="stop-color: var(--ink); stop-opacity: 0" />
    </linearGradient>
    <filter id="ink-wash" x="0" y="0" width="100%" height="100%">
      <feTurbulence
        type="fractalNoise"
        baseFrequency="0.006 0.012"
        numOctaves="4"
        seed="7"
      />
      <feColorMatrix
        type="matrix"
        values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.5 1.05"
      />
      <feComposite in="SourceGraphic" operator="in" />
    </filter>
    <filter id="ink-grain">
      <feTurbulence
        type="fractalNoise"
        baseFrequency="0.85"
        numOctaves="2"
        seed="3"
      />
      <feColorMatrix
        type="matrix"
        values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"
      />
    </filter>
  </defs>
  <rect width={W} height={H} fill="url(#ink-glow)" />
  <rect
    width={W}
    height={H}
    style="fill: var(--ink); opacity: 0.16"
    filter="url(#ink-wash)"
  />
  {#each layers as l, i (i)}
    <path
      d={l.d}
      fill="none"
      style="stroke: var(--ink); opacity: {l.o}"
      stroke-width="1"
    />
  {/each}
  <path d={area} fill="url(#ink-area)" />
  <path
    d={main}
    fill="none"
    style="stroke: var(--ink); opacity: 0.45"
    stroke-width="1.4"
  />
  <rect width={W} height={H} filter="url(#ink-grain)" />
</svg>
