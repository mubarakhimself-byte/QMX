<script lang="ts">
  /**
   * Draws a panel description (lib/sdk/spec.ts) with QMX's own parts. An
   * invalid description shows what is wrong instead of breaking the screen
   * (crash containment, as in bb). Buttons dispatch operation ids to the
   * host; nothing in a description is ever run as code.
   */
  import CircleAlert from "@lucide/svelte/icons/circle-alert";
  import Info from "@lucide/svelte/icons/info";
  import TriangleAlert from "@lucide/svelte/icons/triangle-alert";
  import { Button } from "$lib/components/ui/button";
  import LineChart from "$lib/qmx/LineChart.svelte";
  import { equityWalk } from "$lib/qmx/charts";
  import { cn } from "$lib/utils";
  import { validate, type PanelSpec } from "./spec";

  let {
    spec,
    onaction,
  }: {
    spec: PanelSpec;
    onaction?: (op: string) => void;
  } = $props();

  const errors = $derived(validate(spec));
  const str = (v: unknown) => (v === undefined || v === null ? "" : String(v));
  const TONE: Record<string, string> = {
    up: "text-success",
    down: "text-destructive",
    plain: "",
  };
</script>

{#snippet node(id: string)}
  {@const el = spec.elements[id]}
  {@const p = el.props ?? {}}
  {#if el.type === "Stack"}
    <div
      class={cn(
        "flex gap-3",
        p.direction === "row" ? "flex-row flex-wrap" : "flex-col",
      )}
    >
      {#each el.children ?? [] as c (c)}{@render node(c)}{/each}
    </div>
  {:else if el.type === "Grid"}
    <div
      class="grid gap-2"
      style="grid-template-columns: repeat(auto-fit, minmax({Number(
        p.min ?? 9,
      )}rem, 1fr))"
    >
      {#each el.children ?? [] as c (c)}{@render node(c)}{/each}
    </div>
  {:else if el.type === "Heading"}
    <h3 class="text-base font-semibold">{str(p.text)}</h3>
  {:else if el.type === "Text"}
    <p class="text-sm">{str(p.text)}</p>
  {:else if el.type === "Metric"}
    <div class="rounded-lg border px-3 py-2">
      <p class="text-muted-foreground text-[13px]">{str(p.label)}</p>
      <p class={cn("num text-xl font-semibold", TONE[str(p.tone)] ?? "")}>
        {str(p.value)}
      </p>
    </div>
  {:else if el.type === "Table"}
    <div class="overflow-x-auto rounded-lg border">
      <table class="w-full text-sm">
        <thead class="text-muted-foreground text-left text-[13px]">
          <tr>
            {#each (p.columns as unknown[]) ?? [] as h, i (i)}<th
                class={cn("px-3 py-2 font-medium", i && "text-right")}
                >{str(h)}</th
              >{/each}
          </tr>
        </thead>
        <tbody>
          {#each (p.rows as unknown[][]) ?? [] as r, i (i)}
            <tr class="border-t">
              {#each r as v, k (k)}<td
                  class={cn("px-3 py-2", k && "num text-right")}>{str(v)}</td
                >{/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else if el.type === "LineChart"}
    {@const series = (
      (p.series as {
        label: string;
        seed?: number;
        values?: number[];
        color?: string;
      }[]) ?? []
    ).map((s, i) => ({
      label: s.label,
      values: s.values ?? equityWalk(s.seed ?? 100 + i, 80, 0.0015, 0.012),
      color: s.color ?? `var(--chart-${(i % 5) + 1})`,
    }))}
    <div class="h-44"><LineChart {series} height={160} /></div>
  {:else if el.type === "Badge"}
    <span class="w-fit rounded border px-2 py-0.5 text-[13px]"
      >{str(p.text)}</span
    >
  {:else if el.type === "Callout"}
    {@const Icon =
      p.tone === "danger"
        ? CircleAlert
        : p.tone === "warning"
          ? TriangleAlert
          : Info}
    <p
      class={cn(
        "flex items-start gap-2 rounded-lg border px-3 py-2 text-sm",
        p.tone === "danger"
          ? "border-destructive/50"
          : p.tone === "warning"
            ? "border-warning/50"
            : "border-info/40",
      )}
    >
      <Icon class="mt-0.5 size-4 shrink-0" />{str(p.text)}
    </p>
  {:else if el.type === "Button"}
    <Button
      size="sm"
      variant="outline"
      class="w-fit"
      onclick={() => onaction?.(str(p.action))}>{str(p.label)}</Button
    >
  {/if}
{/snippet}

{#if errors.length}
  <div class="border-destructive/50 rounded-lg border p-3 text-sm" role="alert">
    <p class="text-destructive flex items-center gap-2 font-medium">
      <CircleAlert class="size-4" />This panel can't be drawn
    </p>
    <ul class="text-muted-foreground mt-1 list-disc pl-5 text-[13px]">
      {#each errors.slice(0, 6) as e (e)}<li>{e}</li>{/each}
    </ul>
  </div>
{:else}
  <div class="min-w-0">{@render node(spec.root)}</div>
{/if}
