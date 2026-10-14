<script lang="ts">
  /**
   * Open positions and working orders across every account, ticking live.
   * Sort by any column, group by pod or bot, filter by market. CFD values are the full
   * position size (notional), not the margin behind it. The pod's own
   * record is shown beside what the exchange reports; they are never merged.
   */
  import { onMount } from "svelte";
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import Search from "@lucide/svelte/icons/search";
  import { cn } from "$lib/utils";
  import { ACCOUNTS } from "../demo";
  import { usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  type Pos = {
    sym: string;
    qty: number;
    unit: string;
    entry: number;
    last: number;
    risk: number;
    bot: string;
    pod: string;
    account: string;
    mode: "LIVE" | "PAPER";
    p: number;
  };
  let rows = $state<Pos[]>([
    {
      sym: "XAUUSD",
      qty: 50,
      unit: "oz",
      entry: 2378.2,
      last: 2384.1,
      risk: 0.3,
      bot: "Gold scalper",
      pod: "Gold & indices",
      account: "icm-live",
      mode: "LIVE",
      p: 2,
    },
    {
      sym: "NAS100",
      qty: 1,
      unit: "contract",
      entry: 19650,
      last: 19742.6,
      risk: 0.3,
      bot: "NAS100 breakout",
      pod: "Gold & indices",
      account: "icm-live",
      mode: "LIVE",
      p: 1,
    },
    {
      sym: "EURUSD",
      qty: 30000,
      unit: "EUR",
      entry: 1.0861,
      last: 1.0883,
      risk: 0.25,
      bot: "EURUSD mean reversion",
      pod: "FX majors",
      account: "icm-demo",
      mode: "PAPER",
      p: 5,
    },
    {
      sym: "BTCUSDT",
      qty: 0.18,
      unit: "BTC",
      entry: 63120,
      last: 64210,
      risk: 1.0,
      bot: "BTC breakout",
      pod: "BTC & ETH core",
      account: "bn-spot",
      mode: "LIVE",
      p: 0,
    },
    {
      sym: "ETHUSDT",
      qty: 2.4,
      unit: "ETH",
      entry: 3080,
      last: 3118,
      risk: 0.7,
      bot: "ETH trend",
      pod: "BTC & ETH core",
      account: "bn-spot",
      mode: "LIVE",
      p: 1,
    },
    {
      sym: "SOLUSDT",
      qty: 24,
      unit: "SOL",
      entry: 146.1,
      last: 152.4,
      risk: 0.9,
      bot: "SOL momentum",
      pod: "Alt momentum",
      account: "by-spot",
      mode: "LIVE",
      p: 2,
    },
    {
      sym: "AVAXUSDT",
      qty: 110,
      unit: "AVAX",
      entry: 28.3,
      last: 27.6,
      risk: 0.5,
      bot: "AVAX momentum",
      pod: "Alt momentum",
      account: "by-spot",
      mode: "LIVE",
      p: 2,
    },
    {
      sym: "Basket ×5",
      qty: 1,
      unit: "basket",
      entry: 6000,
      last: 6150,
      risk: 0,
      bot: "Top-5 rotator",
      pod: "Weekly rotation",
      account: "cb-spot",
      mode: "LIVE",
      p: 0,
    },
    {
      sym: "ETHUSDT",
      qty: 0.8,
      unit: "ETH",
      entry: 3052,
      last: 3118,
      risk: 0.4,
      bot: "ETH mean reversion",
      pod: "Mean reversion",
      account: "bn-test",
      mode: "PAPER",
      p: 1,
    },
  ]);
  onMount(() => {
    const t = setInterval(() => {
      rows = rows.map((r) => ({
        ...r,
        last: +(r.last * (1 + (Math.random() - 0.5) * 0.0008)).toFixed(r.p),
      }));
    }, 1200);
    return () => clearInterval(t);
  });

  type Key = "sym" | "value" | "pnl" | "risk" | "bot";
  let key = $state<Key>("pnl");
  let desc = $state(true);
  let group = $state<"none" | "pod" | "bot">("pod");
  let q = $state("");
  const value = (r: Pos) => r.qty * r.last;
  const pnl = (r: Pos) => ((r.last - r.entry) / r.entry) * 100;
  const get = (r: Pos, k: Key) =>
    k === "sym"
      ? r.sym
      : k === "bot"
        ? r.bot
        : k === "value"
          ? value(r)
          : k === "pnl"
            ? pnl(r)
            : r.risk;
  const shown = $derived(
    rows
      .filter(
        (r) =>
          portfolio.world === "all" ||
          (portfolio.world === "live") === (r.mode === "LIVE"),
      )
      .filter(
        (r) =>
          !q ||
          r.sym.toLowerCase().includes(q.toLowerCase()) ||
          r.bot.toLowerCase().includes(q.toLowerCase()),
      )
      .sort((a, b) => {
        const x = get(a, key);
        const y = get(b, key);
        const c =
          typeof x === "number" && typeof y === "number"
            ? x - y
            : String(x).localeCompare(String(y));
        return desc ? -c : c;
      }),
  );
  const groups = $derived(
    group === "none"
      ? [{ name: "", items: shown }]
      : [...new Set(shown.map((r) => (group === "pod" ? r.pod : r.bot)))].map(
          (g) => ({
            name: g,
            items: shown.filter((r) => (group === "pod" ? r.pod : r.bot) === g),
          }),
        ),
  );
  function sortBy(k: Key) {
    if (key === k) desc = !desc;
    else {
      key = k;
      desc = true;
    }
  }
  const COLS: { k: Key; label: string; right?: boolean }[] = [
    { k: "sym", label: "Market" },
    { k: "value", label: "Value", right: true },
    { k: "pnl", label: "P&L", right: true },
    { k: "risk", label: "Risk", right: true },
    { k: "bot", label: "Bot" },
  ];
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-2 border-b px-2 text-xs">
    <span class="relative">
      <Search
        class="text-muted-foreground pointer-events-none absolute top-1/2 left-2 size-3.5 -translate-y-1/2"
      />
      <input
        bind:value={q}
        placeholder="Market or bot"
        aria-label="Filter positions"
        class="bg-background/40 h-7 w-36 rounded-md border pr-2 pl-7 text-xs"
      />
    </span>
    <span class="text-muted-foreground ml-auto">Group</span>
    {#each ["none", "pod", "bot"] as const as g (g)}
      <button
        type="button"
        class={cn(
          "h-6 rounded-md px-2 capitalize",
          group === g
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={group === g}
        onclick={() => (group = g)}>{g}</button
      >
    {/each}
  </div>
  <div class="min-h-0 flex-1 overflow-auto">
    <table class="w-full text-sm whitespace-nowrap">
      <thead
        class="bg-panel text-muted-foreground sticky top-0 z-10 text-left text-xs"
      >
        <tr class="border-b">
          {#each COLS as c (c.k)}
            <th
              class={cn(
                "py-1.5 font-normal",
                c.right ? "pr-3 text-right" : "pr-3 first:pl-3",
              )}
            >
              <button
                type="button"
                class="hover:text-foreground inline-flex items-center gap-0.5"
                onclick={() => sortBy(c.k)}
              >
                {c.label}{#if key === c.k}{#if desc}<ArrowDown
                      class="size-3"
                    />{:else}<ArrowUp class="size-3" />{/if}{/if}
              </button>
            </th>
          {/each}
          <th class="py-1.5 pr-3 font-normal">Account</th>
        </tr>
      </thead>
      <tbody>
        {#each groups as g (g.name)}
          {#if g.name}
            <tr class="bg-muted/30"
              ><td colspan="6" class="px-3 py-1 text-xs font-medium"
                >{g.name}
                <span class="text-muted-foreground font-normal"
                  >· {usd(g.items.reduce((n, r) => n + value(r), 0))}</span
                ></td
              ></tr
            >
          {/if}
          {#each g.items as r (r.sym + r.bot)}
            <tr class="border-b border-border/50">
              <td class="py-1.5 pr-3 pl-3">
                <span class="flex items-center gap-2">
                  <span
                    class="h-4 w-0.5 rounded-full"
                    style="background: var(--tone-{r.mode === 'LIVE'
                      ? 'live'
                      : 'paper'})"
                  ></span>
                  <span class="font-medium">{r.sym}</span>
                  <span class="num text-muted-foreground text-xs"
                    >{r.qty} {r.unit}</span
                  >
                </span>
              </td>
              <td class="num py-1.5 pr-3 text-right">{usd(value(r))}</td>
              <td
                class={cn(
                  "num py-1.5 pr-3 text-right",
                  pnl(r) >= 0 ? "text-success" : "text-destructive",
                )}>{pnl(r) >= 0 ? "+" : ""}{pnl(r).toFixed(2)}%</td
              >
              <td
                class="num text-muted-foreground py-1.5 pr-3 text-right text-xs"
                >{r.risk ? `${r.risk} R` : "—"}</td
              >
              <td class="py-1.5 pr-3 text-xs">{r.bot}</td>
              <td class="text-muted-foreground py-1.5 pr-3 text-xs"
                >{ACCOUNTS.find((a) => a.id === r.account)?.name}</td
              >
            </tr>
          {/each}
        {/each}
      </tbody>
    </table>
  </div>
  <p class="text-muted-foreground border-t px-3 py-1.5 text-xs">
    Sample prices tick every second. Nothing is ordered from here: orders come
    only from bots inside their pods.
  </p>
</div>
