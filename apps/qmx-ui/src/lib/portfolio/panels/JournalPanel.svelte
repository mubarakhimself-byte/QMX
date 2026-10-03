<script lang="ts">
  /**
   * A bot's trading journal: a summary, every closed trade as a bar (up for
   * a win, down for a loss, height = R), then the timeline of trades, events
   * and your notes, filterable. Notes you add stay with the bot.
   */
  import ArrowLeftRight from "@lucide/svelte/icons/arrow-left-right";
  import Zap from "@lucide/svelte/icons/zap";
  import StickyNote from "@lucide/svelte/icons/sticky-note";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { CANDIDATES, JOURNAL, type JournalNote } from "../demo";
  import { portfolio } from "../portfolio.svelte";

  const c = $derived(
    CANDIDATES.find((x) => x.entity.id === portfolio.candidate) ??
      CANDIDATES[0],
  );
  let mine = $state<Record<string, JournalNote[]>>({});
  const notes = $derived([
    ...(mine[c.entity.id] ?? []),
    ...(JOURNAL[c.entity.id] ?? []),
  ]);
  const FILTERS = [
    { id: "all", label: "All" },
    { id: "trade", label: "Trades" },
    { id: "event", label: "Events" },
    { id: "note", label: "Notes" },
  ] as const;
  let filter = $state<(typeof FILTERS)[number]["id"]>("all");
  const shown = $derived(
    notes.filter((n) => filter === "all" || n.kind === filter),
  );
  const trades = $derived(
    notes.filter((n) => n.kind === "trade" && n.r !== undefined && n.r !== 0),
  );
  const totalR = $derived(trades.reduce((s, t) => s + (t.r ?? 0), 0));
  const wins = $derived(trades.filter((t) => (t.r ?? 0) > 0).length);
  // Sample R history for the strip (the daemon sends the full list).
  const strip = $derived([
    ...[0.8, -1, 1.4, 0.3, -1, 2.1, -0.4, 1.1, -1, 0.9, 1.6, -1, 0.5].slice(
      0,
      6 + (c.days % 7),
    ),
    ...trades.map((t) => t.r ?? 0),
  ]);
  const ICON = { trade: ArrowLeftRight, event: Zap, note: StickyNote };
  let draft = $state("");
  function add(e: SubmitEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    mine[c.entity.id] = [
      { time: "Now", kind: "note", text: `You: ${draft.trim()}` },
      ...(mine[c.entity.id] ?? []),
    ];
    draft = "";
  }
</script>

<div class="flex h-full flex-col">
  <div class="grid shrink-0 grid-cols-4 gap-px border-b">
    {#each [["Trades", String(strip.length)], ["Won", `${Math.round(((wins + strip.filter((r) => r > 0).length) / Math.max(1, strip.length + trades.length)) * 100)}%`], ["Total", `${(strip.reduce((a, b) => a + b, 0) + totalR).toFixed(1)} R`], ["Day", String(c.days)]] as [k, v] (k)}
      <div class="px-3 py-2">
        <p class="text-muted-foreground text-xs">{k}</p>
        <p class="num text-lg font-semibold">{v}</p>
      </div>
    {/each}
  </div>
  <div
    class="flex h-16 shrink-0 items-center gap-0.5 border-b px-3"
    aria-label="Each trade's result in R"
  >
    {#each strip as r, i (i)}
      <span class="flex h-full flex-1 flex-col justify-center">
        <span class="flex h-1/2 items-end"
          ><span
            class={cn("w-full rounded-t-sm", r > 0 ? "bg-success/80" : "")}
            style="height:{r > 0 ? Math.min(1, r / 2.5) * 100 : 0}%"
          ></span></span
        >
        <span class="flex h-1/2 items-start"
          ><span
            class={cn("w-full rounded-b-sm", r < 0 ? "bg-destructive/70" : "")}
            style="height:{r < 0 ? Math.min(1, -r / 2.5) * 100 : 0}%"
          ></span></span
        >
      </span>
    {/each}
  </div>
  <div class="flex h-9 shrink-0 items-center gap-1 border-b px-2 text-xs">
    {#each FILTERS as f (f.id)}
      <button
        type="button"
        class={cn(
          "h-6 rounded-md px-2",
          filter === f.id
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={filter === f.id}
        onclick={() => (filter = f.id)}>{f.label}</button
      >
    {/each}
  </div>
  <ol class="min-h-0 flex-1 overflow-auto px-4 py-2">
    {#each shown as n, i (i)}
      {@const Icon = ICON[n.kind]}
      <li class="relative flex gap-3 pb-3 pl-1">
        <span class="bg-border absolute top-6 bottom-0 left-[13px] w-px"></span>
        <span
          class={cn(
            "relative z-10 flex size-7 shrink-0 items-center justify-center rounded-full border bg-[var(--background)]",
            n.kind === "event" && "border-warning/60",
            n.kind === "note" && "border-primary/60",
          )}
        >
          <Icon
            class={cn(
              "size-3.5",
              n.kind === "event"
                ? "text-warning"
                : n.kind === "note"
                  ? "text-primary"
                  : "text-muted-foreground",
            )}
          />
        </span>
        <div class="min-w-0 flex-1 pt-0.5">
          <p class="text-sm">{n.text}</p>
          <p class="text-muted-foreground text-xs">{n.time}</p>
        </div>
        {#if n.r !== undefined && n.r !== 0}<span
            class={cn(
              "num self-start rounded-md px-1.5 py-0.5 text-xs",
              n.r > 0
                ? "bg-success/15 text-success"
                : "bg-destructive/15 text-destructive",
            )}>{n.r > 0 ? "+" : ""}{n.r} R</span
          >{/if}
      </li>
    {:else}
      <li class="text-muted-foreground py-8 text-center text-sm">
        Nothing here yet for {c.entity.name}.
      </li>
    {/each}
  </ol>
  <form class="flex gap-2 border-t p-2" onsubmit={add}>
    <input
      bind:value={draft}
      placeholder={`Note on ${c.entity.name}…`}
      aria-label="Journal note"
      class="bg-background/40 h-8 flex-1 rounded-md border px-2.5 text-sm"
    />
    <Button type="submit" size="sm" disabled={!draft.trim()}>Add note</Button>
  </form>
</div>
