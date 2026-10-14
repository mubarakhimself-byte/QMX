<script lang="ts">
  /** Console output of the selected run, as the run's own process wrote it. */
  import RunConsole from "$lib/qmx/RunConsole.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { cn } from "$lib/utils";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import { RUNS, envById } from "../demo";
  import { lab } from "../lab.svelte";

  let { link }: { link?: LinkGroup } = $props();
  const size = panelSize();
  const run = $derived(RUNS.find((r) => r.id === lab.selectedFor(link)));
  const lines = $derived(
    run
      ? [
          `placed on ${envById(run.env)?.name ?? run.env} (${envById(run.env)?.where ?? ""})`,
          `bot btc-breakout v7 · ${run.symbol} ${run.timeframe} · role ${run.role}`,
          ...(run.status === "queued"
            ? ["waiting for a free slot; the governor never oversubscribes"]
            : run.status === "failed"
              ? [
                  "data gap 2021-03-04 → 2021-03-09 exceeds the allowed 2 days",
                  "run failed: missing bars",
                ]
              : [
                  "loaded 61,320 bars · warm-up 200 bars",
                  run.status === "running"
                    ? `progress ${run.progress}%`
                    : `${run.trades} trades closed`,
                  ...(run.status === "done"
                    ? [`CT-32 written · ${run.role} · net ${run.net}%`]
                    : []),
                ]),
        ]
      : [],
  );
  const status = $derived(
    run?.status === "running" ||
      run?.status === "queued" ||
      run?.status === "failed"
      ? run.status
      : "done",
  );
</script>

{#if !run}
  <div
    class="text-muted-foreground p-panel flex h-full items-center justify-center text-sm"
  >
    No run selected
  </div>
{:else if size.mode === "compact"}
  <div
    class="p-panel flex h-full flex-col gap-0.5 overflow-hidden font-mono text-xs"
  >
    <p class="flex items-center gap-2">
      <span
        class={cn(
          "size-1.5 shrink-0 rounded-full",
          status === "failed"
            ? "bg-destructive"
            : status === "done"
              ? "bg-success"
              : "bg-info",
        )}
      ></span>
      <span class="truncate">{run.id}</span>
      <span class="text-muted-foreground ml-auto uppercase">{status}</span>
    </p>
    {#each lines.slice(-3) as l (l)}<p class="text-muted-foreground truncate">
        {l}
      </p>{/each}
  </div>
{:else}
  <div class="h-full p-2">
    <RunConsole
      command={`qmb ${run.procedure.toLowerCase().replace(" ", "-")} ${run.id}`}
      {lines}
      {status}
    />
  </div>
{/if}
