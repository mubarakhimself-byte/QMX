<script lang="ts">
  /**
   * "Start something new": a short guided flow. 1) what you're doing,
   * 2) the specifics (what, with which data, where it runs), 3) the steps
   * it will set up and the layout it opens. Finishing creates a layout of
   * its own (saved like any other) and can be kept as a template.
   */
  import Lightbulb from "@lucide/svelte/icons/lightbulb";
  import GitCompare from "@lucide/svelte/icons/git-compare";
  import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
  import Grid3x3 from "@lucide/svelte/icons/grid-3x3";
  import Workflow from "@lucide/svelte/icons/workflow";
  import Import from "@lucide/svelte/icons/import";
  import Check from "@lucide/svelte/icons/check";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import MessagesSquare from "@lucide/svelte/icons/messages-square";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import { pane, split, type TileLayout } from "$lib/workbench/tiles/tiles";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PANELS } from "./catalog";
  import { ASSETS, ENVIRONMENTS } from "./demo";
  import { lab } from "./lab.svelte";

  let { open = $bindable(false) }: { open?: boolean } = $props();

  const KINDS = [
    {
      id: "hypothesis",
      icon: Lightbulb,
      title: "Test a hypothesis",
      note: "Start from an idea or a Library item and see if it holds",
    },
    {
      id: "compare",
      icon: GitCompare,
      title: "Compare versions",
      note: "Two or more versions side by side, then a hybrid",
    },
    {
      id: "train",
      icon: BrainCircuit,
      title: "Train a model",
      note: "Dataset, features, split, train, evaluate, plug in",
    },
    {
      id: "sweep",
      icon: Grid3x3,
      title: "Sweep markets",
      note: "One bot across markets, timeframes and settings",
    },
    {
      id: "workflow",
      icon: Workflow,
      title: "Custom workflow",
      note: "Your own steps: train in a pattern, watch, report",
    },
    {
      id: "import",
      icon: Import,
      title: "Bring in outside work",
      note: "Code from Claude Code or Codex, a notebook, a model file",
    },
  ] as const;
  type Kind = (typeof KINDS)[number]["id"];

  const STEPS: Record<Kind, string[]> = {
    hypothesis: [
      "Write the hypothesis",
      "Pick evidence from the Library",
      "Draft a bot",
      "Backtest",
      "Walk-forward",
      "Decide",
    ],
    compare: [
      "Pick versions",
      "Same data and costs for all",
      "Run each",
      "Compare",
      "Draft a hybrid",
    ],
    train: [
      "Dataset",
      "Features",
      "Split and leakage check",
      "Train",
      "Evaluate",
      "Plug into slots",
    ],
    sweep: [
      "Pick the bot",
      "Markets and timeframes",
      "Parameter ranges",
      "Run the grid",
      "Robustness on winners",
    ],
    workflow: [
      "Name it",
      "Add steps",
      "Choose triggers",
      "Where it runs",
      "Publish",
    ],
    import: [
      "Choose what to bring",
      "Map it to steps or a bot",
      "Check it runs offline",
      "First backtest",
    ],
  };
  const PANELS: Record<Kind, string[]> = {
    hypothesis: ["resources", "editor", "runs", "equity"],
    compare: ["resources", "runs", "equity", "compare"],
    train: ["resources", "training", "logs"],
    sweep: ["resources", "matrix", "runs", "robustness"],
    workflow: ["resources", "editor", "inspector", "logs"],
    import: ["resources", "editor", "inspector", "runs"],
  };

  let step = $state(1);
  let kind = $state<Kind | null>(null);
  let name = $state("");
  let picks = $state<string[]>(["wf-regime"]);
  let dataset = $state("d-fx");
  let env = $state("local");
  let keepTemplate = $state(true);

  const subjects = $derived(
    ASSETS.filter((a) =>
      kind === "train"
        ? a.kind === "model"
        : ["bot", "template", "model"].includes(a.kind),
    ),
  );
  const multi = $derived(kind === "compare");
  const chosen = $derived(KINDS.find((k) => k.id === kind));

  /** These start as a copilot conversation, which then drives the Lab. */
  const COPILOT_LED: Kind[] = ["import", "workflow", "train"];
  function choose(k: Kind) {
    if (COPILOT_LED.includes(k)) {
      open = false;
      // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
      goto(`${resolve("/copilot")}?start=${k}`);
      return;
    }
    kind = k;
    name = KINDS.find((x) => x.id === k)!.title;
    picks = k === "compare" ? ["wf-regime"] : [];
    step = 2;
  }
  function togglePick(id: string) {
    picks = multi
      ? picks.includes(id)
        ? picks.filter((p) => p !== id)
        : [...picks, id]
      : [id];
  }
  function build(k: Kind): TileLayout["root"] {
    const [res, ...rest] = PANELS[k];
    const tiles = rest.map((p, i) => pane(`${k}-${p}-${i}`, p, "teal"));
    const right =
      tiles.length === 1
        ? tiles[0]
        : split(
            "col",
            tiles.map((t) => [t, 100 / tiles.length] as [typeof t, number]),
          );
    return split("row", [
      [pane(`${k}-${res}`, res), 20],
      [
        tiles.length > 2
          ? split("row", [
              [tiles[0], 55],
              [
                split(
                  "col",
                  tiles
                    .slice(1)
                    .map(
                      (t) =>
                        [t, 100 / (tiles.length - 1)] as [typeof t, number],
                    ),
                ),
                45,
              ],
            ])
          : right,
        80,
      ],
    ]);
  }
  function finish() {
    if (!kind) return;
    const l = lab.addLayout({
      id: "",
      name: name.trim() || chosen!.title,
      root: build(kind),
      docked: [],
    });
    open = false;
    workbench.notify(
      keepTemplate
        ? `${l.name} is ready and saved as a template.`
        : `${l.name} is ready.`,
    );
    step = 1;
    kind = null;
  }
  const ready = $derived(
    step !== 2 || picks.length >= (multi ? 2 : kind === "workflow" ? 0 : 1),
  );
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
    <Dialog.Header>
      <Dialog.Title>Start something new</Dialog.Title>
      <Dialog.Description>
        {#if step === 1}What are you setting out to do?{:else if step === 2}{chosen?.title}:
          pick what it works on{:else}Here is what will be set up{/if}
      </Dialog.Description>
    </Dialog.Header>
    <ol class="flex items-center gap-2 text-xs" aria-label="Progress">
      {#each ["What", "Details", "Review"] as label, i (label)}
        <li
          class={cn(
            "flex items-center gap-1.5",
            step === i + 1 ? "text-foreground" : "text-muted-foreground",
          )}
        >
          <span
            class={cn(
              "flex size-5 items-center justify-center rounded-full border text-[11px]",
              step > i + 1 &&
                "bg-primary text-primary-foreground border-primary",
              step === i + 1 && "border-primary",
            )}
          >
            {#if step > i + 1}<Check class="size-3" />{:else}{i + 1}{/if}
          </span>{label}
        </li>
        {#if i < 2}<span class="bg-border h-px w-8"></span>{/if}
      {/each}
    </ol>

    {#if step === 1}
      <div class="grid gap-2 sm:grid-cols-2">
        {#each KINDS as k (k.id)}
          <button
            type="button"
            class="hover:border-ring hover:bg-muted/40 flex items-start gap-3 rounded-lg border p-3 text-left"
            onclick={() => choose(k.id)}
          >
            <k.icon class="text-primary mt-0.5 size-5 shrink-0" />
            <span>
              <span class="block text-sm font-medium">{k.title}</span>
              <span class="text-muted-foreground block text-xs">{k.note}</span>
              {#if COPILOT_LED.includes(k.id)}<span
                  class="text-primary mt-1 flex items-center gap-1 text-xs"
                  ><MessagesSquare class="size-3" />Starts a copilot
                  conversation</span
                >{/if}
            </span>
          </button>
        {/each}
      </div>
    {:else if step === 2}
      <div class="grid gap-4">
        <label class="grid gap-1 text-sm">
          <span class="font-medium">Name</span>
          <input
            bind:value={name}
            maxlength="40"
            class="bg-background/40 h-9 rounded-md border px-3 text-sm"
          />
        </label>
        {#if kind !== "workflow"}
          <div class="grid gap-1.5">
            <span class="text-sm font-medium"
              >{multi
                ? "Versions to compare (two or more)"
                : kind === "train"
                  ? "Model"
                  : "Works on"}</span
            >
            <div class="flex flex-wrap gap-1.5">
              {#each subjects as a (a.id)}
                <button
                  type="button"
                  class={cn(
                    "rounded-md border px-2.5 py-1.5 text-left text-xs",
                    picks.includes(a.id)
                      ? "border-primary bg-primary/15"
                      : "hover:border-ring/60",
                  )}
                  aria-pressed={picks.includes(a.id)}
                  onclick={() => togglePick(a.id)}
                >
                  <span class="block text-sm">{a.name}</span>
                  <span class="text-muted-foreground">{a.meta}</span>
                </button>
              {/each}
              {#if multi}
                <button
                  type="button"
                  class="text-muted-foreground hover:text-foreground rounded-md border border-dashed px-2.5 py-1.5 text-xs"
                  onclick={() =>
                    workbench.notify(
                      "Ask the Lab copilot to draft a hybrid from the versions you picked.",
                    )}>+ Hybrid of the picked versions</button
                >
              {/if}
            </div>
          </div>
        {/if}
        <div class="grid gap-3 sm:grid-cols-2">
          <label class="grid gap-1 text-sm">
            <span class="font-medium">Data</span>
            <select
              bind:value={dataset}
              class="h-9 rounded-md border px-2 text-sm"
            >
              {#each ASSETS.filter((a) => a.kind === "dataset") as d (d.id)}<option
                  value={d.id}>{d.name}</option
                >{/each}
            </select>
          </label>
          <label class="grid gap-1 text-sm">
            <span class="font-medium">Runs on</span>
            <select bind:value={env} class="h-9 rounded-md border px-2 text-sm">
              {#each ENVIRONMENTS as e (e.id)}<option
                  value={e.id}
                  disabled={e.status === "offline"}>{e.name} · {e.where}</option
                >{/each}
            </select>
          </label>
        </div>
      </div>
    {:else if kind}
      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <h3 class="mb-2 text-sm font-medium">Steps</h3>
          <ol class="grid gap-1.5">
            {#each STEPS[kind] as s, i (s)}
              <li class="flex items-center gap-2 text-sm">
                <span class="text-muted-foreground num w-4 text-xs"
                  >{i + 1}</span
                >{s}
              </li>
            {/each}
          </ol>
          <p class="text-muted-foreground mt-2 text-xs">
            Every step can be edited, removed or swapped later, or by the
            copilot.
          </p>
        </div>
        <div>
          <h3 class="mb-2 text-sm font-medium">Opens with</h3>
          <ul class="grid gap-1.5">
            {#each PANELS[kind] as p (p)}
              {@const info = LAB_PANELS[p]}
              <li class="flex items-center gap-2 text-sm">
                <info.icon class="text-muted-foreground size-4" />{info.title}
              </li>
            {/each}
          </ul>
          <label class="mt-4 flex items-center justify-between gap-2 text-sm">
            Keep as a template for next time
            <Switch bind:checked={keepTemplate} />
          </label>
        </div>
      </div>
    {/if}

    <Dialog.Footer class="gap-2">
      {#if step > 1}
        <Button variant="ghost" onclick={() => (step -= 1)}>Back</Button>
      {/if}
      {#if step === 2}
        <Button disabled={!ready} onclick={() => (step = 3)}
          >Review<ArrowRight /></Button
        >
      {:else if step === 3}
        <Button onclick={finish}>Start</Button>
      {/if}
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
