<script lang="ts">
  /** The selected block for the pod being designed: its settings as sliders, and whether it is in the pod. */
  import Workflow from "@lucide/svelte/icons/workflow";
  import Plus from "@lucide/svelte/icons/plus";
  import X from "@lucide/svelte/icons/x";
  import { Button } from "$lib/components/ui/button";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { SLOTS, blockById } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";
  import BlockParams from "./BlockParams.svelte";

  const size = panelSize();
  const b = $derived(blockById(lab.block));
  const pod = $derived(podModel.pod(lab.labPod));
  const inPod = $derived(b ? podModel.has(pod.id, b.id) : false);
  const DOCS = {
    yes: "In the docs",
    partial: "Partly in the docs",
    new: "New scope",
  };
</script>

{#if !b}
  <div
    class="text-muted-foreground p-panel flex h-full items-center justify-center text-sm"
  >
    Pick a block in the pod
  </div>
{:else if size.mode === "compact"}
  <PanelSummary
    label={b.name}
    value={podModel.setting(pod.id, b.id)}
    status={inPod ? `In ${pod.name}` : "Not in this pod"}
    tone={inPod ? "good" : "muted"}
  />
{:else}
  <div class="p-panel gap-group flex h-full flex-col overflow-auto">
    <div class="min-w-0">
      <p class="text-muted-foreground text-xs">
        {SLOTS.find((s) => s.id === b.slot)?.label} · {DOCS[b.docs]}
      </p>
      <div class="flex items-center gap-2">
        <h3 class="truncate text-lg font-semibold">{b.name}</h3>
        <InfoTip
          label={`What ${b.name} does`}
          text={`${b.what}. Blocks are pure: same inputs, same answer, so replays are exact.`}
        />
      </div>
    </div>

    <BlockParams pod={pod.id} block={b.id} />

    <div class="mt-auto flex flex-wrap items-center gap-2">
      {#if b.required}
        <span class="text-muted-foreground text-xs">Every pod needs this</span>
      {:else if inPod}
        <Button
          size="sm"
          variant="outline"
          onclick={() =>
            podModel.setStack(
              pod.id,
              b.slot,
              podModel.stack(pod.id)[b.slot].filter((x) => x !== b.id),
            )}><X />Remove from {pod.name}</Button
        >
      {:else}
        <Button
          size="sm"
          variant="outline"
          onclick={() =>
            podModel.setStack(pod.id, b.slot, [
              ...podModel.stack(pod.id)[b.slot],
              b.id,
            ])}><Plus />Add to {pod.name}</Button
        >
      {/if}
      {#if b.kind === "graph" || b.kind === "code"}
        <Button
          size="sm"
          variant="ghost"
          onclick={() =>
            workbench.notify(`${b.name} opens in the editor (Build layout).`)}
          ><Workflow />Open in the editor</Button
        >
      {/if}
    </div>
  </div>
{/if}
