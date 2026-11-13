<script lang="ts" module>
  import { clock, type City } from "$lib/qmx/clock.svelte";
  import type { Event } from "./desk";

  // Instruments by market session. His units on each come from his things.
  export const book: Record<string, string[]> = { tok: ["USDJPY", "JP225"], lon: ["XAUUSD", "XAGUSD", "EURUSD", "UK100"], nyc: ["NAS100", "USOIL", "BTCUSD"] };

  /** An event's time in this machine's own day, in minutes since midnight. */
  export const localAt = (e: Event) => clock.localSpan({ id: e.id, name: "", zone: e.zone, open: e.at, close: e.at })[0];
  export const hhmm = (m: number) => `${String(Math.floor(m / 60) % 24).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
  /** Minutes from now to `m`, forwards round the day. */
  export const ahead = (m: number) => (((m - clock.localMinutes) % 1440) + 1440) % 1440;
  export const inWords = (d: number) => (d >= 60 ? `${Math.floor(d / 60)}h ${d % 60}m` : `${d}m`);

  export function sessionStatus(c: City) {
    const [a, b] = clock.localSpan(c);
    const now = clock.localMinutes;
    const inside = a < b ? now >= a && now < b : now >= a || now < b;
    if (clock.isOpen(c)) return { open: true, text: `Open · closes in ${inWords(ahead(b))}` };
    return { open: false, text: inside ? "Closed for the weekend" : `Closed · opens in ${inWords(ahead(a))}` };
  }
</script>

<script lang="ts">
  import Icon from "$lib/qmx/Icon.svelte";
  import { tone } from "$lib/qmx/state";
  import { shell } from "./state.svelte";
  import { things } from "./things.svelte";
  import { events, pods } from "./desk";

  // One market session in depth: is it open, when in his own time, what of
  // his trades there (instruments, units with live or paper, pods), and what
  // is scheduled. The status-bar clock and the "Markets today" widget both
  // show this, so the two never drift apart.
  let { city, onleave }: { city: City; onleave?: () => void } = $props();

  const st = $derived(sessionStatus(city));
  const span = $derived(clock.localSpan(city));
  const pct = (m: number) => `${(m / 1440) * 100}%`;
  const segs = $derived(span[0] < span[1] ? [[span[0], span[1]]] : [[span[0], 1440], [0, span[1]]]);
  const rows = $derived(
    (book[city.id] ?? []).map((sym) => ({
      sym,
      units: things.all.filter((o) => o.kind === "unit" && o.markets?.some((m) => m.sym === sym && m.life !== "retired" && m.life !== "draft")),
    })),
  );
  const mine = $derived(rows.filter((r) => r.units.length));
  const idle = $derived(rows.filter((r) => !r.units.length));
  const unitIds = $derived(new Set(mine.flatMap((r) => r.units.map((u) => u.id))));
  const here = $derived(pods(things.fixture).filter((p) => p.units.some((u) => unitIds.has(u))));
  const agenda = $derived(events.filter((e) => e.city === city.id).map((e) => ({ e, at: localAt(e) })).sort((x, y) => ahead(x.at) - ahead(y.at)));
  const go = (fn: () => void) => () => (fn(), onleave?.());
</script>

<div class="flex min-w-0 flex-col gap-3">
  <div>
    <div class="flex items-baseline justify-between gap-3">
      <h3 class="display truncate text-lg font-semibold">{city.name}</h3>
      <span class="num text-muted-foreground shrink-0 text-sm">there {clock.time(city.zone)}</span>
    </div>
    <p class="mt-0.5 flex items-center gap-1.5 text-sm {st.open ? 'text-up' : 'text-muted-foreground'}"><span class="dot size-1.5"></span>{st.text}</p>
    <div class="bg-muted relative mt-2.5 h-2 rounded-full">
      {#each segs as [s, e], i (i)}
        <span class="absolute inset-y-0 rounded-full {st.open ? 'bg-up/70' : 'bg-foreground/30'}" style:left={pct(s)} style:width={pct(e - s)}></span>
      {/each}
      <span class="bg-needs absolute -top-1 -bottom-1 w-0.5 rounded-full" style:left={pct(clock.localMinutes)} title="Now"></span>
    </div>
    <p class="mt-1 text-sm"><span class="text-muted-foreground">Your time</span> <span class="num">{hhmm(span[0])} to {hhmm(span[1])}</span></p>
  </div>

  <section class="border-border border-t pt-2">
    <h4 class="text-muted-foreground mb-1 text-sm">Yours that trade here</h4>
    {#if mine.length || idle.length}
      <ul class="flex flex-col">
        {#each mine as r (r.sym)}
          {#each r.units as o (o.id)}
            <li>
              <button class="pick flex w-full min-w-0 items-center gap-2 rounded-md px-1.5 py-1 text-left" onclick={go(() => shell.open({ id: o.id, list: "units" }))}>
                <span class="num w-16 shrink-0">{r.sym}</span>
                <span class="dot size-1.5 {tone[o.tone]}"></span>
                <span class="min-w-0 flex-1 truncate text-sm" title={o.name}>{o.name}</span>
                <span class="ml-auto shrink-0 text-xs font-semibold uppercase {tone[o.tone]}">{o.word}</span>
              </button>
            </li>
          {/each}
        {/each}
        {#each idle as r (r.sym)}
          <li class="flex min-w-0 items-center gap-2 px-1.5 py-1"><span class="num w-16 shrink-0">{r.sym}</span><span class="text-idle text-sm">watching, no unit</span></li>
        {/each}
      </ul>
    {:else}
      <p class="text-sm">Nothing yet. Units you put on paper show up here.</p>
    {/if}
  </section>

  {#if here.length}
    <section class="border-border border-t pt-2">
      <h4 class="text-muted-foreground mb-1 text-sm">Pods trading here</h4>
      <ul class="flex flex-col">
        {#each here as p (p.id)}
          <li>
            <div class="flex w-full min-w-0 items-center gap-2 rounded-md px-1.5 py-1">
              <Icon name="folder-kanban" class="text-muted-foreground size-3.5 shrink-0" />
              <span class="min-w-0 flex-1 truncate text-sm" title={p.name}>{p.name}</span>
              {#if p.live}<span class="text-live num shrink-0 text-xs">live {p.live.today}</span>{/if}
              {#if p.paper}<span class="text-paper num shrink-0 text-xs">paper {p.paper.today}</span>{/if}
            </div>
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  {#if agenda.length}
    <section class="border-border border-t pt-2">
      <h4 class="text-muted-foreground mb-1 text-sm">Scheduled, your time</h4>
      <ul class="flex flex-col">
        {#each agenda as { e, at } (e.id)}
          <li class="flex min-w-0 items-center gap-2 px-1.5 py-1 text-sm">
            <span class="num w-12 shrink-0">{hhmm(at)}</span>
            <span class="dot size-1.5 {e.impact === 'high' ? 'text-down' : 'text-idle'}" title={e.impact === "high" ? "High impact" : "Medium impact"}></span>
            <span class="min-w-0 flex-1 truncate" title={e.title}>{e.title}</span>
            <span class="num text-muted-foreground shrink-0 text-xs">in {inWords(ahead(at))}</span>
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  <div class="border-border flex gap-1 border-t pt-2">
    <button class="press h-8 min-w-0 flex-1 justify-start gap-2 px-2 text-sm" onclick={go(() => shell.go("overview"))}>
      <Icon name="calendar" class="size-3.5 shrink-0" /><span class="truncate">{city.name} news</span>
    </button>
    <button class="press h-8 min-w-0 flex-1 justify-start gap-2 px-2 text-sm" onclick={go(() => shell.go("workflows"))}>
      <Icon name="workflow" class="size-3.5 shrink-0" /><span class="truncate">Macro workflow</span>
    </button>
  </div>
</div>
