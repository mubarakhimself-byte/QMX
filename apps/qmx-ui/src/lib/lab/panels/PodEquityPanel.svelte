<script lang="ts">
  /**
   * Equity of the ticked pods on the same bots and years. "Run together"
   * replaces the old Allocate tab (operator, 2026-10-03): split one pot of
   * money across the ticked pods and see the combined curve next to each
   * pod alone. It is an experiment; a saved mix goes to paper like a pod.
   */
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Save from "@lucide/svelte/icons/save";
  import { Button } from "$lib/components/ui/button";
  import { Slider } from "$lib/components/ui/slider";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import { cn } from "$lib/utils";
  import { usd } from "$lib/portfolio/bits";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PODS, POD_EQUITY, TEST_BOTS } from "../pods";
  import { lab } from "../lab.svelte";

  const POT = 20000;
  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  const weight = (id: string) => lab.mix[id] ?? 0;
  const total = $derived(pods.reduce((t, p) => t + weight(p.id), 0) || 1);
  const share = (id: string) => weight(id) / total;

  const combined = $derived(
    POD_EQUITY.classic.map((_, i) =>
      pods.reduce((v, p) => v + share(p.id) * POD_EQUITY[p.id][i], 0),
    ),
  );
  function dip(values: number[]) {
    let peak = values[0];
    let worst = 0;
    for (const v of values) {
      peak = Math.max(peak, v);
      worst = Math.max(worst, (peak - v) / peak);
    }
    return worst * 100;
  }
  const togetherDip = $derived(dip(combined));
  const bestAlone = $derived(
    Math.min(...pods.map((p) => dip(POD_EQUITY[p.id]))),
  );
  const gain = (values: number[]) => values[values.length - 1] / values[0] - 1;

  const series = $derived(
    lab.together && pods.length > 1
      ? [
          {
            label: "Together",
            values: combined,
            color: "var(--primary)",
          },
          ...pods.map((p) => ({
            label: p.name,
            values: POD_EQUITY[p.id],
            color: p.color,
            dashed: true,
          })),
        ]
      : pods.map((p) => ({
          label: p.name,
          values: POD_EQUITY[p.id],
          color: p.color,
        })),
  );
  const bots = $derived(
    TEST_BOTS.filter((b) => lab.botsTicked.includes(b.id))
      .map((b) => b.name)
      .join(", "),
  );

  function preset(kind: "equal" | "risk") {
    // Equal risk: weight by the inverse of each pod's own deepest dip.
    for (const p of pods)
      lab.mix[p.id] =
        kind === "equal" ? 50 : Math.round(500 / dip(POD_EQUITY[p.id]));
  }
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-2 border-b px-2 text-xs">
    <div class="bg-muted flex rounded-md p-0.5" role="radiogroup">
      {#each [false, true] as t (t)}
        <button
          type="button"
          role="radio"
          aria-checked={lab.together === t}
          class={cn(
            "h-6 rounded px-2.5",
            lab.together === t
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground",
          )}
          onclick={() => (lab.together = t)}
          >{t ? "Run together" : "Each pod"}</button
        >
      {/each}
    </div>
    <span class="text-muted-foreground ml-auto truncate"
      >{bots || "No bots ticked"} · 2022–2025</span
    >
  </div>

  {#if lab.together}
    <div class="shrink-0 border-b px-3 py-2">
      <p class="text-sm">
        What if {usd(POT)} were split across these pods?
      </p>
      <div
        class="mt-2 flex h-6 overflow-hidden rounded-md"
        aria-label="How the money is split"
      >
        {#each pods as p (p.id)}
          <span
            class="num flex items-center justify-center overflow-hidden text-[11px] font-medium text-white"
            style="width:{share(p.id) * 100}%; background:{p.color}"
            title={`${p.name}: ${usd(share(p.id) * POT)}`}
            >{Math.round(share(p.id) * 100)}%</span
          >
        {/each}
      </div>
      <div
        class="mt-2 grid gap-x-4 gap-y-1"
        style="grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr))"
      >
        {#each pods as p (p.id)}
          <label class="flex items-center gap-2 text-xs">
            <span class="w-24 truncate">{p.name}</span>
            <Slider
              type="single"
              class="flex-1"
              min={0}
              max={100}
              step={5}
              value={weight(p.id)}
              onValueChange={(v: number) => (lab.mix[p.id] = v)}
              aria-label={`${p.name} share`}
            />
          </label>
        {/each}
      </div>
      <div class="mt-2 flex flex-wrap items-center gap-1.5">
        <Button size="sm" variant="outline" onclick={() => preset("equal")}
          >Equal money</Button
        >
        <Button size="sm" variant="outline" onclick={() => preset("risk")}
          >Equal risk</Button
        >
        <Button
          size="sm"
          variant="ghost"
          onclick={() =>
            lab.ask(
              "Suggest how to split $20,000 across the ticked pods so the deepest dip stays under 8%, and show how much the split moves across the years.",
            )}><Sparkles />Ask the copilot</Button
        >
        <Button
          size="sm"
          class="ml-auto"
          onclick={() =>
            workbench.notify(
              "Saved as a mix. A mix goes to paper like a pod before any real money is split.",
            )}><Save />Save mix</Button
        >
      </div>
    </div>
  {/if}

  <div class="min-h-0 flex-1 p-3">
    {#if pods.length}
      <LineChart {series} height={200} />
    {:else}
      <p class="text-muted-foreground text-sm">
        Tick pods in Pod resources to see them here.
      </p>
    {/if}
  </div>

  {#if lab.together && pods.length > 1}
    <div class="grid shrink-0 grid-cols-2 gap-2 border-t px-3 py-2 text-sm">
      <p>
        <span class="text-muted-foreground block text-xs">Together</span>
        <span class="num font-semibold"
          >{(gain(combined) * 100).toFixed(0)}% gain · −{togetherDip.toFixed(
            1,
          )}% deepest dip</span
        >
      </p>
      <p>
        <span class="text-muted-foreground block text-xs"
          >Calmest pod alone</span
        >
        <span class="num font-semibold"
          >−{bestAlone.toFixed(1)}% deepest dip</span
        >
      </p>
    </div>
  {/if}
</div>
