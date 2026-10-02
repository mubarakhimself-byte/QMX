<script lang="ts">
  /**
   * Build a scenario: one bot version across markets, timeframes, market
   * pairs and parameter ranges (QMB B-12 permutation sweep: every combination
   * is its own isolated run). Shows the run count, rough time on the chosen
   * machine, and a warning when the grid is big enough that a winner is
   * likely luck (attempt budget not ruled yet, GAP-0017). Pairs and saved
   * scenarios are new scope.
   */
  import X from "@lucide/svelte/icons/x";
  import Plus from "@lucide/svelte/icons/plus";
  import TriangleAlert from "@lucide/svelte/icons/triangle-alert";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import EnvChip from "./EnvChip.svelte";
  import { ENVIRONMENTS } from "./demo";

  let { open = $bindable(false) }: { open?: boolean } = $props();

  const MARKET_GROUPS = [
    {
      label: "FX majors",
      items: [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "USDCAD",
        "NZDUSD",
        "USDCHF",
      ],
    },
    { label: "FX crosses", items: ["EURJPY", "GBPJPY", "EURGBP", "AUDJPY"] },
    { label: "Metals", items: ["XAUUSD", "XAGUSD"] },
    { label: "Indices", items: ["US500", "NAS100", "DE40", "UK100"] },
    { label: "Crypto", items: ["BTCUSD", "ETHUSD", "SOLUSD"] },
  ];
  const TFS = ["M5", "M15", "M30", "H1", "H4", "D1"];

  let markets = $state<string[]>([
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "XAUUSD",
    "US500",
  ]);
  let tfs = $state<string[]>(["M15", "H1", "H4"]);
  let pairs = $state<[string, string][]>([]);
  let pairA = $state("EURUSD");
  let pairB = $state("GBPUSD");
  let own = $state<string[]>([]);
  let newMarket = $state("");
  function addMarket() {
    const m = newMarket.trim().toUpperCase();
    if (!m) return;
    if (!own.includes(m) && !MARKET_GROUPS.some((g) => g.items.includes(m)))
      own = [...own, m];
    if (!markets.includes(m)) markets = [...markets, m];
    newMarket = "";
  }
  const MEASURES = [
    "Net %",
    "Sharpe",
    "Max drawdown",
    "Profit factor",
    "Win rate",
    "Average trade",
    "Exposure",
    "Longest losing streak",
  ];
  let measures = $state(["Net %", "Sharpe", "Max drawdown", "Profit factor"]);
  type Param = {
    id: string;
    name: string;
    from: number;
    to: number;
    step: number;
    on: boolean;
    custom?: boolean;
  };
  let params = $state<Param[]>([
    { id: "p1", name: "ATR stop (×)", from: 1, to: 2.5, step: 0.5, on: true },
    {
      id: "p2",
      name: "Lookback (bars)",
      from: 20,
      to: 60,
      step: 20,
      on: false,
    },
    {
      id: "p3",
      name: "Score threshold",
      from: 0.55,
      to: 0.7,
      step: 0.05,
      on: false,
    },
  ]);
  let costs = $state("Default spread");
  let env = $state("vps-fsn");

  const toggle = (list: string[], v: string) =>
    list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
  const steps = (p: { from: number; to: number; step: number }) =>
    Math.max(1, Math.floor((p.to - p.from) / p.step + 1e-9) + 1);
  const combos = $derived(
    params.filter((p) => p.on).reduce((n, p) => n * steps(p), 1),
  );
  const instruments = $derived(markets.length + pairs.length);
  const runs = $derived(instruments * tfs.length * combos);
  const machine = $derived(ENVIRONMENTS.find((e) => e.id === env)!);
  const minutes = $derived(
    Math.ceil((runs * 2.5) / Math.max(1, machine.slots[1] - machine.slots[0])),
  );
  const time = $derived(
    minutes < 90 ? `${minutes} min` : `${(minutes / 60).toFixed(1)} h`,
  );

  function addPair() {
    if (pairA === pairB || pairs.some(([a, b]) => a === pairA && b === pairB))
      return;
    pairs = [...pairs, [pairA, pairB]];
  }
  function run(e: SubmitEvent) {
    e.preventDefault();
    open = false;
    workbench.notify(
      `Scenario of ${runs} runs drafted. Running it needs the daemon.`,
    );
  }
  const chip = (on: boolean) =>
    cn(
      "h-7 rounded-md border px-2 text-xs",
      on
        ? "border-primary bg-primary/15 text-foreground"
        : "text-muted-foreground hover:text-foreground",
    );
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
    <form class="flex flex-col gap-5" onsubmit={run}>
      <Dialog.Header>
        <Dialog.Title>New scenario · EURUSD H1 GBM v7</Dialog.Title>
        <Dialog.Description>
          Every combination below becomes its own run. Results land in the sweep
          grid and the runs table.
        </Dialog.Description>
      </Dialog.Header>

      <section class="grid gap-2">
        <h3 class="text-sm font-medium">
          Markets <span class="text-muted-foreground font-normal"
            >{markets.length}</span
          >
        </h3>
        {#each MARKET_GROUPS as g (g.label)}
          <div class="flex flex-wrap items-center gap-1.5">
            <span class="text-muted-foreground w-20 text-xs">{g.label}</span>
            {#each g.items as m (m)}
              <button
                type="button"
                class={chip(markets.includes(m))}
                aria-pressed={markets.includes(m)}
                onclick={() => (markets = toggle(markets, m))}>{m}</button
              >
            {/each}
          </div>
        {/each}
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-muted-foreground w-20 text-xs">Yours</span>
          {#each own as m (m)}
            <button
              type="button"
              class={chip(markets.includes(m))}
              aria-pressed={markets.includes(m)}
              onclick={() => (markets = toggle(markets, m))}>{m}</button
            >
          {/each}
          <input
            bind:value={newMarket}
            placeholder="Any symbol, e.g. WTI"
            aria-label="Add a market"
            class="bg-background/40 h-7 w-40 rounded-md border px-2 text-xs uppercase"
            onkeydown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addMarket();
              }
            }}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            class="h-7"
            onclick={addMarket}><Plus />Add</Button
          >
        </div>
      </section>

      <section class="grid gap-2">
        <h3 class="text-sm font-medium">
          Pairs <span class="text-muted-foreground font-normal"
            >trade one market against another · new scope</span
          >
        </h3>
        <div class="flex flex-wrap items-center gap-2">
          {#each pairs as [a, b], i (`${a}-${b}`)}
            <span
              class="bg-muted flex h-7 items-center gap-1.5 rounded-md pr-1 pl-2 text-xs"
            >
              {a} vs {b}
              <button
                type="button"
                class="hover:bg-background/50 rounded p-0.5"
                aria-label={`Remove ${a} vs ${b}`}
                onclick={() => (pairs = pairs.filter((_, k) => k !== i))}
                ><X class="size-3" /></button
              >
            </span>
          {/each}
          <select
            bind:value={pairA}
            class="bg-background/40 h-7 rounded-md border px-1.5 text-xs"
            aria-label="First market"
          >
            {#each MARKET_GROUPS.flatMap((g) => g.items) as m (m)}<option
                >{m}</option
              >{/each}
          </select>
          <span class="text-muted-foreground text-xs">vs</span>
          <select
            bind:value={pairB}
            class="bg-background/40 h-7 rounded-md border px-1.5 text-xs"
            aria-label="Second market"
          >
            {#each MARKET_GROUPS.flatMap((g) => g.items) as m (m)}<option
                >{m}</option
              >{/each}
          </select>
          <Button
            type="button"
            variant="outline"
            size="sm"
            class="h-7"
            onclick={addPair}><Plus />Add pair</Button
          >
        </div>
      </section>

      <section class="grid gap-2">
        <h3 class="text-sm font-medium">Timeframes</h3>
        <div class="flex flex-wrap gap-1.5">
          {#each TFS as t (t)}
            <button
              type="button"
              class={chip(tfs.includes(t))}
              aria-pressed={tfs.includes(t)}
              onclick={() => (tfs = toggle(tfs, t))}>{t}</button
            >
          {/each}
        </div>
      </section>

      <section class="grid gap-2">
        <h3 class="text-sm font-medium">
          Parameters <span class="text-muted-foreground font-normal"
            >from the bot's declared ranges</span
          >
        </h3>
        <div class="grid gap-1.5">
          <div
            class="text-muted-foreground grid grid-cols-[2.5rem_1fr_repeat(3,5rem)_4rem] gap-2 text-xs"
            aria-hidden="true"
          >
            <span></span><span>Sweep</span><span>From</span><span>To</span><span
              >Step</span
            ><span></span>
          </div>
          {#each params as p (p.id)}
            <div
              class="grid grid-cols-[2.5rem_1fr_repeat(3,5rem)_4rem] items-center gap-2 text-sm"
            >
              <Switch bind:checked={p.on} aria-label={`Sweep ${p.name}`} />
              {#if p.custom}
                <input
                  bind:value={p.name}
                  aria-label="Parameter name"
                  class="bg-background/40 h-7 rounded-md border px-2 text-sm"
                />
              {:else}
                <span class={p.on ? "" : "text-muted-foreground"}>{p.name}</span
                >
              {/if}
              <input
                type="number"
                bind:value={p.from}
                step="any"
                disabled={!p.on}
                class="bg-background/40 h-7 rounded-md border px-2 text-xs disabled:opacity-50"
                aria-label={`${p.name} from`}
              />
              <input
                type="number"
                bind:value={p.to}
                step="any"
                disabled={!p.on}
                class="bg-background/40 h-7 rounded-md border px-2 text-xs disabled:opacity-50"
                aria-label={`${p.name} to`}
              />
              <input
                type="number"
                bind:value={p.step}
                step="any"
                min="0.0001"
                disabled={!p.on}
                class="bg-background/40 h-7 rounded-md border px-2 text-xs disabled:opacity-50"
                aria-label={`${p.name} step`}
              />
              <span class="num text-muted-foreground text-right text-xs"
                >{p.on ? `${steps(p)} values` : "fixed"}</span
              >
            </div>
          {/each}
          <div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              class="h-7"
              onclick={() =>
                (params = [
                  ...params,
                  {
                    id: `p${params.length + 1}`,
                    name: "New parameter",
                    from: 1,
                    to: 3,
                    step: 1,
                    on: true,
                    custom: true,
                  },
                ])}><Plus />Add a parameter</Button
            >
            <span class="text-muted-foreground text-xs"
              >New ones are added to the bot's declared ranges as a new version.</span
            >
          </div>
        </div>
      </section>

      <section class="grid gap-2">
        <h3 class="text-sm font-medium">
          Measures <span class="text-muted-foreground font-normal"
            >recorded for every run; raw numbers, never a combined score</span
          >
        </h3>
        <div class="flex flex-wrap items-center gap-1.5">
          {#each MEASURES as m (m)}
            <button
              type="button"
              class={chip(measures.includes(m))}
              aria-pressed={measures.includes(m)}
              onclick={() => (measures = toggle(measures, m))}>{m}</button
            >
          {/each}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            class="h-7"
            onclick={() =>
              workbench.notify(
                "Describe the measure to the Lab copilot; it writes it as a reusable measure.",
              )}><Plus />Your own</Button
          >
        </div>
      </section>

      <section class="grid gap-3 sm:grid-cols-2">
        <label class="grid gap-1 text-sm">
          <span class="font-medium">Costs</span>
          <select
            bind:value={costs}
            class="bg-background/40 h-8 rounded-md border px-2 text-sm"
          >
            <option>Default spread</option><option>Stress spread ×2</option
            ><option>Your broker's fills</option>
          </select>
        </label>
        <label class="grid gap-1 text-sm">
          <span class="font-medium">Run on</span>
          <select
            bind:value={env}
            class="bg-background/40 h-8 rounded-md border px-2 text-sm"
          >
            {#each ENVIRONMENTS as e (e.id)}<option
                value={e.id}
                disabled={e.status === "offline"}
                >{e.name} · {e.where}{e.status === "offline"
                  ? " (offline)"
                  : ""}</option
              >{/each}
          </select>
        </label>
      </section>

      <div
        class="well flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg px-4 py-3"
      >
        <span
          ><span class="num text-2xl font-semibold">{runs}</span>
          <span class="text-muted-foreground text-sm">runs</span></span
        >
        <span class="text-muted-foreground text-sm"
          >{instruments} markets × {tfs.length} timeframes × {combos} settings</span
        >
        <span class="text-sm"
          >about <span class="num">{time}</span> on <EnvChip {env} /></span
        >
        {#if !machine.evidence}<span class="text-muted-foreground text-xs"
            >Exploration only: rerun winners on this laptop for evidence.</span
          >{/if}
      </div>
      {#if runs > 200}
        <p class="text-warning flex items-start gap-2 text-sm">
          <TriangleAlert class="mt-0.5 size-4 shrink-0" />
          {runs} tries make it likely the best result is luck. Narrow the grid, or
          plan a walk-forward and an untouched year for the winners.
        </p>
      {/if}

      <Dialog.Footer class="gap-2">
        <Button
          type="button"
          variant="ghost"
          onclick={() => workbench.notify("Scenario saved to your presets.")}
          >Save as preset</Button
        >
        <Button type="submit" disabled={runs === 0}>Run {runs} runs</Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
