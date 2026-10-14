<script lang="ts">
  /** Why this size: one sample trade walked through the pod being designed, a bar per block. Follows every edit in Design. */
  import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";
  import { Button } from "$lib/components/ui/button";
  import { Slider } from "$lib/components/ui/slider";
  import { Switch } from "$lib/components/ui/switch";
  import * as Popover from "$lib/components/ui/popover";
  import { usd } from "$lib/portfolio/bits";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { SAMPLE, podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const size = panelSize();
  const trail = $derived(podModel.trail(lab.labPod));
  const max = $derived(Math.max(...trail.map((s) => s.usd), 1));
  const last = $derived(trail[trail.length - 1]);
  const money = (v: number) => usd(v, v % 1 ? 2 : 0);
</script>

{#snippet market()}
  <div class="gap-row flex flex-col text-sm">
    <div class="grid grid-cols-[minmax(0,8rem)_1fr_3.5rem] items-center gap-3">
      <span>Under its peak</span>
      <Slider
        type="single"
        min={0}
        max={25}
        step={1}
        value={podModel.sample.dip}
        onValueChange={(v: number) => (podModel.sample.dip = v)}
        aria-label="How far the pod is under its peak"
      />
      <span class="num text-right">−{podModel.sample.dip}%</span>
    </div>
    <label class="flex items-center justify-between gap-3">
      <span>Weekend</span>
      <Switch
        checked={podModel.sample.weekend}
        onCheckedChange={(v: boolean) => (podModel.sample.weekend = v)}
        aria-label="Weekend"
      />
    </label>
  </div>
{/snippet}

{#if size.mode === "compact"}
  <PanelSummary
    label="Sample trade size"
    value={money(last.usd)}
    status={`from ${money(trail[0].usd)} · ${trail.length} steps`}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      <span class="text-muted-foreground truncate text-xs"
        >{SAMPLE.bot} · buy {SAMPLE.entry.toLocaleString("en-US")}, stop {SAMPLE.stop.toLocaleString(
          "en-US",
        )}</span
      >
      <span class="ml-auto flex items-center gap-1">
        {#if size.mode === "regular"}
          <Popover.Root>
            <Popover.Trigger>
              {#snippet child({ props })}
                <Button {...props} size="sm" variant="outline"
                  ><SlidersHorizontal />Market</Button
                >
              {/snippet}
            </Popover.Trigger>
            <Popover.Content align="end" class="w-80">
              {@render market()}
            </Popover.Content>
          </Popover.Root>
        {/if}
        <InfoTip
          label="Explain the size trail"
          text="One trade on a $25,000 pod, block by block: the sizer sets a size and each throttle, cap and the exchange's lot size shrink it. It follows every change you make in Design."
        />
      </span>
    </div>
    <div
      class="px-panel pb-panel gap-group flex min-h-0 flex-1 overflow-auto"
      class:flex-col={size.mode !== "expanded"}
    >
      <ol class="gap-row flex min-w-0 flex-1 flex-col" aria-label="Size trail">
        {#each trail as s, i (i)}
          {@const prev = i ? trail[i - 1].usd : s.usd}
          <li class="grid grid-cols-[1fr_5.5rem] items-center gap-3">
            <div class="min-w-0">
              <p class="truncate text-sm">{s.step}</p>
              <div
                class="bg-muted relative mt-1 h-2 overflow-hidden rounded-sm"
              >
                <span
                  class="bg-destructive/30 absolute inset-y-0 left-0"
                  style="width:{(prev / max) * 100}%"
                ></span>
                <span
                  class="bg-primary absolute inset-y-0 left-0"
                  style="width:{(s.usd / max) * 100}%"
                ></span>
              </div>
            </div>
            <span class="num text-right">{money(s.usd)}</span>
          </li>
        {/each}
      </ol>
      {#if size.mode === "expanded"}
        <aside class="w-80 shrink-0" aria-label="Market">
          <h4 class="mb-row text-sm font-medium">Market</h4>
          {@render market()}
        </aside>
      {/if}
    </div>
  </div>
{/if}
