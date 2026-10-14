<script lang="ts">
  /**
   * News and events: CFD markets with macro, and crypto. Each item shows
   * sentiment and impact; which markets it touches and its source show
   * when the tile is wide or expanded (every item has a backend source).
   */
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import Segmented from "$lib/workbench/Segmented.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { NEWS } from "../demo";

  const size = panelSize();
  let kind = $state<"crypto" | "fx" | "all">("all");
  type SortKey = "time" | "impact" | "mood";
  let sort = $state<SortKey>("time");
  const RANK = { high: 3, medium: 2, low: 1 };
  const rows = $derived(
    [...NEWS.filter((n) => kind === "all" || n.kind === kind)].sort((a, b) =>
      sort === "impact"
        ? RANK[b.impact] - RANK[a.impact]
        : sort === "mood"
          ? Math.abs(b.sentiment) - Math.abs(a.sentiment)
          : 0,
    ),
  );
  const next = $derived(NEWS.find((n) => n.impact === "high") ?? NEWS[0]);
  const mood = (s: number) =>
    s > 0.2
      ? "text-success"
      : s < -0.2
        ? "text-destructive"
        : "text-muted-foreground";
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label={next.title}
    value={next.when}
    status="High impact"
    tone="warn"
  >
    <ul class="flex flex-col">
      {#each NEWS.filter((n) => n !== next).slice(0, 4) as n (n.title)}
        <li class="py-row flex gap-2 text-xs">
          <span class="text-muted-foreground w-12 shrink-0">{n.when}</span>
          <span class="truncate">{n.title}</span>
        </li>
      {/each}
    </ul>
  </PanelSummary>
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2 text-xs">
      <Segmented
        label="Markets"
        options={[
          { value: "all", label: "All" },
          { value: "fx", label: "CFDs" },
          { value: "crypto", label: "Crypto" },
        ]}
        bind:value={kind}
      />
      <select
        bind:value={sort}
        class="bg-background/40 ml-auto h-6 rounded border px-1.5 text-xs"
        aria-label="Sort events"
      >
        <option value="time">Newest</option><option value="impact"
          >Impact</option
        ><option value="mood">Strongest mood</option>
      </select>
      <InfoTip
        label="Explain news and events"
        text="CFD markets with macro (FX, indices, gold, oil) and crypto. The dot is impact; the number is sentiment from −1 to +1. Each item names its source."
      />
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground hover:bg-muted flex size-7 items-center justify-center rounded-md"
        aria-label="Add a source or a news workflow"
        title="Add a source or a news workflow"
        onclick={() =>
          workbench.notify(
            "The news and sentiment workflow is a Lab template: pick sources, score sentiment, map to markets, pause pods around events.",
          )}><Plus class="size-3.5" /></button
      >
    </div>
    <ul class="min-h-0 flex-1 overflow-auto">
      {#each rows as n (n.title)}
        <li
          class="border-border/50 px-panel py-row grid grid-cols-[3.5rem_1fr_auto] items-baseline gap-x-3 border-b"
        >
          <span class="text-muted-foreground text-xs">{n.when}</span>
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
              <span class="truncate" title={n.title}>{n.title}</span>
            </span>
            <span
              class="text-muted-foreground hidden truncate text-xs @2xl:block"
              >{n.affects.join(", ")} · {n.source}</span
            >
          </span>
          <span
            class={cn("num text-sm", mood(n.sentiment))}
            title="Sentiment from −1 to +1"
            >{n.sentiment > 0 ? "+" : ""}{n.sentiment.toFixed(1)}</span
          >
        </li>
      {/each}
    </ul>
  </div>
{/if}
