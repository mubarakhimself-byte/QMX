<script lang="ts">
  /**
   * Drawdown fan over 90 days from 1,000 resampled paths, the pod running
   * inside every path. Bands are the 5th–95th percentile; the kill line is
   * drawn; the headline is the chance of hitting it.
   */
  import { FAN, LAB_PODS } from "../pods";
  import { lab } from "../lab.svelte";

  const W = 600;
  const H = 220;
  const KILL = -20;
  const y = (v: number) => (-v / 26) * H;
  const x = (i: number, n: number) => (i / (n - 1)) * W;
  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  const band = (f: (typeof FAN)[string]) => {
    const n = f.p5.length;
    const top = f.p5
      .map((v, i) => `${i ? "L" : "M"}${x(i, n).toFixed(1)},${y(v).toFixed(1)}`)
      .join("");
    const bot = [...f.p95]
      .reverse()
      .map((v, i) => `L${x(n - 1 - i, n).toFixed(1)},${y(v).toFixed(1)}`)
      .join("");
    return `${top}${bot}Z`;
  };
  const mid = (f: (typeof FAN)[string]) =>
    f.p50
      .map(
        (v, i) =>
          `${i ? "L" : "M"}${x(i, f.p50.length).toFixed(1)},${y(v).toFixed(1)}`,
      )
      .join("");
</script>

<div class="flex h-full flex-col">
  <div class="flex shrink-0 flex-wrap gap-4 border-b px-3 py-2">
    {#each pods as p (p.id)}
      <div>
        <p class="flex items-center gap-1.5 text-xs">
          <span class="size-2 rounded-full" style="background:{p.color}"
          ></span>{p.name}
        </p>
        <p class="num text-xl font-semibold">{FAN[p.id].pKill}%</p>
        <p class="text-muted-foreground text-[11px]">chance of the kill line</p>
      </div>
    {/each}
  </div>
  <div class="solid-backing min-h-0 flex-1 p-2">
    <svg
      viewBox="0 -10 {W} {H + 20}"
      preserveAspectRatio="none"
      class="h-full w-full"
      role="img"
      aria-label="Drawdown fan per pod"
    >
      <line x1="0" x2={W} y1="0" y2="0" stroke="var(--border)" />
      <line
        x1="0"
        x2={W}
        y1={y(KILL)}
        y2={y(KILL)}
        stroke="var(--destructive)"
        stroke-dasharray="6 4"
        vector-effect="non-scaling-stroke"
      />
      {#each pods as p (p.id)}
        <path d={band(FAN[p.id])} fill={p.color} opacity="0.14" />
        <path
          d={mid(FAN[p.id])}
          fill="none"
          stroke={p.color}
          stroke-width="2"
          vector-effect="non-scaling-stroke"
        />
      {/each}
    </svg>
  </div>
  <p class="text-muted-foreground border-t px-3 py-1.5 text-xs">
    Dashed red: kill line at −20%. Bands: 5th–95th percentile of drawdown.
    Robustness only, not proof of profit.
  </p>
</div>
