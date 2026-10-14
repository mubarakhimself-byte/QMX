<script lang="ts">
  /**
   * Stress board: crises down the side, pods across. Each cell: worst loss,
   * how much of the room to the kill line it used, and which guard fired.
   * Your own scenarios sit beside the built-in ones (operator, 2026-10-03:
   * "I'll add my own with the copilot"); a new one shows "Run" until tested.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import History from "@lucide/svelte/icons/history";
  import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { usd } from "$lib/portfolio/bits";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PODS, MY_STRESS, STRESS } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  const rows = $derived(
    [
      ...STRESS.map((s) => ({ ...s, mine: false })),
      ...MY_STRESS.map((s) => ({ ...s, mine: true })),
    ].filter((s) => lab.stressTicked.includes(s.id)),
  );
  const size = panelSize();
  /** Compact summary: the cell that used the most room. */
  const worst = $derived(
    rows
      .flatMap((s) =>
        pods.map((p) => ({ s, p, c: podModel.stress(p.id, s.id) })),
      )
      .filter((x) => x.c)
      .sort((a, b) => b.c!.ofRoom - a.c!.ofRoom)[0],
  );
  const tone = (r: number) =>
    `color-mix(in oklab, ${r >= 0.75 ? "var(--destructive)" : r >= 0.4 ? "var(--warning)" : "var(--success)"} ${Math.round(14 + r * 30)}%, transparent)`;
</script>

{#if size.mode === "compact"}
  <div class="p-panel flex h-full flex-col justify-end gap-1">
    {#if worst}
      <p class="text-muted-foreground truncate text-xs">
        Worst: {worst.s.name}
      </p>
      <p class="num truncate text-2xl font-semibold">{usd(worst.c!.loss)}</p>
      <p class="text-muted-foreground truncate text-xs">
        <span class="num">{Math.round(worst.c!.ofRoom * 100)}%</span> of room ·
        {worst.p.name}
      </p>
    {:else}
      <p class="text-muted-foreground text-sm">Nothing run yet</p>
    {/if}
  </div>
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2 text-xs">
      <span class="text-muted-foreground">{rows.length} scenarios</span>
      <InfoTip
        label="Explain the stress colours"
        text="Each cell is the worst loss in that crisis and how much of the room to the kill line it used: green under 40%, amber to 75%, red above. A red border means the pod stood down. Cells follow the pod's settings in Design."
      />
      <DropdownMenu.Root>
        <DropdownMenu.Trigger
          class="hover:bg-muted ml-auto flex h-7 items-center gap-1 rounded-md border px-2"
          ><Plus class="size-3.5" />Scenario</DropdownMenu.Trigger
        >
        <DropdownMenu.Content align="end" class="w-72">
          <DropdownMenu.Item
            onclick={() =>
              lab.ask(
                "Build a stress scenario: BTC drops 15% in an hour while Binance pauses withdrawals for 6 hours.",
              )}><Sparkles />Describe it to the copilot</DropdownMenu.Item
          >
          <DropdownMenu.Item
            onclick={() =>
              workbench.notify(
                "Pick dates on the chart; the test replays that stretch of real prices through every pod.",
              )}><History />Replay real dates</DropdownMenu.Item
          >
          <DropdownMenu.Item
            onclick={() =>
              workbench.notify(
                "Set the shocks yourself: price move, speed, spread, outage length, stablecoin price.",
              )}><SlidersHorizontal />Set the shocks by hand</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </div>
    <div class="px-panel pb-panel min-h-0 flex-1 overflow-auto">
      <div
        class="grid gap-1"
        style="grid-template-columns: minmax(0, 1.3fr) repeat({pods.length}, minmax(0, 1fr))"
      >
        <span></span>
        {#each pods as p (p.id)}
          <span
            class="flex min-w-0 items-center gap-1.5 px-1 text-xs font-medium"
            ><span
              class="size-2 shrink-0 rounded-full"
              style="background:{p.color}"
            ></span><span class="truncate">{p.name}</span></span
          >
        {/each}
        {#each rows as s (s.id)}
          <span class="min-w-0 self-center truncate text-sm" title={s.name}
            >{#if s.mine}<span class="text-info mr-1 text-xs">Yours</span
              >{/if}{s.name}</span
          >
          {#each pods as p (p.id)}
            {@const c = podModel.stress(p.id, s.id)}
            {#if c}
              <button
                type="button"
                class={cn(
                  "min-w-0 rounded-md border px-2 py-1 text-left",
                  c.stoodDown && "border-destructive",
                )}
                title={`${s.name} under ${p.name}: ${c.stoodDown ? "stood down, " : ""}${c.fired}`}
                style="background:{tone(c.ofRoom)}"
                onclick={() => (lab.labPod = p.id)}
              >
                <span
                  class="flex flex-wrap items-baseline justify-between gap-x-2"
                >
                  <span class="num font-semibold">{usd(c.loss)}</span>
                  <span
                    class="num text-xs"
                    title={`${Math.round(c.ofRoom * 100)}% of the room to the kill line`}
                    >{Math.round(c.ofRoom * 100)}%</span
                  >
                </span>
                {#if size.mode === "expanded"}
                  <span
                    class={cn(
                      "block truncate text-xs",
                      c.stoodDown
                        ? "text-destructive"
                        : "text-muted-foreground",
                    )}>{c.stoodDown ? "Stood down: " : ""}{c.fired}</span
                  >
                {/if}
              </button>
            {:else}
              <button
                type="button"
                class="text-muted-foreground hover:text-foreground hover:border-ring/60 rounded-md border border-dashed px-2 py-1 text-left text-xs"
                aria-label={`Run ${s.name} through ${p.name}`}
                onclick={() => podModel.run(p.id, s.id)}>Run</button
              >
            {/if}
          {/each}
        {/each}
      </div>
    </div>
  </div>
{/if}
