<script lang="ts">
  /**
   * News and events in two streams: CFD markets with macro (FX, indices,
   * gold, oil), and crypto. Each item shows sentiment, which markets it touches, and the
   * source it comes from (every item must have a backend source).
   */
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { NEWS } from "../demo";

  const TABS = [
    { id: "all", label: "All" },
    { id: "fx", label: "CFDs and macro" },
    { id: "crypto", label: "Crypto" },
  ] as const;
  let tab = $state<"crypto" | "fx" | "all">("all");
  type SortKey = "time" | "impact" | "mood";
  let sort = $state<SortKey>("time");
  const RANK = { high: 3, medium: 2, low: 1 };
  const rows = $derived(
    [...NEWS.filter((n) => tab === "all" || n.kind === tab)].sort((a, b) =>
      sort === "impact"
        ? RANK[b.impact] - RANK[a.impact]
        : sort === "mood"
          ? Math.abs(b.sentiment) - Math.abs(a.sentiment)
          : 0,
    ),
  );
  const mood = (s: number) =>
    s > 0.2
      ? "text-success"
      : s < -0.2
        ? "text-destructive"
        : "text-muted-foreground";
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-1 border-b px-2 text-xs">
    {#each TABS as t (t.id)}
      <button
        type="button"
        class={cn(
          "h-6 rounded-md px-2",
          tab === t.id
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={tab === t.id}
        onclick={() => (tab = t.id)}>{t.label}</button
      >
    {/each}
    <span class="text-muted-foreground ml-auto">Sort</span>
    <select
      bind:value={sort}
      class="h-6 rounded border px-1.5 text-xs"
      aria-label="Sort events"
    >
      <option value="time">Newest</option><option value="impact">Impact</option
      ><option value="mood">Strongest mood</option>
    </select>
  </div>
  <ul class="min-h-0 flex-1 overflow-auto">
    {#each rows as n (n.title)}
      <li
        class="grid grid-cols-[3.5rem_1fr_auto] gap-x-3 border-b border-border/50 px-3 py-2"
      >
        <span class="text-muted-foreground pt-0.5 text-xs">{n.when}</span>
        <span class="min-w-0">
          <span class="flex items-center gap-2 text-sm">
            <span
              class={cn(
                "size-2 shrink-0 rounded-full",
                n.impact === "high"
                  ? "bg-destructive"
                  : n.impact === "medium"
                    ? "bg-warning"
                    : "bg-muted-foreground/50",
              )}
              title={`${n.impact} impact`}
            ></span>
            <span class="truncate">{n.title}</span>
          </span>
          <span class="text-muted-foreground block text-xs"
            >{n.affects.join(", ")} · from {n.source}</span
          >
        </span>
        <span
          class={cn("num self-center text-sm", mood(n.sentiment))}
          title="Sentiment from −1 to +1"
          >{n.sentiment > 0 ? "+" : ""}{n.sentiment.toFixed(1)}</span
        >
      </li>
    {/each}
  </ul>
  <button
    type="button"
    class="text-muted-foreground hover:text-foreground flex h-9 shrink-0 items-center gap-1.5 border-t px-3 text-xs"
    onclick={() =>
      workbench.notify(
        "The news and sentiment workflow is a Lab template: pick sources, score sentiment, map to coins, pause pods around events.",
      )}><Plus class="size-3.5" />Add a source or a news workflow</button
  >
</div>
