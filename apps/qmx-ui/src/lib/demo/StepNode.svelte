<script lang="ts">
  import { Handle, Position } from "@xyflow/svelte";
  import { cn } from "$lib/utils";
  import type { StepData } from "./workflow";

  let { data, selected }: { data: StepData; selected?: boolean } = $props();

  const ACCENT: Record<StepData["kind"], string> = {
    Data: "var(--chart-1)",
    Feature: "var(--chart-3)",
    Model: "var(--chart-5)",
    Test: "var(--warning)",
    Output: "var(--success)",
  };
  const path = $derived.by(() => {
    const v = data.preview ?? [];
    if (v.length < 2) return "";
    return v
      .map(
        (y, i) =>
          `${i ? "L" : "M"}${((i / (v.length - 1)) * 100).toFixed(1)},${(26 - y * 22).toFixed(1)}`,
      )
      .join(" ");
  });
  const bars = $derived(
    data.kind === "Feature" && (data.preview?.length ?? 0) <= 4,
  );
</script>

<div
  class={cn(
    "surface text-foreground w-56 overflow-hidden rounded-lg text-xs transition-shadow",
    selected && "ring-ring ring-2",
  )}
>
  <div
    class="flex items-center gap-1.5 border-b px-2.5 py-1.5"
    style="border-top: 2px solid {ACCENT[data.kind]}"
  >
    <span class="panel-label">{data.kind}</span>
    {#if data.status}
      <span
        class={cn(
          "ml-auto size-2 rounded-full",
          data.status === "ok" && "bg-success",
          data.status === "warn" && "bg-warning",
          data.status === "stale" && "bg-muted-foreground",
        )}
        title={data.status === "ok"
          ? "Last run fine"
          : data.status === "warn"
            ? "Last run has a warning"
            : "Not run since edit"}
      ></span>
    {/if}
  </div>
  <div class="px-2.5 pt-2">
    <p class="text-[13px] font-semibold">{data.label}</p>
    <p class="text-muted-foreground truncate">{data.detail}</p>
  </div>
  {#if data.preview?.length}
    <svg
      viewBox="0 0 100 28"
      preserveAspectRatio="none"
      class="mt-1.5 block h-8 w-full"
      aria-hidden="true"
    >
      {#if bars}
        {#each data.preview as v, i (i)}
          <rect
            x={6 + i * 31}
            y={28 - v * 60}
            width="24"
            height={v * 60}
            rx="2"
            fill={ACCENT[data.kind]}
            opacity="0.7"
          />
        {/each}
      {:else}
        <path
          d={path}
          fill="none"
          stroke={ACCENT[data.kind]}
          stroke-width="1.5"
          vector-effect="non-scaling-stroke"
        />
      {/if}
    </svg>
  {:else}
    <div class="h-2"></div>
  {/if}
  {#if data.kind !== "Data"}
    <Handle type="target" position={Position.Left} />
  {/if}
  {#if data.kind !== "Output"}
    <Handle type="source" position={Position.Right} />
  {/if}
</div>
