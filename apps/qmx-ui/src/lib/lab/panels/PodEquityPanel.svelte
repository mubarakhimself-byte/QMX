<script lang="ts">
  /**
   * Equity of the ticked pods on the same bots and years. "Run together"
   * (operator, 2026-10-03) splits one pot across them and draws the combined
   * curve. Worked example of DESIGN-RULES.md: compact is a summary, regular
   * the chart and figures with the split behind one button, expanded the
   * split controls in the open.
   */
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Save from "@lucide/svelte/icons/save";
  import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Slider } from "$lib/components/ui/slider";
  import * as Popover from "$lib/components/ui/popover";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { cn } from "$lib/utils";
  import { pct, usd } from "$lib/portfolio/bits";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PODS, TEST_BOTS } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const size = panelSize();

  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  const weight = (id: string) => lab.mix[id] ?? 0;
  const total = $derived(pods.reduce((t, p) => t + weight(p.id), 0) || 1);
  const share = (id: string) => weight(id) / total;
  const together = $derived(lab.together && pods.length > 1);

  /** Each pod's test curve under its current Design settings. */
  const curves = $derived(
    Object.fromEntries(pods.map((p) => [p.id, podModel.equity(p.id).curve])),
  );
  const combined = $derived(
    (curves[pods[0]?.id] ?? []).map((_, i) =>
      pods.reduce((v, p) => v + share(p.id) * curves[p.id][i], 0),
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
  const gain = (values: number[]) =>
    (values[values.length - 1] / values[0] - 1) * 100;

  type Row = {
    id: string;
    name: string;
    color: string;
    values: number[];
    share?: number;
  };
  const rows = $derived<Row[]>([
    ...(together
      ? [
          {
            id: "together",
            name: "Together",
            color: "var(--primary)",
            values: combined,
            share: 1,
          },
        ]
      : []),
    ...pods.map((p) => ({
      id: p.id,
      name: p.name,
      color: p.color,
      values: curves[p.id],
      share: together ? share(p.id) : undefined,
    })),
  ]);
  const series = $derived(
    rows.map((r) => ({
      label: r.name,
      values: r.values,
      color: r.color,
      dashed: together && r.id !== "together",
    })),
  );
  /** Compact headline: the combined curve, or the best pod alone. */
  const headline = $derived(
    together
      ? rows[0]
      : [...rows].sort((a, b) => gain(b.values) - gain(a.values))[0],
  );
  const botCount = $derived(
    TEST_BOTS.filter((b) => lab.botsTicked.includes(b.id)).length,
  );

  function preset(kind: "equal" | "risk") {
    // Equal risk: weight by the inverse of each pod's own deepest dip.
    for (const p of pods)
      lab.mix[p.id] =
        kind === "equal" ? 50 : Math.round(500 / dip(curves[p.id]));
  }
</script>

{#snippet modeToggle()}
  <div
    class="bg-muted flex max-w-full shrink-0 rounded-md p-0.5 text-xs"
    role="radiogroup"
    aria-label="Show"
  >
    {#each [false, true] as t (t)}
      <button
        type="button"
        role="radio"
        aria-checked={lab.together === t}
        class={cn(
          "h-6 min-w-0 truncate rounded px-2.5",
          lab.together === t
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground",
        )}
        onclick={() => (lab.together = t)}
        >{#if size.mode === "compact"}{t ? "Together" : "Each"}{:else}{t
            ? "Run together"
            : "Each pod"}{/if}</button
      >
    {/each}
  </div>
{/snippet}

{#snippet splitControls()}
  <div class="gap-group flex flex-col">
    <label class="flex items-center justify-between gap-3 text-sm">
      <span>Pot</span>
      <span class="flex items-center gap-1">
        <span class="text-muted-foreground">$</span>
        <Input
          type="number"
          min={100}
          step={1000}
          class="num h-8 w-28 text-right"
          bind:value={lab.pot}
          aria-label="Money to split"
        />
      </span>
    </label>
    <ul class="gap-row flex flex-col">
      {#each pods as p (p.id)}
        <li
          class="py-row grid grid-cols-[minmax(0,7rem)_1fr_3rem] items-center gap-3 text-sm"
        >
          <span class="flex min-w-0 items-center gap-2">
            <span
              class="size-2 shrink-0 rounded-full"
              style="background:{p.color}"
            ></span>
            <span class="truncate">{p.name}</span>
          </span>
          <Slider
            type="single"
            min={0}
            max={100}
            step={5}
            value={weight(p.id)}
            onValueChange={(v: number) => (lab.mix[p.id] = v)}
            aria-label={`${p.name} share`}
          />
          <span class="num text-right">{Math.round(share(p.id) * 100)}%</span>
        </li>
      {/each}
    </ul>
    <div class="flex flex-wrap gap-2">
      <Button size="sm" variant="outline" onclick={() => preset("equal")}
        >Equal money</Button
      >
      <Button size="sm" variant="outline" onclick={() => preset("risk")}
        >Equal risk</Button
      >
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <Button
        size="sm"
        variant="ghost"
        onclick={() =>
          lab.ask(
            `Suggest how to split ${usd(lab.pot)} across the ticked pods so the deepest dip stays under 8%, and show how much the split moves across the years.`,
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
{/snippet}

{#snippet figures()}
  <table class="w-full text-sm" aria-label="Pod results">
    <thead class="text-muted-foreground text-xs">
      <tr>
        <th class="py-row text-left font-normal">{together ? "Mix" : "Pod"}</th>
        {#if together && size.mode === "expanded"}<th
            class="py-row text-right font-normal">Share</th
          >{/if}
        {#if size.mode === "expanded"}<th class="py-row text-right font-normal"
            >Ends at</th
          >{/if}
        <th class="py-row text-right font-normal">Gain</th>
        <th class="py-row pl-4 text-right font-normal">Deepest dip</th>
      </tr>
    </thead>
    <tbody>
      {#each rows as r (r.id)}
        <tr class={cn("border-t", r.id === "together" && "font-semibold")}>
          <td class="py-row">
            <span class="flex min-w-0 items-center gap-2">
              <span
                class="w-3 shrink-0 border-t-2"
                style="border-color:{r.color}; border-top-style:{together &&
                r.id !== 'together'
                  ? 'dashed'
                  : 'solid'}"
              ></span>
              <span class="truncate">{r.name}</span>
            </span>
          </td>
          {#if together && size.mode === "expanded"}<td
              class="num py-row text-right"
              >{Math.round((r.share ?? 0) * 100)}%</td
            >{/if}
          {#if size.mode === "expanded"}
            <td class="num py-row text-right"
              >{usd(lab.pot * (1 + gain(r.values) / 100))}</td
            >
          {/if}
          <td class="num py-row text-right">{pct(gain(r.values), 0)}</td>
          <td class="num py-row pl-4 text-right"
            >−{dip(r.values).toFixed(1)}%</td
          >
        </tr>
      {/each}
    </tbody>
  </table>
{/snippet}

{#if !pods.length}
  <div
    class="text-muted-foreground p-panel flex h-full items-center justify-center text-sm"
  >
    No pods ticked
  </div>
{:else if size.mode === "compact"}
  <div class="gap-row p-panel flex h-full flex-col items-start">
    {@render modeToggle()}
    <div class="mt-auto w-full min-w-0">
      <p class="text-muted-foreground truncate text-xs">{headline.name}</p>
      <p class="num truncate text-2xl font-semibold">
        {pct(gain(headline.values), 0)}
      </p>
      <p class="num text-muted-foreground text-xs">
        −{dip(headline.values).toFixed(1)}% dip
      </p>
    </div>
    <Sparkline values={headline.values} class="h-8 w-full shrink-0" />
  </div>
{:else}
  <div class="flex h-full min-h-0">
    <div class="flex min-w-0 flex-1 flex-col">
      <div class="px-panel flex h-11 shrink-0 items-center gap-3">
        {@render modeToggle()}
        <span class="text-muted-foreground truncate text-xs">
          {botCount} bots · 2022–2025
        </span>
        <span class="ml-auto flex items-center gap-1">
          {#if together && size.mode === "regular"}
            <Popover.Root>
              <Popover.Trigger>
                {#snippet child({ props })}
                  <Button {...props} size="sm" variant="outline"
                    ><SlidersHorizontal />Split</Button
                  >
                {/snippet}
              </Popover.Trigger>
              <Popover.Content align="end" class="w-96">
                {@render splitControls()}
              </Popover.Content>
            </Popover.Root>
          {/if}
          <InfoTip
            label="Explain pod equity"
            text="Equity of the ticked pods over the same bots and years. Run together splits one pot across them: the solid line is the mix, dashed lines are each pod alone. A saved mix goes to paper like a pod before any real money is split."
          />
        </span>
      </div>
      {#if together}
        <div class="px-panel pb-row flex shrink-0" aria-hidden="true">
          {#each pods as p, i (p.id)}
            <span
              class={cn(
                "h-1.5",
                i === 0 && "rounded-l-full",
                i === pods.length - 1 && "rounded-r-full",
              )}
              style="width:{share(p.id) * 100}%; background:{p.color}"
            ></span>
          {/each}
        </div>
      {/if}
      <div
        class={cn(
          "px-panel pt-row pb-panel gap-panel flex min-h-0 flex-1",
          size.mode === "expanded" ? "flex-col" : "flex-row",
        )}
      >
        <div class="min-h-0 min-w-0 flex-1">
          <LineChart {series} height={160} legend={false} />
        </div>
        <div
          class={cn(
            "shrink-0",
            size.mode === "regular" ? "w-[17rem]" : "max-w-4xl",
          )}
        >
          {@render figures()}
        </div>
      </div>
    </div>
    {#if together && size.mode === "expanded"}
      <aside
        class="p-panel w-96 shrink-0 overflow-auto border-l"
        aria-label="Split the pot"
      >
        <h4 class="mb-panel text-sm font-medium">Split {usd(lab.pot)}</h4>
        {@render splitControls()}
      </aside>
    {/if}
  </div>
{/if}
