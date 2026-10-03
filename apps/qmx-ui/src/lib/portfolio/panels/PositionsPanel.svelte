<script lang="ts">
  /**
   * Open positions and working orders across every account, ticking live.
   * The Book's own record (frozen R) is shown beside what the broker reports;
   * they are never merged.
   */
  import { onMount } from "svelte";
  import { cn } from "$lib/utils";
  import { ACCOUNTS } from "../demo";
  import { portfolio } from "../portfolio.svelte";

  type Pos = {
    sym: string;
    side: "Long" | "Short";
    qty: string;
    entry: number;
    last: number;
    r: string;
    book: string;
    account: string;
    mode: "LIVE" | "PAPER";
    p: number;
  };
  let rows = $state<Pos[]>([
    {
      sym: "BTCUSDT",
      side: "Long",
      qty: "0.18 BTC",
      entry: 63120,
      last: 64210,
      r: "1.0 R",
      book: "Crypto momentum",
      account: "bn-main",
      mode: "LIVE",
      p: 0,
    },
    {
      sym: "ETHUSDT",
      side: "Long",
      qty: "2.4 ETH",
      entry: 3080,
      last: 3118,
      r: "0.7 R",
      book: "Crypto momentum",
      account: "bn-main",
      mode: "LIVE",
      p: 1,
    },
    {
      sym: "EURUSD",
      side: "Long",
      qty: "1.20 lots",
      entry: 1.0849,
      last: 1.0883,
      r: "1.2 R",
      book: "FX core",
      account: "ic-live",
      mode: "LIVE",
      p: 4,
    },
    {
      sym: "US500",
      side: "Long",
      qty: "0.40 lots",
      entry: 5562,
      last: 5531,
      r: "0.4 R",
      book: "Prop challenge",
      account: "ftmo-1",
      mode: "LIVE",
      p: 1,
    },
    {
      sym: "BTC basis",
      side: "Short",
      qty: "0.10 BTC",
      entry: 64400,
      last: 64280,
      r: "0.6 R",
      book: "Crypto neutral",
      account: "by-demo",
      mode: "PAPER",
      p: 0,
    },
  ]);
  const ORDERS = [
    {
      sym: "SOLUSDT",
      what: "Buy stop 0.9 R",
      price: "152.40",
      book: "Crypto momentum",
      mode: "LIVE",
    },
    {
      sym: "GBPUSD",
      what: "Limit sell 0.8 R",
      price: "1.2790",
      book: "FX core",
      mode: "LIVE",
    },
  ];
  onMount(() => {
    const t = setInterval(() => {
      rows = rows.map((r) => ({
        ...r,
        last: +(r.last * (1 + (Math.random() - 0.5) * 0.0006)).toFixed(r.p),
      }));
    }, 1200);
    return () => clearInterval(t);
  });
  const shown = $derived(
    rows.filter(
      (r) =>
        portfolio.world === "all" ||
        (portfolio.world === "live") === (r.mode === "LIVE"),
    ),
  );
  const pnl = (r: Pos) =>
    (((r.side === "Long" ? 1 : -1) * (r.last - r.entry)) / r.entry) * 100;
</script>

<div class="h-full overflow-auto">
  <table class="w-full text-sm whitespace-nowrap">
    <thead
      class="bg-panel text-muted-foreground sticky top-0 text-left text-xs"
    >
      <tr class="border-b">
        <th class="py-1.5 pl-3 font-normal">Market</th>
        <th class="py-1.5 pr-3 font-normal">Side</th>
        <th class="py-1.5 pr-3 font-normal">Size</th>
        <th class="py-1.5 pr-3 text-right font-normal">Entry</th>
        <th class="py-1.5 pr-3 text-right font-normal">Last</th>
        <th class="py-1.5 pr-3 text-right font-normal">P&amp;L</th>
        <th class="py-1.5 pr-3 font-normal">Risk</th>
        <th class="py-1.5 pr-3 font-normal">Book · account</th>
      </tr>
    </thead>
    <tbody>
      {#each shown as r (r.sym + r.account)}
        <tr class="border-b border-border/50">
          <td class="py-1.5 pl-3">
            <span class="flex items-center gap-2">
              <span
                class={cn(
                  "h-4 w-0.5 rounded-full",
                  r.mode === "LIVE"
                    ? "bg-[var(--tone-live)]"
                    : "bg-[var(--tone-paper)]",
                )}
              ></span>
              <span class="font-medium">{r.sym}</span>
            </span>
          </td>
          <td class="py-1.5 pr-3">{r.side}</td>
          <td class="num py-1.5 pr-3 text-xs">{r.qty}</td>
          <td class="num py-1.5 pr-3 text-right">{r.entry}</td>
          <td class="num py-1.5 pr-3 text-right">{r.last}</td>
          <td
            class={cn(
              "num py-1.5 pr-3 text-right",
              pnl(r) >= 0 ? "text-success" : "text-destructive",
            )}>{pnl(r) >= 0 ? "+" : ""}{pnl(r).toFixed(2)}%</td
          >
          <td class="num text-muted-foreground py-1.5 pr-3 text-xs">{r.r}</td>
          <td class="text-muted-foreground py-1.5 pr-3 text-xs"
            >{r.book} · {ACCOUNTS.find((a) => a.id === r.account)?.name}</td
          >
        </tr>
      {/each}
      {#each ORDERS.filter((o) => portfolio.world !== "paper") as o (o.sym)}
        <tr class="border-b border-border/50">
          <td class="py-1.5 pl-3 font-medium">{o.sym}</td>
          <td class="py-1.5 pr-3" colspan="2">{o.what}</td>
          <td class="num py-1.5 pr-3 text-right">{o.price}</td>
          <td class="text-muted-foreground py-1.5 pr-3 text-right text-xs"
            >working</td
          >
          <td></td><td></td>
          <td class="text-muted-foreground py-1.5 pr-3 text-xs">{o.book}</td>
        </tr>
      {/each}
    </tbody>
  </table>
  <p class="text-muted-foreground px-3 py-2 text-xs">
    Sample prices tick every second. Nothing is ordered from this screen: orders
    come only from bots inside their Books.
  </p>
</div>
