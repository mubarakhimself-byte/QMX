<script lang="ts">
  /**
   * A watchlist: price, change and a small line per market, filtered to one
   * broker or one account (CFDs trade at IC Markets, crypto at the CCXT
   * exchanges).
   */
  import Check from "@lucide/svelte/icons/check";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { linePath, equityWalk } from "$lib/qmx/charts";
  import { cn } from "$lib/utils";
  import { MARKETS, isCfd } from "$lib/demo/markets";
  import { ACCOUNTS, VENUES } from "$lib/portfolio/demo";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { fmtPx, home } from "../home.svelte";

  const size = panelSize();
  const lines = MARKETS.map((c, i) => {
    const v = equityWalk(400 + i, 40, c.chg / 4000, 0.01);
    return {
      ...c,
      path: linePath(v, 80, 24, [Math.min(...v), Math.max(...v)]),
    };
  });

  const venueOf = (from: string) =>
    from.startsWith("venue:")
      ? from.slice(6)
      : from.startsWith("acct:")
        ? ACCOUNTS.find((a) => a.id === from.slice(5))?.venue
        : undefined;
  const label = $derived.by(() => {
    const f = home.marketsFrom;
    if (f.startsWith("venue:"))
      return VENUES.find((v) => v.id === f.slice(6))?.name ?? "All";
    if (f.startsWith("acct:"))
      return ACCOUNTS.find((a) => a.id === f.slice(5))?.name ?? "All";
    return "All accounts";
  });
  const shown = $derived.by(() => {
    const venue = venueOf(home.marketsFrom);
    if (!venue) return lines;
    return lines.filter((l) =>
      venue === "icmarkets" ? isCfd(l.kind) : !isCfd(l.kind),
    );
  });
  const best = $derived(
    [...shown].sort((a, b) => Math.abs(b.chg) - Math.abs(a.chg))[0],
  );
  const signed = (v: number) =>
    `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(2)}%`;
</script>

{#snippet item(value: string, text: string, indent = false)}
  <DropdownMenu.Item
    class={cn(indent && "pl-6")}
    onclick={() => home.setMarketsFrom(value)}
  >
    <span class="flex-1">{text}</span>
    {#if home.marketsFrom === value}<Check class="size-4" />{/if}
  </DropdownMenu.Item>
{/snippet}

{#snippet filter()}
  <DropdownMenu.Root>
    <DropdownMenu.Trigger
      class="hover:bg-muted flex h-7 max-w-full min-w-0 items-center gap-1 rounded-md px-2 text-xs"
      aria-label={`Markets from: ${label}`}
    >
      <span class="truncate">{label}</span>
      <ChevronDown class="size-3.5 shrink-0" />
    </DropdownMenu.Trigger>
    <DropdownMenu.Content align="start" class="w-56">
      {@render item("all", "All accounts")}
      {#each VENUES as v (v.id)}
        <DropdownMenu.Separator />
        {@render item(`venue:${v.id}`, v.name)}
        {#each ACCOUNTS.filter((a) => a.venue === v.id) as a (a.id)}
          {@render item(`acct:${a.id}`, a.name, true)}
        {/each}
      {/each}
    </DropdownMenu.Content>
  </DropdownMenu.Root>
{/snippet}

{#if size.mode === "compact"}
  <div class="p-panel gap-row flex h-full flex-col overflow-hidden">
    {@render filter()}
    <ul class="flex flex-col">
      {#each shown as c (c.sym)}
        <li
          class="py-row grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 text-sm"
          title={c.name}
        >
          <span class="truncate font-medium">{c.sym}</span>
          <span
            class={cn(
              "num text-right",
              c.chg >= 0 ? "text-success" : "text-destructive",
            )}>{signed(c.chg)}</span
          >
        </li>
      {/each}
    </ul>
  </div>
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-10 shrink-0 items-center gap-2">
      {@render filter()}
      {#if best}<span class="text-muted-foreground ml-auto truncate text-xs"
          >Biggest move {best.sym}
          <span class="num">{signed(best.chg)}</span></span
        >{/if}
    </div>
    <ul class="px-panel pb-panel min-h-0 flex-1 overflow-auto">
      {#each shown as c (c.sym)}
        <li
          class={cn(
            "py-row grid items-center gap-3",
            size.mode === "expanded"
              ? "grid-cols-[5rem_minmax(0,14rem)_1fr_6rem_5rem]"
              : "grid-cols-[4.5rem_1fr_5rem_4rem]",
          )}
          title={c.name}
        >
          <span class="text-sm font-medium">{c.sym}</span>
          {#if size.mode === "expanded"}<span
              class="text-muted-foreground truncate text-sm">{c.name}</span
            >{/if}
          <svg
            viewBox="0 0 80 24"
            class="h-6 w-full"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path
              d={c.path}
              fill="none"
              stroke={c.chg >= 0 ? "var(--success)" : "var(--destructive)"}
              stroke-width="1.5"
              vector-effect="non-scaling-stroke"
            />
          </svg>
          <span class="num text-right text-sm">{fmtPx(c.px)}</span>
          <span
            class={cn(
              "num text-right text-sm",
              c.chg >= 0 ? "text-success" : "text-destructive",
            )}>{signed(c.chg)}</span
          >
        </li>
      {/each}
    </ul>
  </div>
{/if}
