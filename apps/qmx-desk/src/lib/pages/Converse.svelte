<script lang="ts" module>
  // The script survives leaving the page and coming back.
  const run = $state({ step: 0, folded: true, typed: [] as string[], beside: "notes" as "notes" | "result" | "none" });
</script>

<script lang="ts">
  import { tick, untrack } from "svelte";
  import Icon from "$lib/qmx/Icon.svelte";
  import IconButton from "$lib/qmx/IconButton.svelte";
  import { tone } from "$lib/qmx/state";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { series, type Obj } from "$lib/shell/model";

  // A session is a thing too: its page is the conversation, with what it
  // opens beside it. Helpers sit on top, each with what it does and where.
  let { o }: { o: Obj } = $props();
  const worst = $derived(things.fixture === "worst");
  const server = $derived(worst ? "trading-node-frankfurt-02.contabo-vps.internal" : "vps-fra");
  const ans = $derived(things.approval);

  // After he answers, the work carries on by itself (scripted).
  $effect(() => {
    if (ans === "open") return;
    const from = untrack(() => run.step);
    const t = [1, 2, 3]
      .filter((s) => s > from)
      .map((s, i) => setTimeout(() => ((run.step = s), s === 3 && (run.beside = "result")), 700 + i * 950));
    return () => t.forEach(clearTimeout);
  });

  const helpers = $derived([
    { name: "Researcher", doing: run.step >= 2 ? "Done: 14 results read" : "Reading 14 backtest results", where: server, state: run.step >= 2 ? "up" : "run" },
    {
      name: "Data analyst",
      doing: ans === "open" ? "Waits for your approval" : ans === "rejected" ? "Skipped the download" : run.step >= 2 ? "Done: EURUSD H1 rebuilt" : "Downloading 2024 EURUSD ticks",
      where: "This PC",
      state: ans === "open" ? "needs" : run.step >= 2 || ans === "rejected" ? "up" : "run",
    },
  ]);
  const tools = $derived(["library.search  units Regime study", "backtest.read  14 results", "readings.get  EURUSD, XAUUSD, NAS100, BTCUSD", "delegate  Researcher on " + server, "delegate  Data analyst on This PC", "data.coverage  EURUSD 2024: missing"]);

  let draft = $state("");
  let feed: HTMLElement | undefined = $state();
  const send = async () => {
    const t = draft.trim();
    if (!t) return;
    run.typed.push(t);
    draft = "";
    await tick();
    feed?.scrollTo({ top: feed.scrollHeight });
  };
  $effect(() => {
    void run.step;
    void ans;
    tick().then(() => feed?.scrollTo({ top: feed.scrollHeight }));
  });

  const W = 600;
  const H = 200;
  const path = (s: number[], lo: number, hi: number) => s.map((v, i) => `${i ? "L" : "M"}${((i / (s.length - 1)) * W).toFixed(1)},${(H - 8 - ((v - lo) / (hi - lo || 1)) * (H - 16)).toFixed(1)}`).join(" ");
  const lo = Math.min(...series.a, ...series.b);
  const hi = Math.max(...series.a, ...series.b);
  const table = [
    ["XAUUSD", "+18.4%", "+11.2%", "v3"],
    ["EURUSD", "+6.1%", "+6.8%", "v1"],
    ["NAS100", "+9.7%", "+4.0%", "v3"],
    ["BTCUSD", "+22.5%", "+15.1%", "v3"],
  ];
</script>

<article class="cv flex h-full min-h-0 flex-col">
  <header class="border-border shrink-0 border-b px-6 pt-4 pb-3">
    <p class="text-muted-foreground flex min-w-0 items-center gap-2 text-sm">
      <span class="dot {run.step >= 3 ? 'text-up' : 'text-run'}"></span>
      <span class="shrink-0">Session</span><span aria-hidden="true">·</span>
      <span class="truncate">Copilot on This PC · Opus 5.5</span>
      <span class="border-border text-muted-foreground ml-auto shrink-0 rounded-full border px-2 text-xs tracking-wide uppercase">Demo, scripted</span>
    </p>
    <h1 class="ttl display mt-1 line-clamp-1 text-3xl font-semibold" title={o.name}>{o.name}</h1>
    <ul class="mt-3 grid gap-2 [grid-template-columns:repeat(auto-fit,minmax(min(100%,20rem),1fr))]" aria-label="Helpers">
      {#each helpers as h (h.name)}
        <li class="well flex min-w-0 items-center gap-3 px-3 py-2" style:border-color={h.state === "needs" ? "color-mix(in oklch, var(--needs) 60%, var(--border))" : undefined}>
          <span class="dot {tone[h.state]}"></span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-medium">{h.name}</span>
            <span class="text-muted-foreground block truncate text-sm">{h.doing}</span>
          </span>
          <span class="text-muted-foreground flex max-w-[45%] min-w-0 items-center gap-1.5 text-sm" title={h.where}>
            <Icon name={h.where === "This PC" ? "laptop" : "server"} class="size-3.5 shrink-0" /><span class="truncate">{h.where}</span>
          </span>
        </li>
      {/each}
    </ul>
  </header>

  <div class="body relative grid min-h-0 flex-1" data-beside={run.beside !== "none"} data-kind={run.beside}>
    <!-- The conversation -->
    <div class="flex min-h-0 min-w-0 flex-col">
      <div bind:this={feed} class="min-h-0 flex-1 overflow-x-hidden overflow-y-auto px-6 py-4">
        <div class="mx-auto flex max-w-[46rem] flex-col gap-4">
          <p class="bg-accent self-end rounded-lg px-3.5 py-2.5">Compare v3 and v1 on the last two years, all four markets. Tell me which one to promote.</p>
          <p>I'll split this. The Researcher reads the 14 backtests on {server}; the Data analyst rebuilds EURUSD H1 bars here.</p>

          <div>
            <button class="press text-muted-foreground h-8 gap-2 px-2 text-sm" aria-expanded={!run.folded} onclick={() => (run.folded = !run.folded)}>
              <Icon name="chevron-right" class="size-3.5 transition-transform duration-150 {run.folded ? '' : 'rotate-90'}" />{tools.length} tool calls
            </button>
            {#if !run.folded}
              <ol class="border-border mt-1 ml-3 flex flex-col border-l pl-3">
                {#each tools as t, i (i)}
                  <li class="num text-muted-foreground flex items-center gap-2 py-0.5 text-sm"><span class="dot text-up size-1.5"></span><span class="truncate" title={t}>{t}</span></li>
                {/each}
              </ol>
            {/if}
          </div>

          <!-- Inline approval: the one thing in this chat that waits for him. -->
          <div class="rounded-lg border p-3.5" style:border-color="color-mix(in oklch, var(--needs) {ans === 'open' ? 70 : 25}%, var(--border))" style:background="color-mix(in oklch, var(--needs) {ans === 'open' ? 9 : 3}%, transparent)">
            <p class="text-needs flex items-center gap-2 text-sm font-medium"><Icon name="shield" class="size-4" />Data analyst asks</p>
            <p class="mt-1 text-lg">Download EURUSD ticks for 2024</p>
            <p class="text-muted-foreground flex flex-wrap items-center gap-x-2 text-sm"><span class="num">2.1 GB</span><span aria-hidden="true">·</span><span class="flex items-center gap-1"><Icon name="laptop" class="size-3.5" />to This PC</span><span aria-hidden="true">·</span><span>Dukascopy</span></p>
            {#if ans === "open"}
              <div class="mt-3 flex flex-wrap gap-2">
                <button class="bg-foreground text-background h-10 rounded-md px-4 font-semibold transition-transform duration-100 active:scale-[0.97]" onclick={() => things.answer("allowed")}>Allow once</button>
                <button class="press border-border h-10 border px-4" onclick={() => (things.answer("allowed"), things.say("Downloads from Dukascopy are always allowed now"))}>Always allow downloads</button>
                <button class="press h-10 px-4" onclick={() => things.answer("rejected")}>Reject</button>
              </div>
            {:else}
              <p class="mt-2 flex items-center gap-2 text-sm"><span class="dot {ans === 'allowed' ? 'text-up' : 'text-idle'}"></span>{ans === "allowed" ? "You allowed it" : "You rejected it"}</p>
            {/if}
          </div>

          {#if run.step >= 1}
            <p class="num text-muted-foreground flex items-center gap-2 text-sm"><span class="dot text-up size-1.5"></span>{ans === "allowed" ? "data.download  EURUSD 2024 ticks · 2.1 GB · done" : "Skipped: using EURUSD up to Dec 2023"}</p>
          {/if}
          {#if run.step >= 2}
            <p class="num text-muted-foreground flex items-center gap-2 text-sm"><span class="dot text-up size-1.5"></span>Both helpers finished</p>
          {/if}
          {#if run.step >= 3}
            <p>v3 beats v1 on 3 of 4 markets, and it holds after doubled costs. EURUSD is the exception: v1 is slightly better there. I'd promote v3 on XAUUSD first.</p>
            <button class="well hover:bg-accent/60 flex items-center gap-3 px-3 py-2.5 text-left transition-colors duration-150" onclick={() => (run.beside = "result")}>
              <Icon name="git-compare" class="text-muted-foreground shrink-0" />
              <span class="min-w-0 flex-1"><span class="block truncate font-medium">v3 against v1, two years</span><span class="text-muted-foreground block text-sm">Result · opened beside</span></span>
              <Icon name="arrow-right" class="text-muted-foreground shrink-0" />
            </button>
          {/if}
          {#each run.typed as t, i (i)}
            <p class="bg-accent self-end rounded-lg px-3.5 py-2.5 [overflow-wrap:anywhere]">{t}</p>
            <p class="text-muted-foreground">Demo: replies here are scripted.</p>
          {/each}
        </div>
      </div>
      <form class="shrink-0 px-6 pb-4" onsubmit={(e) => (e.preventDefault(), send())}>
        <label class="well bg-panel mx-auto flex max-w-[46rem] items-center gap-2 px-3">
          <input bind:value={draft} class="placeholder:text-muted-foreground h-12 min-w-0 flex-1 bg-transparent outline-none" placeholder="Steer the copilot" aria-label="Message the copilot" />
          <button class="press size-9" aria-label="Send" title="Send" type="submit"><Icon name="arrow-up" /></button>
        </label>
      </form>
    </div>

    <!-- Beside the chat: what it opens. -->
    {#if run.beside !== "none"}
      <aside class="side border-border bg-panel flex min-h-0 min-w-0 flex-col border-l" aria-label="Opened beside">
        <header class="flex h-12 shrink-0 items-center gap-2 pr-1.5 pl-4">
          <Icon name={run.beside === "result" ? "git-compare" : "scan-eye"} class="text-muted-foreground" />
          <h2 class="min-w-0 flex-1 truncate font-medium">{run.beside === "result" ? "v3 against v1, two years" : "What the helpers read"}</h2>
          <IconButton icon="x" label="Close the side" onclick={() => (run.beside = "none")} />
        </header>
        {#if run.beside === "result"}
          <div class="min-h-0 flex-1 overflow-y-auto px-4 pb-4">
            <div class="flex items-center gap-4 text-sm">
              <span class="flex items-center gap-1.5"><span class="bg-foreground h-0.5 w-4 rounded"></span>v3</span>
              <span class="text-muted-foreground flex items-center gap-1.5"><span class="bg-foreground/35 h-0.5 w-4 rounded"></span>v1</span>
              <span class="text-muted-foreground ml-auto">same markets, same costs</span>
            </div>
            <svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" class="mt-2 h-44 w-full" aria-label="Equity of v3 and v1">
              <path d={path(series.b, lo, hi)} fill="none" stroke="currentColor" stroke-opacity="0.35" stroke-width="2" vector-effect="non-scaling-stroke" />
              <path d={path(series.a, lo, hi)} fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke" />
            </svg>
            <table class="mt-3 w-full border-separate border-spacing-0">
              <thead><tr>{#each ["Market", "v3", "v1", "Better"] as c, i (c)}<th class="text-muted-foreground border-border border-b px-2 py-1.5 text-sm font-medium {i ? 'text-right' : 'text-left'}">{c}</th>{/each}</tr></thead>
              <tbody>
                {#each table as r (r[0])}
                  <tr>{#each r as c, i (i)}<td class="border-border/60 num border-b px-2 py-1.5 {i ? 'text-right' : 'text-left'} {i === 3 && c === 'v3' ? 'text-up' : ''}">{c}</td>{/each}</tr>
                {/each}
              </tbody>
            </table>
            <div class="mt-4 flex flex-wrap gap-2">
              <button class="press border-border h-10 gap-2 border px-3" onclick={() => things.say("Saved to the Library as a result")}><Icon name="library" class="size-4" />Save to Library</button>
              <button class="press h-10 gap-2 px-3" onclick={() => shell.open({ id: "u-gold" })}>Open Gold breakout<Icon name="arrow-right" /></button>
            </div>
          </div>
        {:else}
          <ul class="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
            {#each ["Gold breakout v4 · XAUUSD H1", "Gold breakout v3 · XAUUSD H1", "London fade v3 · EURUSD", "London fade v1 · EURUSD", "Index open drive v1 · NAS100", "BTC trend v2 · BTCUSD", "BTC trend v1 · BTCUSD"] as r, i (r)}
              <li class="flex min-w-0 items-center gap-3 px-2 py-1.5">
                <span class="dot size-1.5 {i < 4 || run.step >= 2 ? 'text-up' : 'text-run'}"></span>
                <span class="min-w-0 flex-1 truncate">{r}</span>
                <span class="text-muted-foreground text-sm">{i < 4 || run.step >= 2 ? "read" : "reading"}</span>
              </li>
            {/each}
            <li class="text-muted-foreground px-2 py-1.5 text-sm">and 7 more</li>
          </ul>
        {/if}
      </aside>
    {/if}
  </div>
</article>

<style>
  .cv {
    container-type: inline-size;
  }
  .body {
    grid-template-columns: minmax(0, 1fr);
  }
  .body[data-beside="true"] {
    grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
  }
  /* Narrow: the chat keeps the room; a result slides over it from the
     right, where it opened, and closes back the same way. */
  @container (max-width: 52rem) {
    .body[data-beside="true"] {
      grid-template-columns: minmax(0, 1fr);
    }
    .side {
      position: absolute;
      inset: 0 0 0 auto;
      width: min(30rem, 92%);
      box-shadow: -24px 0 48px -12px black;
      transition: transform 220ms cubic-bezier(0.32, 0.72, 0, 1);
      @starting-style {
        transform: translateX(100%);
      }
    }
    .body[data-kind="notes"] .side {
      display: none;
    }
  }
  @media (max-height: 820px) {
    .ttl {
      font-size: 1.6rem;
    }
  }
</style>
