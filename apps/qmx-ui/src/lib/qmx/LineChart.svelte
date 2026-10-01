<script lang="ts">
  /** Several series on one shared y-axis, with a legend. Pure SVG. */
  import { extent, linePath } from "./charts";

  type Series = {
    label: string;
    values: number[];
    color: string;
    dashed?: boolean;
  };
  let {
    series,
    height = 180,
    band,
  }: {
    series: Series[];
    height?: number;
    /** Optional shaded band path already in chart coordinates. */
    band?: { path: string; color: string };
  } = $props();

  const W = 600;
  const domain = $derived(extent(series.flatMap((s) => s.values)));
</script>

<div class="flex h-full flex-col gap-1.5">
  <svg
    viewBox="0 0 {W} {height}"
    preserveAspectRatio="none"
    class="w-full flex-1"
    style="min-height: {height * 0.6}px"
    role="img"
    aria-label={series.map((s) => s.label).join(", ")}
  >
    {#each [0.25, 0.5, 0.75] as g (g)}
      <line
        x1="0"
        x2={W}
        y1={g * height}
        y2={g * height}
        stroke="var(--border)"
        stroke-width="1"
        vector-effect="non-scaling-stroke"
      />
    {/each}
    {#if band}<path d={band.path} fill={band.color} opacity="0.18" />{/if}
    {#each series as s (s.label)}
      <path
        d={linePath(s.values, W, height, domain)}
        fill="none"
        stroke={s.color}
        stroke-width="1.8"
        stroke-dasharray={s.dashed ? "5 4" : undefined}
        vector-effect="non-scaling-stroke"
      />
    {/each}
  </svg>
  <div class="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-xs">
    {#each series as s (s.label)}
      <span class="flex items-center gap-1.5">
        <span class="h-0.5 w-4 rounded" style="background: {s.color}"
        ></span>{s.label}
      </span>
    {/each}
  </div>
</div>
