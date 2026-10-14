<script lang="ts">
  /** Every pod as a card (things you own): money, room above its kill line, how it sizes, paused or trading. Click to steer it in the Pod panel. */
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { PODS, accountById } from "../demo";
  import { MODE_BORDER, pct, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";
  import { methodOf, podSim } from "../pod-sim.svelte";

  const size = panelSize();
  const views = $derived(
    PODS.filter(
      (p) =>
        portfolio.world === "all" ||
        (portfolio.world === "live" ? p.mode === "LIVE" : true),
    ).map((p) => podSim.view(p.id)),
  );
  const total = $derived(views.reduce((t, v) => t + v.equity, 0));
  const paused = $derived(views.filter((v) => v.paused).length);
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label={`${views.length} pods`}
    value={usd(total)}
    status={paused ? `${paused} paused` : "All trading"}
    tone={paused ? "warn" : "good"}
  >
    <ul class="flex flex-col">
      {#each views as v (v.pod.id)}
        <li>
          <button
            type="button"
            class={cn(
              "hover:bg-muted py-row flex w-full items-center gap-2 rounded px-1.5 text-left text-sm",
              portfolio.pod === v.pod.id && "bg-muted",
            )}
            aria-pressed={portfolio.pod === v.pod.id}
            onclick={() => (portfolio.pod = v.pod.id)}
          >
            <span
              class="size-2 shrink-0 rounded-full"
              style="background: var(--tone-{v.pod.mode === 'LIVE'
                ? 'live'
                : 'paper'})"
            ></span>
            <span class="min-w-0 flex-1 truncate">{v.pod.name}</span>
            {#if v.paused}<span class="text-warning text-xs">Paused</span>{/if}
          </button>
        </li>
      {/each}
    </ul>
  </PanelSummary>
{:else}
  <div
    class="gap-tile p-tile grid h-full content-start overflow-auto [grid-template-columns:repeat(auto-fill,minmax(15rem,1fr))]"
  >
    {#each views as v (v.pod.id)}
      {@const p = v.pod}
      <button
        type="button"
        class={cn(
          "hover:bg-muted/40 p-panel flex flex-col gap-3 rounded-xl border-2 text-left transition-colors",
          portfolio.pod === p.id && "bg-muted/50",
          v.paused && "opacity-70",
        )}
        style="border-color: {p.mode === 'LIVE'
          ? MODE_BORDER.live
          : MODE_BORDER.paper}"
        aria-pressed={portfolio.pod === p.id}
        aria-label={`${p.name}${v.paused ? ", paused" : ""}`}
        onclick={() => (portfolio.pod = p.id)}
      >
        <span class="flex items-center gap-2">
          <span class="truncate text-base font-semibold">{p.name}</span>
          <span
            class={cn(
              "ml-auto shrink-0 text-xs",
              v.paused ? "text-warning" : "text-muted-foreground",
            )}
            >{v.paused ? "Paused" : p.mode === "LIVE" ? "Live" : "Paper"}</span
          >
        </span>
        <span class="block h-10"
          ><Sparkline values={v.curve} class="block h-full w-full" /></span
        >
        <span class="flex items-baseline gap-2">
          <span class="num text-xl font-semibold">{usd(v.equity)}</span>
          <span
            class={cn(
              "num text-sm",
              v.today >= 0 ? "text-success" : "text-destructive",
            )}>{pct(v.today)}</span
          >
        </span>
        <span
          class="bg-muted block h-1.5 overflow-hidden rounded-full"
          title={`${usd(v.room)} above the kill line`}
          ><span
            class={cn(
              "block h-full",
              v.roomShare < 0.25 ? "bg-destructive" : "bg-success",
            )}
            style="width:{Math.min(1, v.roomShare) * 100}%"
          ></span></span
        >
        <span class="text-muted-foreground flex gap-2 text-xs">
          <span class="truncate">{methodOf(v.method).label}</span>
          <span class="ml-auto shrink-0"
            >{accountById(p.account)?.name} · {p.bots.length} bot{p.bots
              .length === 1
              ? ""
              : "s"}</span
          >
        </span>
      </button>
    {/each}
    <button
      type="button"
      class="hover:border-ring text-muted-foreground hover:text-foreground flex min-h-40 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed text-sm"
      onclick={() => (portfolio.templatesOpen = true)}
      ><Plus class="size-5" />New pod</button
    >
  </div>
{/if}
