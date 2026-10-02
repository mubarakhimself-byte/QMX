<script lang="ts">
  /**
   * A model in training: the pipeline it runs (each step editable or
   * replaceable), live loss curves, and the split it must respect (CT-12:
   * train / validation / sealed test, purge and embargo). The model object
   * itself is new scope; the split rules are the docs'.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Lock from "@lucide/svelte/icons/lock";
  import TriangleAlert from "@lucide/svelte/icons/triangle-alert";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import EnvChip from "../EnvChip.svelte";
  import { TRAINING as T } from "../demo";

  const STEPS = [
    { id: "data", label: "Dataset", state: "done" },
    { id: "features", label: "Features", state: "done" },
    { id: "split", label: "Split", state: "done" },
    { id: "leakage", label: "Leakage check", state: "done" },
    { id: "train", label: "Train", state: "running" },
    { id: "evaluate", label: "Evaluate", state: "waiting" },
    { id: "plug", label: "Plug into slots", state: "waiting" },
  ];
  const gap = $derived(T.valid.at(-1)! - T.train.at(-1)!);
</script>

<div class="flex h-full flex-col">
  <div
    class="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b px-3 py-2"
  >
    <span class="text-sm font-medium">{T.model}</span>
    <span class="text-muted-foreground text-xs">{T.kind}</span>
    <span class="num text-xs">epoch {T.epoch} / {T.epochs}</span>
    <span class="ml-auto"><EnvChip env={T.env} status="running" /></span>
  </div>
  <ol
    class="flex shrink-0 items-center gap-1 overflow-x-auto border-b px-3 py-2"
    aria-label="Pipeline"
  >
    {#each STEPS as s, i (s.id)}
      {#if i > 0}<span class="bg-border h-px w-3 shrink-0"></span>{/if}
      <li>
        <button
          type="button"
          class={cn(
            "flex h-7 items-center gap-1.5 rounded-md border px-2 text-xs whitespace-nowrap",
            s.state === "running" && "border-info text-info",
            s.state === "waiting" && "text-muted-foreground border-dashed",
          )}
          onclick={() =>
            workbench.notify(
              `${s.label}: open it in the Build layout to edit or swap it.`,
            )}
        >
          <span
            class={cn(
              "size-1.5 rounded-full",
              s.state === "done"
                ? "bg-success"
                : s.state === "running"
                  ? "bg-info remote-pulse"
                  : "bg-muted-foreground/50",
            )}
          ></span>{s.label}
        </button>
      </li>
    {/each}
    <li>
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground flex h-7 items-center gap-1 rounded-md px-2 text-xs"
        onclick={() =>
          workbench.notify(
            "Add a step: pick from your saved steps, or describe one to the Lab copilot.",
          )}><Plus class="size-3.5" />Step</button
      >
    </li>
  </ol>
  <div class="min-h-0 flex-1 p-3">
    <LineChart
      series={[
        { label: "Training loss", values: T.train, color: "var(--chart-2)" },
        { label: "Validation loss", values: T.valid, color: "var(--chart-4)" },
      ]}
      height={180}
    />
  </div>
  <div class="grid shrink-0 grid-cols-3 gap-px border-t text-xs">
    <div class="px-3 py-2">
      <span class="text-muted-foreground block">Train</span>{T.split.train}
    </div>
    <div class="px-3 py-2">
      <span class="text-muted-foreground block">Validation</span>{T.split
        .validation}
    </div>
    <div class="px-3 py-2">
      <span class="text-muted-foreground flex items-center gap-1"
        ><Lock class="size-3" />Sealed test</span
      >{T.split.sealed}
    </div>
  </div>
  <p
    class="text-muted-foreground flex items-center gap-1.5 border-t px-3 py-2 text-xs"
  >
    {#if gap > 0.05}<TriangleAlert
        class="text-warning size-3.5 shrink-0"
      />Validation loss is pulling away from training loss: likely overfitting.{:else}Purge
      {T.purge}, embargo {T.embargo}. The sealed year opens once, at the end.{/if}
  </p>
</div>
