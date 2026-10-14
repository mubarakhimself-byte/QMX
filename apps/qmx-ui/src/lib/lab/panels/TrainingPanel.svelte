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
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { cn } from "$lib/utils";
  import EnvChip from "../EnvChip.svelte";
  import { TRAINING as T, envById } from "../demo";
  import { lab } from "../lab.svelte";

  const STEPS = [
    { id: "data", label: "Dataset", state: "done" },
    { id: "features", label: "Features", state: "done" },
    { id: "split", label: "Split", state: "done" },
    { id: "leakage", label: "Leakage check", state: "done" },
    { id: "train", label: "Train", state: "running" },
    { id: "evaluate", label: "Evaluate", state: "waiting" },
    { id: "plug", label: "Plug into slots", state: "waiting" },
  ];
  const size = panelSize();
  const overfit = $derived(T.valid.at(-1)! - T.train.at(-1)! > 0.05);
</script>

{#snippet split()}
  <div
    class={cn(
      "px-panel py-row grid shrink-0 gap-x-4 text-xs",
      size.mode === "expanded" ? "grid-cols-5" : "grid-cols-3",
    )}
  >
    <div>
      <span class="text-muted-foreground block">Train</span>{T.split.train}
    </div>
    <div>
      <span class="text-muted-foreground block">Validation</span>{T.split
        .validation}
    </div>
    <div>
      <span class="text-muted-foreground flex items-center gap-1"
        ><Lock class="size-3" />Sealed test</span
      >{T.split.sealed}
    </div>
    {#if size.mode === "expanded"}
      <div>
        <span class="text-muted-foreground block">Purge</span>{T.purge}
      </div>
      <div>
        <span class="text-muted-foreground block">Embargo</span>{T.embargo}
      </div>
    {/if}
  </div>
{/snippet}

{#if lab.machine && lab.machine !== T.env}
  <div
    class="text-muted-foreground p-panel flex h-full items-center justify-center text-center text-sm"
  >
    Nothing training on {envById(lab.machine)?.name}
  </div>
{:else if size.mode === "compact"}
  <div class="p-panel gap-row flex h-full flex-col">
    <p class="truncate text-sm font-medium">{T.model}</p>
    <p class="num text-2xl font-semibold">{T.epoch} / {T.epochs}</p>
    <p
      class="truncate text-xs {overfit
        ? 'text-warning'
        : 'text-muted-foreground'}"
    >
      {overfit ? "Likely overfitting" : "epochs"}
    </p>
    <Sparkline values={T.valid} class="mt-auto h-8 w-full shrink-0" />
  </div>
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-x-3">
      <span class="truncate text-sm font-medium">{T.model}</span>
      <span class="num text-muted-foreground text-xs"
        >epoch {T.epoch} / {T.epochs}</span
      >
      {#if overfit}<span
          class="text-warning flex items-center gap-1 text-xs whitespace-nowrap"
          ><TriangleAlert class="size-3.5" />Likely overfitting</span
        >{/if}
      <span class="ml-auto flex shrink-0 items-center gap-1"
        ><EnvChip env={T.env} status="running" /><InfoTip
          label="Explain training"
          text={`${T.kind}. Validation loss pulling away from training loss means the model is learning noise. Purge ${T.purge} and embargo ${T.embargo} keep the split honest; the sealed year opens once, at the end. Click a step to edit it in Build.`}
        /></span
      >
    </div>
    <ol
      class="px-panel pb-row flex shrink-0 items-center gap-1 overflow-x-auto"
      aria-label="Pipeline"
    >
      {#each STEPS as s, i (s.id)}
        {#if i > 0}<span class="bg-border h-px w-3 shrink-0"></span>{/if}
        <li>
          <button
            type="button"
            class={cn(
              "hover:border-ring flex h-7 items-center gap-1.5 rounded-md border px-2 text-xs whitespace-nowrap",
              s.state === "running" && "border-info text-info",
              s.state === "waiting" && "text-muted-foreground border-dashed",
            )}
            title={`Edit ${s.label} in Build`}
            onclick={() => lab.open("build")}
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
          onclick={() => lab.ask(`Add a step to the ${T.model} pipeline that `)}
          ><Plus class="size-3.5" />Step</button
        >
      </li>
    </ol>
    <div class="px-panel pt-row min-h-0 flex-1">
      <LineChart
        series={[
          { label: "Training loss", values: T.train, color: "var(--chart-2)" },
          {
            label: "Validation loss",
            values: T.valid,
            color: "var(--chart-4)",
          },
        ]}
        height={180}
      />
    </div>
    {@render split()}
  </div>
{/if}
