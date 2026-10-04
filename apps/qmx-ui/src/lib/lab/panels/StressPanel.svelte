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
  import { usd } from "$lib/portfolio/bits";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PODS, MY_STRESS, STRESS, STRESS_GRID } from "../pods";
  import { lab } from "../lab.svelte";

  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  const rows = $derived(
    [
      ...STRESS.map((s) => ({ ...s, mine: false })),
      ...MY_STRESS.map((s) => ({ ...s, mine: true })),
    ].filter((s) => lab.stressTicked.includes(s.id)),
  );
  const tone = (r: number) =>
    `color-mix(in oklab, ${r >= 0.75 ? "var(--destructive)" : r >= 0.4 ? "var(--warning)" : "var(--success)"} ${Math.round(14 + r * 30)}%, transparent)`;
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-2 border-b px-2 text-xs">
    <span class="text-muted-foreground"
      >Colour: how much of the room to the kill line the crisis used</span
    >
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
  <div class="min-h-0 flex-1 overflow-auto p-2">
    <div
      class="grid gap-1"
      style="grid-template-columns: minmax(9rem, 12rem) repeat({pods.length}, minmax(9rem, 1fr))"
    >
      <span></span>
      {#each pods as p (p.id)}
        <span class="flex items-center gap-1.5 px-1 text-xs font-medium"
          ><span class="size-2 rounded-full" style="background:{p.color}"
          ></span>{p.name}</span
        >
      {/each}
      {#each rows as s (s.id)}
        <span class="self-center text-sm"
          >{s.name}{#if s.mine}<span class="text-info block text-xs"
              >Yours</span
            >{/if}</span
        >
        {#each pods as p (p.id)}
          {@const c = STRESS_GRID[p.id]?.[s.id]}
          {#if c}
            <button
              type="button"
              class={cn(
                "rounded-md border px-2 py-1.5 text-left",
                c.stoodDown && "border-destructive",
              )}
              style="background:{tone(c.ofRoom)}"
              onclick={() =>
                workbench.notify(
                  `Replay of ${s.name} under ${p.name} opens at the shock (needs the daemon).`,
                )}
            >
              <span class="flex items-baseline justify-between gap-2">
                <span class="num font-semibold">{usd(c.loss)}</span>
                <span class="num text-xs"
                  >{Math.round(c.ofRoom * 100)}% of room</span
                >
              </span>
              <span
                class={cn(
                  "block truncate text-xs",
                  c.stoodDown ? "text-destructive" : "text-muted-foreground",
                )}>{c.stoodDown ? "Stood down: " : ""}{c.fired}</span
              >
            </button>
          {:else}
            <button
              type="button"
              class="text-muted-foreground hover:text-foreground hover:border-ring/60 rounded-md border border-dashed px-2 py-1.5 text-left text-xs"
              onclick={() =>
                workbench.notify(
                  `Running ${s.name} through ${p.name} needs the daemon.`,
                )}>Not run yet · Run</button
            >
          {/if}
        {/each}
      {/each}
    </div>
  </div>
</div>
