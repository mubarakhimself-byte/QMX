<script lang="ts">
  import { things } from "$lib/shell/things.svelte";
  import { pods, positions, type Pod } from "$lib/shell/desk";
  import { panelSize } from "../tiles/panel-size";
  import Fit from "../Fit.svelte";

  // Pods: his units grouped by trading style, each with its own risk rule.
  // The portfolio at a glance: each pod's live and paper result today and how
  // much room it has before its day stop. Compact: one line per pod. Regular:
  // the two sides and the room bar. Expanded: its units and rules too.
  // A pod's own page waits for the pods section; rows do not open yet.
  const size = panelSize();
  const list = $derived(pods(things.fixture));
  const name = (id: string) => things.get(id)?.name ?? id;
  const sign = (s: string) => (s.startsWith("+") ? "text-up" : s.startsWith("-") ? "text-down" : "text-muted-foreground");
  const roomTone = (p: Pod) => (p.room.left / p.room.stop < 0.25 ? "var(--down)" : p.room.left / p.room.stop < 0.6 ? "var(--paper)" : "var(--up)");
  const podOf = (unit: string) => list.find((p) => p.units.includes(unit));
  const closed = $derived(positions(things.fixture).closed.filter((c) => podOf(c.unit)));
</script>

{#snippet room(p: Pod, wide: boolean)}
  <span class="flex min-w-0 items-center gap-2 {wide ? 'w-full' : ''}" title="{p.room.left}R of {p.room.stop}R left before the day stop">
    <span class="bg-foreground/10 relative h-1.5 min-w-10 flex-1 overflow-hidden rounded-full">
      <span class="absolute inset-y-0 left-0 rounded-full" style:width="{(p.room.left / p.room.stop) * 100}%" style:background={roomTone(p)}></span>
    </span>
    <span class="num text-muted-foreground shrink-0 text-sm">{p.room.left}R<span class="opacity-60">/{p.room.stop}</span></span>
  </span>
{/snippet}

{#snippet side(label: string, s: { today: string; open: number } | null, ink: string)}
  <span class="flex min-w-0 items-baseline gap-1.5 text-sm">
    <span class="shrink-0 text-xs font-semibold uppercase" style:color={s ? ink : "var(--idle)"}>{label}</span>
    {#if s}<span class="num whitespace-nowrap {sign(s.today)}">{s.today}</span>{#if size.mode === "expanded"}<span class="text-muted-foreground whitespace-nowrap">· {s.open} open</span>{/if}{:else}<span class="text-idle">none</span>{/if}
  </span>
{/snippet}

<div class="flex h-full min-h-0 flex-col">
  {#if !list.length}
    <p class="text-muted-foreground shrink-0 p-2.5" data-empty>No pods yet. A pod groups units of one style under one risk rule.</p>
  {:else}
    <ul class="min-h-0 flex-[0_1_auto] overflow-x-hidden overflow-y-auto">
      {#each list as p (p.id)}
        <li>
          <div class="grid w-full min-w-0 items-center gap-x-4 gap-y-1 rounded-md px-2.5 {size.mode === 'compact' ? 'grid-cols-[minmax(0,1fr)_auto] py-1.5' : 'pod py-2'} text-left">
            <span class="min-w-0">
              <span class="block truncate font-medium" title={p.name}>{p.name}</span>
              {#if size.mode !== "compact"}
                <span class="text-muted-foreground block truncate text-sm" title={size.mode === "expanded" ? p.units.map(name).join(", ") : p.style}>
                  {size.mode === "expanded" ? p.units.map(name).join(", ") : `${p.units.length} ${p.units.length === 1 ? "unit" : "units"} · ${p.style}`}
                </span>
              {/if}
            </span>
            {#if size.mode === "compact"}
              <span class="num shrink-0 text-sm {sign((p.live ?? p.paper)?.today ?? '')}">{(p.live ?? p.paper)?.today ?? "idle"}</span>
              <span class="col-span-2">{@render room(p, true)}</span>
            {:else}
              <span class="flex min-w-0 flex-col gap-0.5">
                {@render side("Live", p.live, "var(--live)")}
                {@render side("Paper", p.paper, "var(--paper)")}
              </span>
              <span class="c-room min-w-0">{@render room(p, true)}</span>
              {#if size.mode === "expanded"}
                <span class="c-rules text-muted-foreground min-w-0 truncate text-sm">{p.rules.map(([k, v]) => `${k} ${v}`).join(" · ")}</span>
              {/if}
            {/if}
          </div>
        </li>
      {/each}
    </ul>
    <Fit items={closed} title="Closed lately, by pod" key={(c) => c.id}>
      {#snippet row(c)}
        <div class="flex min-w-0 items-center gap-3 px-2.5 py-1.5 text-sm">
          <span class="dot {c.mode === 'live' ? 'text-live' : 'text-paper'}" title={c.mode}></span>
          <span class="min-w-0 flex-1 truncate" title="{podOf(c.unit)?.name}: {c.name}"><span class="text-muted-foreground">{podOf(c.unit)?.name} ·</span> {c.name}</span>
          <span class="num shrink-0 {sign(c.result)}">{c.result}</span>
          <span class="num text-muted-foreground w-[4.5rem] shrink-0 text-right">{c.at}</span>
        </div>
      {/snippet}
    </Fit>
  {/if}
</div>

<style>
  .pod {
    grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) minmax(0, 1fr);
  }
  @container (max-width: 30rem) {
    .pod {
      grid-template-columns: minmax(0, 1fr) auto;
    }
    .c-room {
      grid-column: 1 / -1;
    }
  }
  @container (min-width: 60rem) {
    .pod {
      grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.4fr);
    }
  }
  @container (max-width: 60rem) {
    .c-rules {
      display: none;
    }
  }
</style>
