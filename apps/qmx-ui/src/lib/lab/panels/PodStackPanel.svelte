<script lang="ts">
  /**
   * A pod as a stack: seven slots in a fixed order, each holding blocks.
   * Add, remove and pick blocks; each chip shows its live settings
   * (podModel). Edits make a draft; Save mints the next version; Send to
   * paper checks the pod and moves it to paper (demo, in the browser).
   * Expanded, the selected block's sliders open under its slot.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import X from "@lucide/svelte/icons/x";
  import Workflow from "@lucide/svelte/icons/workflow";
  import Code from "@lucide/svelte/icons/code";
  import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
  import Send from "@lucide/svelte/icons/send";
  import Undo2 from "@lucide/svelte/icons/undo-2";
  import CircleCheck from "@lucide/svelte/icons/circle-check";
  import CircleDashed from "@lucide/svelte/icons/circle-dashed";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import * as Popover from "$lib/components/ui/popover";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { BLOCKS, LAB_PODS, SLOTS, STAGE_LABEL, blockById } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";
  import BlockParams from "./BlockParams.svelte";

  const size = panelSize();
  const pod = $derived(podModel.pod(lab.labPod));
  const stack = $derived(podModel.stack(pod.id));
  const dirty = $derived(podModel.isDirty(pod.id));
  const KIND_ICON = {
    form: null,
    graph: Workflow,
    code: Code,
    model: BrainCircuit,
  };
  const blockCount = $derived(Object.values(stack).flat().length);
  const checks = $derived([
    { label: "Saved", done: !dirty },
    { label: "Kill line set", done: podModel.has(pod.id, "kill") },
    {
      label: "Stress board run",
      done: lab.stressTicked.every((s) => podModel.stress(pod.id, s)),
    },
  ]);
  const canSend = $derived(
    checks.every((c) => c.done) && !podModel.onPaper(pod.id),
  );
  const SLOT_HELP =
    "Seven slots, always in this order: inputs (what the pod looks at), guards (can stop everything), allocator (splits money between bots), sizer (turns an entry into a size), throttles (shrink size ×0 to ×1), caps (hard limits) and ledger (capital, periods, fees). Venue fit always runs last: lot size, minimum order, fees.";
</script>

{#snippet chip(id: string, slot: (typeof SLOTS)[number])}
  {@const b = blockById(id)}
  {#if b}
    {@const Icon = KIND_ICON[b.kind]}
    <span
      class={cn(
        "flex items-center rounded-md border text-sm",
        lab.block === id
          ? "border-primary bg-primary/12"
          : "bg-background/40 hover:border-ring/60",
      )}
    >
      <button
        type="button"
        class="flex items-center gap-1.5 py-1 pr-1 pl-2.5 text-left"
        aria-pressed={lab.block === id}
        onclick={() => (lab.block = id)}
      >
        {#if Icon}<Icon class="text-info size-3.5" />{/if}
        <span>{b.name}</span>
        <span class="text-muted-foreground num text-xs"
          >{podModel.setting(pod.id, id)}</span
        >
      </button>
      {#if !b.required}
        <button
          type="button"
          class="text-muted-foreground hover:text-destructive px-1.5 py-1"
          aria-label={`Remove ${b.name}`}
          onclick={() =>
            podModel.setStack(
              pod.id,
              slot.id,
              stack[slot.id].filter((x) => x !== id),
            )}><X class="size-3.5" /></button
        >
      {/if}
    </span>
  {/if}
{/snippet}

{#if size.mode === "compact"}
  <PanelSummary
    label={`${pod.name} ${podModel.version(pod.id)}`}
    value={podModel.setting(pod.id, stack.sizer[0])}
    status={`Kill −${podModel.kill(pod.id)}% · ${blockCount} blocks${dirty ? " · draft" : ""}`}
    tone={dirty ? "warn" : "muted"}
    values={podModel.equity(pod.id).curve}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-1">
      {#each LAB_PODS as p (p.id)}
        <button
          type="button"
          class={cn(
            "flex h-7 min-w-0 items-center gap-1.5 rounded-md px-2.5 text-sm",
            lab.labPod === p.id
              ? "bg-muted font-medium"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-pressed={lab.labPod === p.id}
          onclick={() => (lab.labPod = p.id)}
          ><span
            class="size-2 shrink-0 rounded-full"
            style="background:{p.color}"
          ></span><span class="truncate">{p.name}</span></button
        >
      {/each}
      <span class="ml-auto flex shrink-0 items-center gap-1">
        <span class="text-muted-foreground num hidden text-xs @lg:inline"
          >{podModel.version(pod.id)} · {STAGE_LABEL[
            podModel.stage(pod.id)
          ]}</span
        >
        <InfoTip label="Explain the slots" text={SLOT_HELP} />
      </span>
    </div>
    <ol class="px-panel min-h-0 flex-1 overflow-auto">
      {#each SLOTS as s (s.id)}
        <li class="py-row border-t first:border-t-0">
          <div class="flex items-start gap-3 py-1">
            <p class="w-24 shrink-0 pt-1 text-sm font-medium">{s.label}</p>
            <div class="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
              {#each stack[s.id] as id (id)}
                {@render chip(id, s)}
              {:else}
                <span class="text-muted-foreground text-xs">Empty</span>
              {/each}
              <DropdownMenu.Root>
                <DropdownMenu.Trigger
                  class="text-muted-foreground hover:text-foreground hover:bg-muted flex size-7 items-center justify-center rounded-md border border-dashed"
                  aria-label={`Add to ${s.label}`}
                >
                  <Plus class="size-3.5" />
                </DropdownMenu.Trigger>
                <DropdownMenu.Content class="w-72">
                  <DropdownMenu.Label>{s.label}</DropdownMenu.Label>
                  {#each BLOCKS.filter((b) => b.slot === s.id && !stack[s.id].includes(b.id)) as b (b.id)}
                    <DropdownMenu.Item
                      onclick={() => {
                        podModel.setStack(pod.id, s.id, [...stack[s.id], b.id]);
                        lab.block = b.id;
                      }}
                    >
                      <span class="flex flex-col"
                        ><span>{b.name}</span><span
                          class="text-muted-foreground text-xs">{b.what}</span
                        ></span
                      >
                    </DropdownMenu.Item>
                  {/each}
                  <DropdownMenu.Separator />
                  <DropdownMenu.Item
                    onclick={() =>
                      workbench.notify(
                        "A new graph block opens in the editor with this slot's inputs and outputs placed.",
                      )}><Workflow />New block as a graph</DropdownMenu.Item
                  >
                  <DropdownMenu.Item
                    onclick={() =>
                      workbench.notify(
                        "A Python stub with this slot's signature opens in the code editor.",
                      )}><Code />New block as code</DropdownMenu.Item
                  >
                  <DropdownMenu.Item
                    onclick={() =>
                      workbench.notify(
                        "Pick or import a model; it plugs into this slot under a rule ceiling.",
                      )}><BrainCircuit />Use a model</DropdownMenu.Item
                  >
                </DropdownMenu.Content>
              </DropdownMenu.Root>
            </div>
          </div>
          {#if size.mode === "expanded" && stack[s.id].includes(lab.block)}
            <div class="mb-row ml-27 max-w-xl">
              <BlockParams pod={pod.id} block={lab.block} />
            </div>
          {/if}
        </li>
      {/each}
    </ol>
    <div
      class="px-panel py-row flex shrink-0 flex-wrap items-center gap-2 border-t"
    >
      {#if dirty}
        <span class="text-sm font-medium"
          >Draft {podModel.version(pod.id, 1)}</span
        >
        <Button
          size="sm"
          variant="ghost"
          onclick={() => podModel.discard(pod.id)}><Undo2 />Discard</Button
        >
        <Button
          size="sm"
          variant="outline"
          onclick={() =>
            workbench.notify(`${pod.name} ${podModel.save(pod.id)} saved.`)}
          >Save {podModel.version(pod.id, 1)}</Button
        >
      {/if}
      <Popover.Root>
        <Popover.Trigger>
          {#snippet child({ props })}
            <Button {...props} size="sm" class="ml-auto"
              ><Send />Send to paper</Button
            >
          {/snippet}
        </Popover.Trigger>
        <Popover.Content align="end" class="w-72">
          <ul class="gap-row mb-panel flex flex-col text-sm">
            {#each checks as c (c.label)}
              <li class="flex items-center gap-2">
                {#if c.done}<CircleCheck
                    class="text-success size-4"
                  />{:else}<CircleDashed
                    class="text-muted-foreground size-4"
                  />{/if}{c.label}
              </li>
            {/each}
          </ul>
          <Button
            size="sm"
            class="w-full"
            disabled={!canSend}
            onclick={() => {
              podModel.sendToPaper(pod.id);
              workbench.notify(
                `${pod.name} ${podModel.version(pod.id)} is on paper.`,
              );
            }}
            ><Send />{podModel.onPaper(pod.id)
              ? `${podModel.version(pod.id)} is on paper`
              : `Send ${podModel.version(pod.id)} to paper`}</Button
          >
        </Popover.Content>
      </Popover.Root>
    </div>
  </div>
{/if}
