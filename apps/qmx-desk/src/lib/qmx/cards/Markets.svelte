<script lang="ts">
  import Sessions from "../Sessions.svelte";
  import Icon from "../Icon.svelte";
  import Fit from "../Fit.svelte";
  import { cities } from "../clock.svelte";
  import { panelSize } from "../tiles/panel-size";
  import SessionDetail, { localAt, hhmm, ahead, inWords } from "$lib/shell/SessionDetail.svelte";
  import { events, tomorrow, headlines, type Event, type Headline } from "$lib/shell/desk";
  import { things } from "$lib/shell/things.svelte";

  // The trading day: the three sessions, then what is scheduled today
  // (CPI and the like), then headlines. Click a session for what trades in
  // it: his instruments, his units with live or paper, his pods. That view
  // is the same one the status-bar clock opens.
  // Compact: the bars and the next event. Regular: bars, then the agenda
  // and headlines one under the other. Expanded: agenda and headlines side by side.
  const size = panelSize();
  let pick = $state<string | null>(null);
  const city = $derived(cities.find((c) => c.id === pick));

  const agenda = $derived(events.map((e) => ({ e, at: localAt(e), d: ahead(localAt(e)) })).sort((a, b) => a.d - b.d));
  const next = $derived(agenda[0]);
  // Expanded: today's agenda, then tomorrow's.
  const days = $derived<Item[]>([
    ...agenda.map((x) => ({ id: x.e.id, ev: x })),
    { id: "h-t", head: "Tomorrow" },
    ...tomorrow.map((e) => ({ id: e.id, ev: { e, at: localAt(e), d: -1 } })),
  ]);
  const news = $derived(headlines(things.fixture));
  const short: Record<string, string> = { tok: "TYO", lon: "LON", nyc: "NYC" };
  type Item = { id: string; head?: string; ev?: { e: Event; at: number; d: number }; h?: Headline };
  const both = $derived<Item[]>([
    { id: "h-a", head: "Scheduled today, your time" },
    ...agenda.map((x) => ({ id: x.e.id, ev: x })),
    { id: "h-n", head: "Headlines" },
    ...news.map((h) => ({ id: h.id, h })),
  ]);
</script>

{#snippet evRow(x: { e: Event; at: number; d: number })}
  <div class="flex min-w-0 items-center gap-2.5 px-2.5 py-1.5 text-sm" title="{x.e.title} · {x.e.syms.join(', ')}">
    <span class="num w-11 shrink-0">{hhmm(x.at)}</span>
    <span class="dot size-1.5 {x.e.impact === 'high' ? 'text-down' : 'text-idle'}" title={x.e.impact === "high" ? "High impact" : "Medium impact"}></span>
    <span class="min-w-0 flex-1 truncate">{x.e.title}</span>
    <span class="num text-muted-foreground shrink-0 text-xs">{short[x.e.city]}{x.d >= 0 ? ` · in ${inWords(x.d)}` : ""}</span>
  </div>
{/snippet}

{#snippet hRow(h: Headline)}
  <div class="flex min-w-0 items-start gap-2.5 px-2.5 py-1.5 text-sm">
    <span class="min-w-0 flex-1">
      <span class="line-clamp-2" title={h.text}>{h.text}</span>
      <span class="text-muted-foreground block truncate text-xs" title="{h.source} · {h.syms.join(', ')}">{h.source} · {h.syms.join(", ")}</span>
    </span>
    <span class="num text-muted-foreground shrink-0 text-xs">{h.ago}</span>
  </div>
{/snippet}

<div class="flex h-full min-h-0 flex-col">
  {#if city}
    <div class="flex min-h-0 flex-1 flex-col">
      <button class="press text-muted-foreground mx-1.5 h-8 shrink-0 self-start gap-1.5 px-2 text-sm" onclick={() => (pick = null)}><Icon name="arrow-left" class="size-3.5" />All sessions</button>
      <div class="min-h-0 flex-1 overflow-x-hidden overflow-y-auto px-2.5 pb-1"><SessionDetail {city} /></div>
    </div>
  {:else}
    <div class="shrink-0 px-2.5 pt-1 pb-1.5"><Sessions onpick={(id) => (pick = id)} /></div>
    {#if size.mode === "compact" && next}
      <div class="shrink-0 border-t border-border/70 mx-2.5"></div>
      <div class="shrink-0">{@render evRow(next)}</div>
    {/if}
    {#if size.mode === "expanded"}
      <div class="grid min-h-0 flex-1 grid-cols-2 gap-4">
        <Fit items={days} title="Scheduled today, your time" key={(x) => x.id}>
          {#snippet row(x)}
            {#if x.head}<h4 class="text-muted-foreground border-border/70 mx-2.5 mt-1.5 border-t pt-2 pb-0.5 text-sm font-medium">{x.head}</h4>{:else if x.ev}{@render evRow(x.ev)}{/if}
          {/snippet}
        </Fit>
        <Fit items={news} title="Headlines" key={(h) => h.id}>{#snippet row(h)}{@render hRow(h)}{/snippet}</Fit>
      </div>
    {:else}
      <Fit items={size.mode === "compact" ? [{ id: "h-l", head: "Later today" }, ...both.slice(2)] : both} key={(x) => x.id}>
        {#snippet row(x)}
          {#if x.head}
            <h4 class="text-muted-foreground border-border/70 mx-2.5 mt-1.5 border-t pt-2 pb-0.5 text-sm font-medium">{x.head}</h4>
          {:else if x.ev}{@render evRow(x.ev)}{:else if x.h}{@render hRow(x.h)}{/if}
        {/snippet}
      </Fit>
    {/if}
  {/if}
</div>
