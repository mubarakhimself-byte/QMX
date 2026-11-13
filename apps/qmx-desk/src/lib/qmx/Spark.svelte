<script lang="ts">
  // A line with a soft fill. Its colour comes from the frame: live, paper or neutral.
  let { series, note }: { series: number[]; note?: string } = $props();
  const W = 600;
  const H = 200;
  const path = $derived.by(() => {
    const min = Math.min(...series);
    const max = Math.max(...series);
    const span = max - min || 1;
    return series
      .map((v, i) => `${i ? "L" : "M"}${((i / (series.length - 1)) * W).toFixed(1)},${(H - 8 - ((v - min) / span) * (H - 16)).toFixed(1)}`)
      .join(" ");
  });
  const id = $props.id();
</script>

<div class="flex h-full min-h-0 flex-col gap-2 p-2.5">
  <svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" class="min-h-24 w-full flex-1 text-[var(--line,var(--foreground))]">
    <defs>
      <linearGradient id="g{id}" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0" stop-color="currentColor" stop-opacity="0.22" />
        <stop offset="1" stop-color="currentColor" stop-opacity="0" />
      </linearGradient>
    </defs>
    <path d="{path} L{W},{H} L0,{H} Z" fill="url(#g{id})" />
    <path d={path} fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round" />
  </svg>
  {#if note}
    <p class="text-muted-foreground num line-clamp-2 text-sm" title={note}>{note}</p>
  {/if}
</div>
