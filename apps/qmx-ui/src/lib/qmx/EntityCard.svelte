<script lang="ts">
  /**
   * Card for a bot, ML model, mini app or workflow. A generated cover, the
   * stage, and four named measures with plain definitions. No overall score:
   * evidence is shown as raw measures.
   */
  import Bot from "@lucide/svelte/icons/bot";
  import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import Workflow from "@lucide/svelte/icons/workflow";
  import CoverArt from "./CoverArt.svelte";
  import { KIND_LABEL, type Entity } from "./entities";
  import { cn } from "$lib/utils";

  let {
    entity,
    href,
    compact = false,
    changed = [],
  }: {
    entity: Entity;
    href?: string;
    compact?: boolean;
    /** Measure keys that changed after an edit; highlighted in place. */
    changed?: string[];
  } = $props();

  const ICON = {
    bot: Bot,
    model: BrainCircuit,
    app: AppWindow,
    workflow: Workflow,
  };
  const Icon = $derived(ICON[entity.kind]);
  const headless = $derived(
    entity.kind === "app" && (entity.views?.length ?? 0) === 0,
  );
  const STAGE_TONE: Record<string, string> = {
    Live: "text-success border-success/40",
    Paper: "text-warning border-warning/40",
    Evidence: "text-info border-info/40",
    Research: "text-info border-info/40",
    Hypothesis: "text-muted-foreground",
    Installed: "text-foreground",
    Draft: "text-muted-foreground",
  };
</script>

<svelte:element
  this={href ? "a" : "div"}
  {href}
  class={cn(
    "surface group flex h-full flex-col overflow-hidden rounded-xl transition-transform",
    href && "hover:-translate-y-0.5 focus-visible:-translate-y-0.5",
  )}
>
  <div class="relative">
    <CoverArt
      kind={entity.kind}
      seed={entity.id}
      series={entity.spark}
      steps={entity.steps?.length ?? 0}
      class={compact ? "h-20 w-full" : "h-28 w-full"}
    />
    <span
      class="bg-background/80 text-foreground absolute top-2 left-2 flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium backdrop-blur"
    >
      <Icon class="size-3" />
      {KIND_LABEL[entity.kind]}{headless ? " · headless" : ""}
    </span>
  </div>
  <div class="flex flex-1 flex-col gap-2 p-3.5">
    <div class="flex items-start gap-2">
      <div class="min-w-0 flex-1">
        <p class="truncate text-[15px] leading-tight font-semibold">
          {entity.name}
        </p>
        <p class="text-muted-foreground line-clamp-2 text-xs">
          {entity.summary}
        </p>
      </div>
      <span
        class={cn(
          "shrink-0 rounded-full border px-2 py-0.5 text-[11px]",
          STAGE_TONE[entity.stage],
        )}
      >
        {entity.stage}
      </span>
    </div>
    <dl class="mt-auto grid grid-cols-2 gap-x-3 gap-y-2 border-t pt-2.5">
      {#each entity.measures.slice(0, 4) as m (m.key)}
        <div
          title={m.help}
          class={cn(
            "rounded-sm",
            changed.includes(m.key) && "bg-warning/15 -mx-1 px-1",
          )}
        >
          <dt class="text-muted-foreground truncate text-[11px]">{m.label}</dt>
          <dd
            class={cn(
              "num text-sm font-semibold",
              m.tone === "up" && "text-success",
              m.tone === "down" && "text-destructive",
            )}
          >
            {m.value}
          </dd>
        </div>
      {/each}
    </dl>
    {#if !compact}
      <p class="text-muted-foreground flex items-center gap-2 text-[11px]">
        <span class="num">{entity.version}</span>
        <span class="num truncate">{entity.fp}</span>
        {#if entity.connections?.length}
          <span class="ml-auto truncate"
            >{entity.connections[0].book} · {entity.connections[0].mode}</span
          >
        {:else if entity.slots?.length}
          <span class="ml-auto truncate">{entity.slots.length} slots</span>
        {:else if entity.ops}
          <span class="ml-auto">{entity.ops.length} operations</span>
        {/if}
      </p>
    {/if}
  </div>
</svelte:element>
