<script lang="ts">
  /**
   * Every run for the subject: tick to compare, click to select (linked
   * tiles follow), sort by any measure. Roles follow QMB (confirmation,
   * trial, replicate, aborted); measures are raw, never a composite score.
   */
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import { cn } from "$lib/utils";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import EnvChip from "../EnvChip.svelte";
  import StatusDot from "../StatusDot.svelte";
  import X from "@lucide/svelte/icons/x";
  import { RUNS, envById, type Run } from "../demo";
  import { lab } from "../lab.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import Segmented from "$lib/workbench/Segmented.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";

  let { link }: { link?: LinkGroup } = $props();
  const size = panelSize();

  const FILTERS = ["All", "Running", "Done", "Failed"] as const;
  let filter = $state<(typeof FILTERS)[number]>("All");
  type SortKey = "net" | "maxDd" | "sharpe" | "trades" | "id";
  let sortKey = $state<SortKey>("id");
  let desc = $state(true);

  const rows = $derived.by(() => {
    const f = RUNS.filter((r) =>
      lab.machine && r.env !== lab.machine
        ? false
        : filter === "All"
          ? true
          : filter === "Running"
            ? r.status === "running" || r.status === "queued"
            : filter === "Done"
              ? r.status === "done"
              : r.status === "failed" ||
                r.status === "aborted" ||
                r.status === "unknown",
    );
    const v = (r: Run) =>
      sortKey === "id" ? Number(r.id.slice(4)) : (r[sortKey] ?? -Infinity);
    return [...f].sort((a, b) => (desc ? v(b) - v(a) : v(a) - v(b)));
  });
  const selected = $derived(lab.selectedFor(link));
  const counts = $derived({
    running: RUNS.filter((r) => r.status === "running").length,
    queued: RUNS.filter((r) => r.status === "queued").length,
  });

  function sortBy(k: SortKey) {
    if (sortKey === k) desc = !desc;
    else {
      sortKey = k;
      desc = k !== "maxDd";
    }
  }
  const fmt = (v: number | null, suffix = "") =>
    v === null ? "—" : `${v > 0 && suffix === "%" ? "+" : ""}${v}${suffix}`;
  /** Columns that give way first in a narrow tile, so it never scrolls sideways. */
  const HIDE: Partial<Record<SortKey, string>> = {
    maxDd: "hidden @md:table-cell",
    sharpe: "hidden @md:table-cell",
    trades: "hidden @lg:table-cell",
  };
  const COLS: { key: SortKey; label: string }[] = [
    { key: "net", label: "Net" },
    { key: "maxDd", label: "Max DD" },
    { key: "sharpe", label: "Sharpe" },
    { key: "trades", label: "Trades" },
  ];
</script>

{#if size.mode === "compact"}
  {@const best = RUNS.filter((r) => r.net !== null).sort(
    (a, b) => (b.net ?? 0) - (a.net ?? 0),
  )[0]}
  <PanelSummary
    label={`${RUNS.length} runs · best ${best.symbol} ${best.timeframe}`}
    value={fmt(best.net, "%")}
    status={`${counts.running} running · ${counts.queued} queued`}
    values={best.equity.length > 1 ? best.equity : undefined}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      <Segmented
        label="Show runs"
        options={FILTERS.map((f) => ({ value: f, label: f }))}
        bind:value={filter}
      />
      {#if lab.machine}
        <button
          type="button"
          class="bg-info/12 text-info ml-1 flex h-6 items-center gap-1 rounded-md px-2 text-xs"
          aria-label="Show work on every machine"
          onclick={() => lab.connect(null)}
          >On {envById(lab.machine)?.name}<X class="size-3" /></button
        >
      {/if}
      <span
        class="text-muted-foreground ml-auto hidden text-xs tabular-nums @md:inline"
        >{rows.length} runs · {lab.ticked.length} ticked</span
      >
    </div>
    <div class="min-h-0 flex-1 overflow-auto">
      <table class="w-full text-sm whitespace-nowrap">
        <thead
          class="bg-panel text-muted-foreground sticky top-0 z-10 text-left text-xs"
        >
          <tr class="border-b">
            <th class="w-8 py-1.5 pl-2"><span class="sr-only">Compare</span></th
            >
            <th class="py-1.5 font-normal">
              <button
                type="button"
                class="hover:text-foreground"
                onclick={() => sortBy("id")}>Run</button
              >
            </th>
            <th class="hidden py-1.5 font-normal @2xl:table-cell">Procedure</th>
            <th class="py-1.5 font-normal">Market</th>
            <th class="hidden py-1.5 font-normal @3xl:table-cell">Role</th>
            {#each COLS as c (c.key)}
              <th class={cn("py-1.5 pr-3 text-right font-normal", HIDE[c.key])}>
                <button
                  type="button"
                  class="hover:text-foreground inline-flex items-center gap-0.5"
                  onclick={() => sortBy(c.key)}
                  >{c.label}{#if sortKey === c.key}{#if desc}<ArrowDown
                        class="size-3"
                      />{:else}<ArrowUp class="size-3" />{/if}{/if}</button
                >
              </th>
            {/each}
            <th class="hidden py-1.5 pr-2 font-normal @4xl:table-cell">Where</th
            >
            <th class="hidden py-1.5 pr-2 font-normal @xl:table-cell">State</th>
          </tr>
        </thead>
        <tbody>
          {#each rows as r (r.id)}
            <tr
              class={cn(
                "hover:bg-muted/50 cursor-pointer border-b border-border/50",
                selected === r.id && "bg-primary/10 hover:bg-primary/15",
              )}
              onclick={() => lab.select(link, r.id)}
            >
              <td class="py-1 pl-2">
                <input
                  type="checkbox"
                  class="accent-primary size-3.5"
                  checked={lab.ticked.includes(r.id)}
                  aria-label={`Compare ${r.id}`}
                  onclick={(e) => e.stopPropagation()}
                  onchange={() => lab.toggleTick(r.id)}
                />
              </td>
              <td class="num py-1 pr-3 text-xs">{r.id}</td>
              <td class="hidden py-1 pr-3 @2xl:table-cell">{r.procedure}</td>
              <td class="py-1 pr-3"
                >{r.symbol}
                <span class="text-muted-foreground text-xs">{r.timeframe}</span
                ></td
              >
              <td
                class="text-muted-foreground hidden py-1 pr-3 text-xs @3xl:table-cell"
                >{r.role}</td
              >
              <td
                class={cn(
                  "num py-1 pr-3 text-right",
                  (r.net ?? 0) > 0 && "text-success",
                  (r.net ?? 0) < 0 && "text-destructive",
                )}>{fmt(r.net, "%")}</td
              >
              <td
                class={cn(
                  "num text-muted-foreground py-1 pr-3 text-right",
                  HIDE.maxDd,
                )}>{fmt(r.maxDd, "%")}</td
              >
              <td class={cn("num py-1 pr-3 text-right", HIDE.sharpe)}
                >{fmt(r.sharpe)}</td
              >
              <td
                class={cn(
                  "num text-muted-foreground py-1 pr-3 text-right",
                  HIDE.trades,
                )}>{r.trades || "—"}</td
              >
              <td class="hidden py-1 pr-2 @4xl:table-cell"
                ><EnvChip env={r.env} status={r.status} /></td
              >
              <td class="hidden py-1 pr-2 @xl:table-cell">
                {#if r.progress !== undefined}
                  <span class="flex items-center gap-1.5">
                    <span class="bg-muted h-1 w-12 overflow-hidden rounded-full"
                      ><span
                        class="bg-info block h-full"
                        style="width: {r.progress}%"
                      ></span></span
                    ><span class="num text-xs">{r.progress}%</span>
                  </span>
                {:else}
                  <StatusDot status={r.status} />
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}
