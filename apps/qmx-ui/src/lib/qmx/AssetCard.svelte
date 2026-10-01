<script lang="ts" module>
  export type AssetKind = "bot" | "model" | "app" | "workflow";
  export type Attribute = { key: string; label: string; value: number };
  export type Asset = {
    id: string;
    kind: AssetKind;
    name: string;
    role: string;
    stage: "Research" | "Paper" | "Live" | "Installed" | "Draft";
    rating: number;
    attributes: Attribute[];
    spark?: number[];
    tags?: string[];
  };
</script>

<script lang="ts">
  /**
   * Player-card view of a QMX asset (bot, ML model, mini app, workflow),
   * after sports-game player cards: one overall rating, six attributes,
   * a tier by rating. Ratings come from the asset's own metrics; the card
   * only displays them.
   */
  import Bot from "@lucide/svelte/icons/bot";
  import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
  import AppWindow from "@lucide/svelte/icons/app-window";
  import Workflow from "@lucide/svelte/icons/workflow";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { cn } from "$lib/utils";

  let {
    asset,
    selected = false,
    onselect,
  }: { asset: Asset; selected?: boolean; onselect?: () => void } = $props();

  const ICON = {
    bot: Bot,
    model: BrainCircuit,
    app: AppWindow,
    workflow: Workflow,
  };
  const KIND = {
    bot: "Bot",
    model: "ML model",
    app: "Mini app",
    workflow: "Workflow",
  };
  const tier = $derived(
    asset.rating >= 85 ? "gold" : asset.rating >= 75 ? "silver" : "bronze",
  );
  const FOIL = {
    gold: "from-[#f6d27a]/35 via-[#b8862f]/15 to-transparent",
    silver: "from-[#dfe6ee]/30 via-[#8d99a8]/12 to-transparent",
    bronze: "from-[#e0a070]/30 via-[#8a5a35]/12 to-transparent",
  };
  const RING = {
    gold: "ring-[#e8c46a]/60",
    silver: "ring-[#c8d1dc]/45",
    bronze: "ring-[#d29567]/45",
  };
  const Icon = $derived(ICON[asset.kind]);
</script>

<button
  type="button"
  onclick={onselect}
  aria-pressed={selected}
  aria-label={`${asset.name}, ${KIND[asset.kind]}, rating ${asset.rating}`}
  class={cn(
    "surface group relative flex w-full flex-col overflow-hidden rounded-xl text-left ring-1 transition-transform hover:-translate-y-0.5",
    RING[tier],
    selected && "ring-2",
  )}
>
  <div
    class={cn(
      "pointer-events-none absolute inset-0 bg-linear-to-br",
      FOIL[tier],
    )}
  ></div>
  <div class="relative flex items-start gap-3 p-3 pb-2">
    <div class="flex flex-col items-center">
      <span class="num text-3xl leading-none font-semibold">{asset.rating}</span
      >
      <span class="panel-label mt-1">{tier}</span>
    </div>
    <div class="min-w-0 flex-1">
      <div class="text-muted-foreground flex items-center gap-1.5 text-xs">
        <Icon class="size-3.5" />
        {KIND[asset.kind]} · {asset.stage}
      </div>
      <p class="mt-0.5 truncate text-[15px] font-semibold">{asset.name}</p>
      <p class="text-muted-foreground truncate text-xs">{asset.role}</p>
    </div>
  </div>
  {#if asset.spark}
    <Sparkline values={asset.spark} class="relative h-8 w-full px-3" />
  {/if}
  <dl class="relative grid grid-cols-3 gap-x-3 gap-y-1.5 border-t p-3">
    {#each asset.attributes as a (a.key)}
      <div class="flex items-baseline justify-between gap-1" title={a.label}>
        <dt
          class="text-muted-foreground text-[11px] font-medium tracking-wider"
        >
          {a.key}
        </dt>
        <dd
          class={cn(
            "num text-sm font-semibold",
            a.value >= 85
              ? "text-success"
              : a.value < 60
                ? "text-destructive"
                : "",
          )}
        >
          {a.value}
        </dd>
      </div>
    {/each}
  </dl>
</button>
