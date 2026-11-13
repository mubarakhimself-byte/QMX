<script lang="ts">
  import * as Menu from "$lib/components/ui/dropdown-menu";
  import Icon from "$lib/qmx/Icon.svelte";
  import Spark from "$lib/qmx/Spark.svelte";
  import Stats from "$lib/qmx/Stats.svelte";
  import { tone } from "$lib/qmx/state";
  import Life from "./Life.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import type { Obj } from "$lib/shell/model";

  // One decision: the evidence and the button on one screen, nothing else.
  let { o }: { o: Obj } = $props();
  const ev = $derived(o.evidence!);
  const unit = $derived(things.get(ev.unit));
  const market = $derived(unit?.markets?.find((m) => m.sym === ev.sym) ?? { sym: ev.sym, life: ev.from });
  const done = $derived(things.decision(o.id));
  const reasons = ["Needs more trades", "Test another period", "Costs look too high", "I want to read the journal first"];
</script>

<article class="decide flex h-full min-h-0 flex-col overflow-x-hidden overflow-y-auto">
  <header class="hd shrink-0 px-6 pt-5 pb-4">
    <p class="text-muted-foreground flex min-w-0 items-center gap-2 text-sm">
      <span class="dot {tone[o.tone]}"></span>
      <span class="shrink-0">Proposal</span><span aria-hidden="true">·</span>
      <span class="truncate">from {ev.by}, {o.when} ago</span>
    </p>
    <h1 class="ttl display mt-1 line-clamp-2 text-4xl leading-[1.05] font-semibold [overflow-wrap:anywhere]" title={o.name}>{o.name}</h1>
    <div class="mt-4 max-w-[46rem]">
      <Life market={done === "promoted" ? market : { ...market, life: ev.from }} target={done ? undefined : ev.to} big />
    </div>
  </header>

  <div class="ev grid flex-1 gap-[var(--gap)] px-6 pb-4">
    <!-- What the judge says, and every try it counted. -->
    <section class="surface flex min-h-0 flex-col overflow-hidden" aria-label="The judge">
      <header class="flex h-11 shrink-0 items-center gap-2 px-3">
        <Icon name="scale" class="text-muted-foreground" /><h3 class="font-medium">The judge</h3>
      </header>
      <div class="min-h-0 flex-1 overflow-y-auto px-3 pb-3">
        <p class="display text-4xl font-semibold {tone[ev.verdictTone]}">{ev.verdict}</p>
        <p class="text-muted-foreground mt-1">{ev.judge}</p>
        <p class="mt-4 mb-1 text-sm font-medium">{ev.tries.length} {ev.tries.length === 1 ? "try" : "tries"} counted</p>
        <ol class="flex flex-col">
          {#each ev.tries as t (t.n)}
            <li class="border-border/60 flex min-w-0 items-center gap-3 border-t py-1.5">
              <span class="num text-muted-foreground w-5 shrink-0 text-sm">{t.n}</span>
              <span class="min-w-0 flex-1 truncate" title={t.what}>{t.what}</span>
              <span class="num shrink-0 {t.tone ? tone[t.tone] : ''}">{t.result}</span>
            </li>
          {/each}
        </ol>
      </div>
    </section>

    <section class="surface chart flex min-h-0 flex-col overflow-hidden" aria-label="Result">
      <header class="flex h-11 shrink-0 items-center gap-2 px-3">
        <Icon name="line-chart" class="text-muted-foreground" /><h3 class="font-medium">Result on {ev.sym}</h3>
        <span class="text-muted-foreground ml-auto text-sm">backtest, costs in</span>
      </header>
      <div class="min-h-0 flex-1" style:--line={ev.to === "live" ? "var(--paper)" : undefined}>
        <Spark series={ev.series} />
      </div>
      <div class="shrink-0 [&_dl]:grid-cols-4 [&_dl]:gap-x-4 [&_dd]:text-xl [&_dt]:truncate">
        <Stats stats={ev.stats} />
      </div>
    </section>

    <section class="surface flex min-h-0 flex-col overflow-hidden" aria-label="Costs">
      <header class="flex h-11 shrink-0 items-center gap-2 px-3">
        <Icon name="gauge" class="text-muted-foreground" /><h3 class="font-medium">Costs</h3>
      </header>
      <dl class="min-h-0 flex-1 overflow-y-auto px-3 pb-3">
        {#each ev.costs as [k, v, t] (k)}
          <div class="border-border/60 flex min-w-0 items-baseline justify-between gap-3 border-t py-2 first:border-t-0">
            <dt class="text-muted-foreground min-w-0 truncate">{k}</dt>
            <dd class="num shrink-0 text-lg {t ? tone[t] : ''}">{v}</dd>
          </div>
        {/each}
      </dl>
    </section>
  </div>

  <!-- The decision. Always at the foot of the evidence, never a scroll away. -->
  <footer class="border-border bg-panel sticky bottom-0 z-10 flex shrink-0 flex-wrap items-center gap-x-4 gap-y-2 border-t px-6 py-3">
    {#if done}
      <span class="flex min-w-0 flex-1 items-center gap-2">
        <span class="dot {done === 'promoted' ? 'text-up' : 'text-idle'}"></span>
        <span class="truncate">{done === "promoted" ? `Promoted. ${ev.sym} is on ${ev.to}.` : "Left for later. The proposal stays in the Library."}</span>
      </span>
      {#if unit}
        <button class="press border-border h-10 gap-2 border px-4" onclick={() => shell.open({ id: unit.id })}>Open {unit.name.length > 28 ? "the unit" : unit.name}<Icon name="arrow-right" /></button>
      {/if}
    {:else}
      <div class="min-w-0 flex-1">
        <p class="truncate font-medium">{ev.to === "live" ? "Real money" : "Demo money"} on {ev.sym}</p>
        <p class="text-muted-foreground flex min-w-0 items-center gap-1.5 text-sm">
          <Icon name={ev.node.includes("This PC") ? "laptop" : "server"} class="size-3.5 shrink-0" /><span class="truncate" title={ev.node}>{ev.node}</span>
        </p>
      </div>
      <Menu.Root>
        <Menu.Trigger>
          {#snippet child({ props })}
            <button {...props} class="press border-border h-11 gap-2 border px-4 text-base">Not yet<Icon name="chevron-down" class="size-3.5" /></button>
          {/snippet}
        </Menu.Trigger>
        <Menu.Content side="top" align="end" class="w-72">
          <Menu.Label>Why not yet</Menu.Label>
          {#each reasons as r (r)}
            <Menu.Item onclick={() => things.later(o, r)}>{r}</Menu.Item>
          {/each}
        </Menu.Content>
      </Menu.Root>
      <button
        class="h-11 shrink-0 rounded-md px-5 text-base font-semibold whitespace-nowrap transition-transform duration-100 active:scale-[0.97]"
        style:background={ev.to === "live" ? "var(--live)" : "var(--paper)"}
        style:color="var(--background)"
        onclick={() => things.promote(o)}
      >
        Promote to {ev.to}
      </button>
    {/if}
  </footer>
</article>

<style>
  .decide {
    container-type: inline-size;
  }
  .ev {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.7fr) minmax(0, 1fr);
    min-height: 16rem;
  }
  /* A short window: the title takes one line so the evidence keeps its room. */
  @media (max-height: 820px) {
    .ttl {
      -webkit-line-clamp: 1;
      line-clamp: 1;
      font-size: 2rem;
    }
    .hd {
      padding-top: 0.75rem;
      padding-bottom: 0.75rem;
    }
  }
  @container (max-width: 50rem) {
    .ev {
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      grid-template-rows: 20rem;
      grid-auto-rows: minmax(14rem, auto);
      overflow-y: auto;
    }
    .ev .chart {
      grid-column: span 2;
      grid-row: 1;
      height: 20rem;
    }
  }
</style>
