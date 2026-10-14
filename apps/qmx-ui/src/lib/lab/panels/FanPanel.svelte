<script lang="ts">
  /**
   * Drawdown fan over 90 days from 1,000 resampled paths, each pod under its
   * current Design settings. Bands are the 5th–95th percentile; each pod's
   * kill line is dashed in its colour; the headline is the chance of
   * hitting it.
   */
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { LAB_PODS } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const W = 600;
  const H = 220;
  const size = panelSize();
  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  const fans = $derived(pods.map((p) => ({ p, f: podModel.fan(p.id) })));
  const depth = $derived(
    Math.max(
      26,
      ...fans
        .map(({ f }) => Math.max(f.kill, -Math.min(...f.p95)))
        .map((d) => d * 1.1),
    ),
  );
  const y = (v: number) => (-v / depth) * H;
  const x = (i: number, n: number) => (i / (n - 1)) * W;
  const band = (f: { p5: number[]; p95: number[] }) => {
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
  const mid = (f: { p50: number[] }) =>
    f.p50
      .map(
        (v, i) =>
          `${i ? "L" : "M"}${x(i, f.p50.length).toFixed(1)},${y(v).toFixed(1)}`,
      )
      .join("");
  const working = $derived(
    fans.find(({ p }) => p.id === lab.labPod) ?? fans[0],
  );
</script>

{#if !fans.length}
  <div
    class="text-muted-foreground p-panel flex h-full items-center justify-center text-sm"
  >
    No pods ticked
  </div>
{:else if size.mode === "compact"}
  <PanelSummary
    label={`Kill-line risk · ${working.p.name}`}
    value={`${working.f.pKill}%`}
    status={`within 90 days · kill −${working.f.kill}%`}
    tone={working.f.pKill >= 5 ? "bad" : working.f.pKill >= 2 ? "warn" : "good"}
  />
{:else}
  <div class="flex h-full flex-col">
    <div
      class="px-panel gap-x-group flex shrink-0 flex-wrap items-start gap-y-2 py-2"
    >
      {#each fans as { p, f } (p.id)}
        <div class="min-w-0">
          <p class="flex items-center gap-1.5 text-xs">
            <span
              class="size-2 shrink-0 rounded-full"
              style="background:{p.color}"
            ></span><span class="truncate">{p.name}</span>
          </p>
          <p class="num text-xl font-semibold">{f.pKill}%</p>
        </div>
      {/each}
      <InfoTip
        class="ml-auto"
        label="Explain the drawdown fan"
        text="Chance of hitting each pod's kill line (dashed, in its colour) within 90 days, from 1,000 resampled paths. Bands are the 5th to 95th percentile of drawdown. Follows each pod's settings in Design. Robustness only, not proof of profit."
      />
    </div>
    <div class="solid-backing px-panel pb-panel min-h-0 flex-1">
      <svg
        viewBox="0 -10 {W} {H + 20}"
        preserveAspectRatio="none"
        class="h-full min-h-20 w-full"
        role="img"
        aria-label="Drawdown fan per pod"
      >
        <line x1="0" x2={W} y1="0" y2="0" stroke="var(--border)" />
        {#each fans as { p, f } (p.id)}
          <line
            x1="0"
            x2={W}
            y1={y(-f.kill)}
            y2={y(-f.kill)}
            stroke={p.color}
            stroke-dasharray="6 4"
            opacity="0.8"
            vector-effect="non-scaling-stroke"
          />
          <path d={band(f)} fill={p.color} opacity="0.14" />
          <path
            d={mid(f)}
            fill="none"
            stroke={p.color}
            stroke-width="2"
            vector-effect="non-scaling-stroke"
          />
        {/each}
      </svg>
    </div>
  </div>
{/if}
