<script lang="ts">
  /**
   * Decisions arriving from the paper run as they happen: every trade with
   * the steps that sized it, and every trade the pod refused. In the demo
   * new rows are replayed from a sample every few seconds.
   */
  import { onMount } from "svelte";
  import { cn } from "$lib/utils";
  import { usd } from "$lib/portfolio/bits";
  import { PAPER_FEED, type PaperDecision } from "../pods";

  let rows = $state<(PaperDecision & { key: number; fresh?: boolean })[]>(
    PAPER_FEED.map((d, i) => ({ ...d, key: i })),
  );
  onMount(() => {
    let k = 100;
    const timer = setInterval(() => {
      const sample = PAPER_FEED[k % PAPER_FEED.length];
      const now = new Date();
      const at = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
      rows = [
        { ...sample, at, key: k++, fresh: true },
        ...rows.map((r) => ({ ...r, fresh: false })),
      ].slice(0, 30);
    }, 7000);
    return () => clearInterval(timer);
  });
  const money = (v: number) => usd(v, v % 1 ? 2 : 0);
</script>

<div class="flex h-full flex-col">
  <p
    class="text-muted-foreground flex h-8 shrink-0 items-center gap-2 border-b px-3 text-xs"
  >
    <span class="bg-success size-1.5 animate-pulse rounded-full"></span>
    Live from paper · newest first
  </p>
  <ul class="min-h-0 flex-1 overflow-auto">
    {#each rows as r (r.key)}
      {@const last = r.steps[r.steps.length - 1]}
      <li
        class={cn(
          "border-b border-border/50 px-3 py-2 transition-colors duration-700",
          r.fresh && "bg-primary/10",
        )}
      >
        <div class="flex items-baseline gap-2 text-sm">
          <span class="text-muted-foreground num w-11 shrink-0 text-xs"
            >{r.at}</span
          >
          <span
            class={cn(
              "font-medium",
              r.side === "Buy" ? "text-success" : "text-destructive",
            )}>{r.side}</span
          >
          <span class="num">{r.symbol}</span>
          <span class="text-muted-foreground truncate text-xs">{r.bot}</span>
          {#if r.refused}
            <span class="text-destructive ml-auto shrink-0 text-xs font-medium"
              >Refused</span
            >
          {:else}
            <span class="num ml-auto shrink-0 font-semibold"
              >{money(last.usd)}</span
            >
          {/if}
        </div>
        <div
          class="text-muted-foreground mt-1 flex flex-wrap items-center gap-1 pl-13 text-xs"
        >
          {#each r.steps as s, i (i)}
            {#if i}<span aria-hidden="true">›</span>{/if}
            <span class="rounded border px-1.5"
              >{s.by}
              <span class="num text-foreground">{money(s.usd)}</span></span
            >
          {/each}
          {#if r.refused}<span aria-hidden="true">›</span><span
              class="border-destructive/50 text-destructive rounded border px-1.5"
              >{r.refused}</span
            >{/if}
        </div>
      </li>
    {/each}
  </ul>
</div>
