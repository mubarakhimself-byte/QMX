<script lang="ts">
  import Icon from "$lib/qmx/Icon.svelte";
  import { cards } from "$lib/shell/data";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { guestSections, guestActions, guestInk, guestWash, kindName } from "$lib/shell/model";

  // A mini app is a guest. Its own screen is sandboxed HTML it supplies (the
  // host passes colours and fonts in). What it adds to his things is listed
  // here, so he sees where the guest shows up.
  let { id }: { id: string } = $props();
  const g = $derived(things.guest(id)!);
  const adds = $derived([
    ...guestSections.filter((s) => s.guest === id).map((s) => ({ what: `Section "${s.title}"`, where: `on every ${kindName[s.kind].toLowerCase()} page` })),
    ...guestActions.filter((a) => a.guest === id).map((a) => ({ what: `Action "${a.label}"`, where: `on every ${kindName[a.kind].toLowerCase()}` })),
    ...Object.values(cards).filter((c) => c.guest === id).map((c) => ({ what: `Card "${c.title}"`, where: "for Overview and Trading" })),
  ]);
  const screen = $derived(`<!doctype html><html><head><meta charset="utf-8"><style>
    :root{--bg:#0b0b0c;--fg:#f2f2f2;--muted:#9a9aa2;--accent:${guestInk(g.hue)}}
    body{margin:0;padding:20px;background:var(--bg);color:var(--fg);font:17px/1.45 system-ui,sans-serif}
    h2{margin:0 0 4px;font-size:22px} p{margin:0 0 16px;color:var(--muted)}
    table{width:100%;border-collapse:collapse} td,th{padding:9px 6px;border-bottom:1px solid #222;text-align:left}
    th{color:var(--muted);font-weight:500;font-size:14px} td.n{font-family:ui-monospace,monospace;text-align:right}
    .tag{color:var(--accent);font-weight:600}
  </style></head><body>
    <h2>${g.name}</h2><p>This screen is the app's own HTML, in a sandbox. Demo content.</p>
    <table><tr><th>Market</th><th>Reading</th><th style="text-align:right">Variance ratio</th><th style="text-align:right">Fresh</th></tr>
    <tr><td>XAUUSD</td><td class="tag">Trending</td><td class="n">1.18</td><td class="n">2m</td></tr>
    <tr><td>EURUSD</td><td>Choppy</td><td class="n">0.94</td><td class="n">2m</td></tr>
    <tr><td>NAS100</td><td class="tag">Trending</td><td class="n">1.09</td><td class="n">3m</td></tr>
    <tr><td>BTCUSD</td><td>Mixed</td><td class="n">1.01</td><td class="n">5m</td></tr></table>
  </body></html>`);
</script>

<article class="flex h-full min-h-0 flex-col px-6 pt-5 pb-4">
  <p class="flex items-center gap-2 text-sm" style:color={guestInk(g.hue)}><Icon name="puzzle" class="size-4" />Mini app · a guest</p>
  <h1 class="display mt-1 line-clamp-2 text-4xl font-semibold [overflow-wrap:anywhere]" title={g.name}>{g.name}</h1>

  <div class="app-grid mt-4 grid min-h-0 flex-1 gap-[var(--gap)]">
    <section class="surface flex min-h-0 flex-col overflow-hidden border-dashed" style:border-color={guestInk(g.hue)} aria-label="Its screen">
      <header class="flex h-11 shrink-0 items-center gap-2 px-3"><Icon name={g.icon} class="size-4" /><h3 class="font-medium">Its screen</h3><span class="text-muted-foreground ml-auto text-sm">sandboxed</span></header>
      <iframe title="{g.name} screen" sandbox="" srcdoc={screen} class="min-h-0 w-full flex-1 border-0"></iframe>
    </section>
    <section class="surface flex min-h-0 flex-col overflow-hidden" aria-label="What it adds">
      <header class="flex h-11 shrink-0 items-center gap-2 px-3"><Icon name="plus" class="text-muted-foreground size-4" /><h3 class="font-medium">What it adds to your things</h3></header>
      <ul class="min-h-0 flex-1 overflow-y-auto px-3 pb-3">
        {#each adds as a (a.what)}
          <li class="border-border/60 flex flex-col border-t py-2.5 first:border-t-0">
            <span class="font-medium" style:color={guestInk(g.hue)}>{a.what}</span>
            <span class="text-muted-foreground text-sm">{a.where}</span>
          </li>
        {:else}
          <li class="text-muted-foreground py-2.5">Only its own screen and its tools in chat.</li>
        {/each}
      </ul>
      <p class="text-muted-foreground border-border shrink-0 border-t px-3 py-2.5 text-sm" style:background={guestWash(g.hue)}>Add or remove these from a page with Edit page, or from a board with Arrange.</p>
    </section>
  </div>
</article>

<style>
  .app-grid {
    grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  }
</style>
