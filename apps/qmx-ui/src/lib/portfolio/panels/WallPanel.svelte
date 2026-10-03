<script lang="ts">
  /**
   * A tile per Book: equity curve, room above the kill line, today's loss
   * budget, where its risk comes from, seats. Border colour says live or
   * paper. Add a Book from a template.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { BOOKS, accountById, sizing } from "../demo";
  import { MODE_BORDER, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  const rows = $derived(
    BOOKS.filter((b) =>
      portfolio.world === "all"
        ? true
        : portfolio.world === "live"
          ? b.mode === "LIVE"
          : b.mode === "PAPER",
    ),
  );
</script>

<div
  class="grid h-full content-start gap-2 overflow-auto p-2 [grid-template-columns:repeat(auto-fill,minmax(15rem,1fr))]"
>
  {#each rows as b (b.id)}
    {@const s = sizing(b)}
    {@const room = Math.max(
      0,
      (b.equity - b.killLine) / (b.capital - b.killLine),
    )}
    <button
      type="button"
      class={cn(
        "hover:bg-muted/40 flex flex-col gap-2 rounded-lg border-2 p-3 text-left",
        portfolio.book === b.id && "ring-ring ring-1",
      )}
      style="border-color: {b.mode === 'LIVE'
        ? MODE_BORDER.live
        : MODE_BORDER.paper}"
      onclick={() => (portfolio.book = b.id)}
    >
      <span class="flex items-center gap-2">
        <span class="font-medium">{b.name}</span>
        <span class="text-muted-foreground text-xs">{b.version}</span>
        <span class="text-muted-foreground ml-auto text-xs">{b.mode}</span>
      </span>
      <span class="text-muted-foreground text-xs"
        >{accountById(b.account)?.name} · {b.engine.label}</span
      >
      <span class="block h-12"><Sparkline values={b.equitySeries} /></span>
      <span class="flex items-baseline justify-between">
        <span class="num text-lg">{usd(b.equity)}</span>
        {#if b.binding === "stood-down"}<span class="text-destructive text-xs"
            >stood down at the kill line</span
          >{/if}
      </span>
      <span class="grid gap-1 text-xs">
        <span class="flex items-center gap-2"
          ><span class="text-muted-foreground w-24">Above kill line</span><span
            class="bg-muted h-1.5 flex-1 overflow-hidden rounded-full"
            ><span
              class={cn(
                "block h-full",
                room < 0.25 ? "bg-destructive" : "bg-success",
              )}
              style="width:{room * 100}%"
            ></span></span
          ></span
        >
        <span class="flex items-center gap-2"
          ><span class="text-muted-foreground w-24">Budget used</span><span
            class="bg-muted h-1.5 flex-1 overflow-hidden rounded-full"
            ><span
              class="bg-primary block h-full"
              style="width:{Math.min(1, b.lossToday / s.budget) * 100}%"
            ></span></span
          ></span
        >
      </span>
      <span class="text-muted-foreground text-xs"
        >{b.seats.filter((x) => x.state === "active").length} of {b.seats
          .length} seats active</span
      >
    </button>
  {/each}
  <button
    type="button"
    class="hover:border-ring text-muted-foreground hover:text-foreground flex min-h-48 flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed text-sm"
    onclick={() => (portfolio.templatesOpen = true)}
  >
    <Plus class="size-5" />New Book from a template
  </button>
</div>
