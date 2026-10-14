<script lang="ts">
  /** What the portfolio holds, by market, across every account (cash includes stablecoins). A report, never used to stop an order. */
  import type { Snippet } from "svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { EXPOSURE } from "../demo";

  /** `lead` sits at the start of the header row (Holdings puts its toggle there). */
  let { lead }: { lead?: Snippet } = $props();
  const size = panelSize();
  const max = Math.max(...EXPOSURE.map((r) => r.share));
  const top = [...EXPOSURE].sort((a, b) => b.share - a.share)[0];
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label={`Largest · ${top.asset}`}
    value={`${top.share}%`}
    status={`${EXPOSURE.length} markets`}
  >
    <ul class="flex flex-col">
      {#each EXPOSURE.slice(0, 5) as r (r.asset)}
        <li class="py-row flex justify-between gap-2 text-xs">
          <span class="truncate">{r.asset}</span><span class="num"
            >{r.share}%</span
          >
        </li>
      {/each}
    </ul>
  </PanelSummary>
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      {#if lead}{@render lead()}{:else}<span
          class="text-muted-foreground text-xs"
          >Share of equity · 12:04 UTC</span
        >{/if}
      <InfoTip
        class="ml-auto"
        label="Explain exposure"
        text="What you hold by market across every account, as a share of total equity. Cash includes stablecoins. A report: each pod's own limits do the stopping."
      />
    </div>
    <div class="px-panel pb-panel min-h-0 flex-1 overflow-auto">
      {#each EXPOSURE as r (r.asset)}
        <div
          class="py-row grid grid-cols-[5.5rem_1fr_3rem] items-center gap-2 text-sm"
        >
          <span class={r.asset === "Cash" ? "text-muted-foreground" : ""}
            >{r.asset}</span
          >
          <span class="bg-muted h-2 overflow-hidden rounded-sm">
            <span
              class="block h-full rounded-sm {r.asset === 'Cash'
                ? 'bg-muted-foreground/50'
                : 'bg-primary/80'}"
              style="width:{(r.share / max) * 100}%"
            ></span>
          </span>
          <span class="num text-right">{r.share}%</span>
        </div>
      {/each}
    </div>
  </div>
{/if}
