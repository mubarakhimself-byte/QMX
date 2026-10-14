<script lang="ts">
  /** How the pods move together (daily P&L). Above 0.7 is flagged: two pods doing the same thing. */
  import type { Snippet } from "svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { CORR } from "../demo";

  /** `lead` sits at the start of the header row (Holdings puts its toggle there). */
  let { lead }: { lead?: Snippet } = $props();
  const size = panelSize();
  const fill = (v: number) =>
    `color-mix(in oklab, ${v >= 0.7 ? "var(--destructive)" : "var(--primary)"} ${Math.round(Math.abs(v) * 70)}%, transparent)`;
  const pairs = CORR.m
    .flatMap((row, i) =>
      row.map((v, j) => ({ a: CORR.names[i], b: CORR.names[j], v, i, j })),
    )
    .filter((x) => x.i < x.j)
    .sort((x, y) => y.v - x.v);
  const flagged = pairs.filter((x) => x.v >= 0.7).length;
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label={`${pairs[0].a} · ${pairs[0].b}`}
    value={pairs[0].v.toFixed(2)}
    status={flagged ? `${flagged} pair above 0.7` : "No pair above 0.7"}
    tone={flagged ? "bad" : "good"}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      {#if lead}{@render lead()}{:else}<span
          class="text-muted-foreground text-xs">Daily P&L, 90 days</span
        >{/if}
      <InfoTip
        class="ml-auto"
        label="Explain correlation"
        text="How the pods' daily profit and loss move together. Red cells are above 0.7: two pods doing the same thing. Here Alt momentum and Weekly rotation both lean on the same large alts."
      />
    </div>
    <div class="px-panel pb-panel min-h-0 flex-1 overflow-auto">
      <div
        class="grid h-full gap-1"
        style="grid-template-columns: 6rem repeat({CORR.names
          .length}, minmax(0, 1fr)); grid-template-rows: 1.5rem repeat({CORR
          .names.length}, minmax(2rem, 1fr))"
      >
        <span></span>
        {#each CORR.names as n (n)}<span
            class="text-muted-foreground truncate text-center text-xs"
            title={n}>{n}</span
          >{/each}
        {#each CORR.m as row, i (i)}
          <span class="text-muted-foreground self-center truncate text-xs"
            >{CORR.names[i]}</span
          >
          {#each row as v, j (j)}
            <span
              class="num flex items-center justify-center rounded text-xs"
              style="background:{i === j ? 'var(--muted)' : fill(v)}"
              >{i === j ? "" : v.toFixed(2)}</span
            >
          {/each}
        {/each}
      </div>
    </div>
  </div>
{/if}
