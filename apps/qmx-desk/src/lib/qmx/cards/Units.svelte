<script lang="ts">
  import Thing from "$lib/pages/Thing.svelte";
  import WideRow from "$lib/pages/WideRow.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { positions } from "$lib/shell/desk";
  import type { Obj } from "$lib/shell/model";
  import { panelSize } from "../tiles/panel-size";
  import Fit from "../Fit.svelte";

  // His units on paper and live, grouped by state with a heading and a
  // hairline in its colour (SPACE-RULES 12). Compact: names only. Regular:
  // each with where it runs. Expanded: wide rows with life per market, curve
  // and number. Under them: what is tested and ready, then today's trades.
  const size = panelSize();
  const live = $derived(things.all.filter((o) => o.kind === "unit" && o.word === "live"));
  const paper = $derived(things.all.filter((o) => o.kind === "unit" && (o.word === "paper" || o.word === "paused")));
  const tested = $derived(things.all.filter((o) => o.kind === "unit" && o.word === "tested"));
  const groups = $derived(
    [
      { name: "Live", ink: "var(--live)", items: live },
      { name: "Paper", ink: "var(--paper)", items: paper },
    ].filter((g) => g.items.length),
  );
  type Extra = { id: string; head?: string; unit?: Obj; trade?: ReturnType<typeof positions>["closed"][number] };
  const extra = $derived<Extra[]>([
    ...(tested.length ? [{ id: "h-t", head: "Tested, ready for paper" }, ...tested.map((u) => ({ id: u.id, unit: u }))] : []),
    { id: "h-c", head: "Closed lately" },
    ...positions(things.fixture).closed.map((c) => ({ id: c.id, trade: c })),
  ]);
</script>

<div class="flex h-full min-h-0 flex-col">
  {#if groups.length}
    <div class="min-h-0 flex-[0_1_auto] overflow-x-hidden overflow-y-auto">
      {#each groups as g (g.name)}
        <h4 class="mx-2.5 mt-1 flex items-baseline gap-2 border-b pt-1 pb-1 text-sm font-semibold" style:color={g.ink} style:border-color="color-mix(in oklch, {g.ink} 35%, transparent)">
          {g.name}<span class="num opacity-70">{g.items.length}</span>
        </h4>
        <ul class="mb-1">
          {#each g.items as o (o.id)}
            <li>
              {#if size.mode === "expanded"}<WideRow {o} list="units" />{:else}<Thing {o} list="units" slim={size.mode === "compact"} />{/if}
            </li>
          {/each}
        </ul>
      {/each}
    </div>
  {:else}
    <div class="flex shrink-0 flex-col items-start gap-2 p-2.5">
      <p class="text-muted-foreground">No unit is on paper or live.</p>
      <button class="press border-border h-8 border px-3 text-sm" onclick={() => shell.go("units")}>See tested units</button>
    </div>
  {/if}
  <Fit items={extra} key={(x) => x.id}>
    {#snippet row(x)}
      {#if x.head}
        <h4 class="text-muted-foreground border-border/70 mx-2.5 mt-2 border-t pt-2 pb-0.5 text-sm font-medium">{x.head}</h4>
      {:else if x.unit}
        <Thing o={x.unit} list="units" slim />
      {:else if x.trade}
        {@const t = x.trade}
        <button class="pick flex w-full min-w-0 items-center gap-3 rounded-md px-2.5 py-1.5 text-left text-sm" onclick={() => shell.open({ id: t.unit, list: "units" })}>
          <span class="dot {t.mode === 'live' ? 'text-live' : 'text-paper'}" title={t.mode}></span>
          <span class="min-w-0 flex-1 truncate" title={t.name}>{t.name}</span>
          <span class="num text-muted-foreground shrink-0">{t.sym}</span>
          <span class="num shrink-0 {t.result.startsWith('+') ? 'text-up' : 'text-down'}">{t.result}</span>
          <span class="num text-muted-foreground w-[4.5rem] shrink-0 text-right">{t.at}</span>
        </button>
      {/if}
    {/snippet}
  </Fit>
</div>
