<script lang="ts">
  /** Console output of the selected run, as the run's own process wrote it. */
  import RunConsole from "$lib/qmx/RunConsole.svelte";
  import type { LinkGroup } from "$lib/workbench/tiles/tiles";
  import { RUNS, envById } from "../demo";
  import { lab } from "../lab.svelte";

  let { link }: { link?: LinkGroup } = $props();
  const run = $derived(RUNS.find((r) => r.id === lab.selectedFor(link)));
  const lines = $derived(
    run
      ? [
          `placed on ${envById(run.env)?.name ?? run.env} (${envById(run.env)?.where ?? ""})`,
          `bot eurusd-h1-gbm v7 · ${run.symbol} ${run.timeframe} · role ${run.role}`,
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

<div class="h-full p-2">
  {#if run}
    <RunConsole
      command={`qmb ${run.procedure.toLowerCase().replace(" ", "-")} ${run.id}`}
      {lines}
      {status}
    />
  {:else}
    <p class="text-muted-foreground p-4 text-sm">
      Select a run to see its log.
    </p>
  {/if}
</div>
