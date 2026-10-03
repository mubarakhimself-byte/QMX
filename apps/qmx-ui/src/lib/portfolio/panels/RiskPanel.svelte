<script lang="ts">
  /**
   * Every Book in one grid: mode, where risk comes from, equity, loss budget
   * used today, distance to the kill line, kill-switch level and the worst
   * rule. Click a row to select it. Platform totals are reports only; they
   * never gate an order (DEC-0143).
   */
  import Sparkline from "$lib/demo/Sparkline.svelte";
  import { cn } from "$lib/utils";
  import { BOOKS, accountById, sizing } from "../demo";
  import { KSA_TONE, RULE_TONE, usd } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  const rows = $derived(
    BOOKS.filter((b) =>
      portfolio.world === "all"
        ? true
        : portfolio.world === "live"
          ? b.mode === "LIVE"
          : b.mode === "PAPER",
    ),
  );
  const worst = (b: (typeof BOOKS)[number]) =>
    b.rules.find((r) => r.state === "tripped") ??
    b.rules.find((r) => r.state === "near") ??
    b.rules[0];
  const totalEq = $derived(rows.reduce((n, b) => n + b.equity, 0));
</script>

<div class="flex h-full flex-col">
  <div class="min-h-0 flex-1 overflow-auto">
    <table class="w-full text-sm whitespace-nowrap">
      <thead
        class="bg-panel text-muted-foreground sticky top-0 z-10 text-left text-xs"
      >
        <tr class="border-b">
          <th class="py-1.5 pl-3 font-normal">Book</th>
          <th class="py-1.5 pr-3 font-normal">Account</th>
          <th class="py-1.5 pr-3 font-normal">Risk from</th>
          <th class="py-1.5 pr-3 text-right font-normal">Equity</th>
          <th class="py-1.5 pr-3 font-normal">90 days</th>
          <th class="py-1.5 pr-3 font-normal">Loss budget today</th>
          <th class="py-1.5 pr-3 font-normal">Above kill line</th>
          <th class="py-1.5 pr-3 font-normal">Kill switch</th>
          <th class="py-1.5 pr-3 font-normal">Closest rule</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as b (b.id)}
          {@const a = accountById(b.account)}
          {@const s = sizing(b)}
          {@const used = Math.min(1, b.lossToday / s.budget)}
          {@const room = Math.max(
            0,
            (b.equity - b.killLine) / (b.capital - b.killLine),
          )}
          {@const w = worst(b)}
          <tr
            class={cn(
              "hover:bg-muted/50 cursor-pointer border-b border-border/50",
              portfolio.book === b.id && "bg-primary/10",
            )}
            onclick={() => (portfolio.book = b.id)}
          >
            <td class="py-1.5 pr-3 pl-3">
              <span class="flex items-center gap-2">
                <span
                  class={cn(
                    "h-4 w-0.5 rounded-full",
                    b.mode === "LIVE"
                      ? "bg-[var(--tone-live)]"
                      : "bg-[var(--tone-paper)]",
                  )}
                ></span>
                <span class="font-medium">{b.name}</span>
                <span class="text-muted-foreground text-xs">{b.version}</span>
                {#if b.binding === "stood-down"}<span
                    class="text-destructive text-xs">stood down</span
                  >{/if}
              </span>
            </td>
            <td class="text-muted-foreground py-1.5 pr-3 text-xs">{a?.name}</td>
            <td class="py-1.5 pr-3 text-xs">
              <span
                class={cn(
                  "rounded px-1.5 py-0.5",
                  b.engine.kind === "rules"
                    ? "bg-muted"
                    : "bg-info/12 text-info",
                )}>{b.engine.label}</span
              >
            </td>
            <td class="num py-1.5 pr-3 text-right">{usd(b.equity)}</td>
            <td class="py-1.5 pr-3"
              ><span class="block h-6 w-24"
                ><Sparkline values={b.equitySeries} /></span
              ></td
            >
            <td class="py-1.5 pr-3">
              <span class="flex items-center gap-2">
                <span class="bg-muted h-1.5 w-20 overflow-hidden rounded-full"
                  ><span
                    class={cn(
                      "block h-full",
                      used > 0.75 ? "bg-warning" : "bg-primary",
                    )}
                    style="width:{used * 100}%"
                  ></span></span
                >
                <span class="num text-xs"
                  >{usd(b.lossToday)} / {usd(s.budget)}</span
                >
              </span>
            </td>
            <td class="py-1.5 pr-3">
              <span class="flex items-center gap-2">
                <span class="bg-muted h-1.5 w-20 overflow-hidden rounded-full"
                  ><span
                    class={cn(
                      "block h-full",
                      room < 0.25 ? "bg-destructive" : "bg-success",
                    )}
                    style="width:{room * 100}%"
                  ></span></span
                >
                <span class="num text-xs">{usd(b.equity - b.killLine)}</span>
              </span>
            </td>
            <td class="py-1.5 pr-3"
              ><span class="flex items-center gap-1.5 text-xs"
                ><span
                  class={cn("size-2 rounded-full", KSA_TONE[a?.ksa ?? "GREEN"])}
                ></span>{a?.ksa}</span
              ></td
            >
            <td class="py-1.5 pr-3 text-xs">
              <span class="flex items-center gap-1.5"
                ><span class={cn("size-2 rounded-full", RULE_TONE[w.state])}
                ></span>{w.name}: {w.value}</span
              >
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  <p
    class="text-muted-foreground flex items-center gap-3 border-t px-3 py-2 text-xs"
  >
    <span
      >All Books shown: <span class="num text-foreground">{usd(totalEq)}</span
      ></span
    >
    <span
      >Totals across brokers are reports only; each Book's own limits do the
      stopping.</span
    >
  </p>
</div>
