<script lang="ts">
  import { Handle, Position } from "@xyflow/svelte";
  import { cn } from "$lib/utils";
  import type { StepData } from "./workflow";

  let { data, selected }: { data: StepData; selected?: boolean } = $props();

  const ACCENT: Record<StepData["kind"], string> = {
    Data: "bg-chart-1",
    Feature: "bg-chart-3",
    Model: "bg-chart-5",
    Test: "bg-warning",
    Output: "bg-success",
  };
</script>

<div
  class={cn(
    "bg-panel text-foreground w-48 overflow-hidden rounded-md border text-xs shadow-sm",
    selected && "border-ring ring-ring/40 ring-2",
  )}
>
  <div class="flex items-center gap-1.5 border-b px-2 py-1">
    <span class={cn("size-1.5 rounded-full", ACCENT[data.kind])}></span>
    <span class="panel-label">{data.kind}</span>
  </div>
  <div class="px-2 py-1.5">
    <p class="font-medium">{data.label}</p>
    <p class="text-muted-foreground truncate">{data.detail}</p>
  </div>
  {#if data.kind !== "Data"}
    <Handle type="target" position={Position.Left} />
  {/if}
  {#if data.kind !== "Output"}
    <Handle type="source" position={Position.Right} />
  {/if}
</div>
