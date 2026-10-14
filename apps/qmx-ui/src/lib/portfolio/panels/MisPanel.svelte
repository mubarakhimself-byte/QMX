<script lang="ts">
  /**
   * MIS: the trading servers' market labelers (regime, volatility, liquidity, news
   * state) and who listens to them (pod guards and the kill switch, never
   * bots). Candidate labelers run in a shadow lane until promoted. A big
   * revamp is coming (operator, 2026-10-03); this is the placeholder shape.
   */
  import Radar from "@lucide/svelte/icons/radar";
  import { cn } from "$lib/utils";

  const LABELERS = [
    {
      name: "Volatility state",
      value: "elevated",
      since: "09:10",
      lane: "live",
      feeds: "Pod guards, kill switch",
    },
    {
      name: "Session",
      value: "London–NY overlap",
      since: "12:00",
      lane: "live",
      feeds: "Pod guards",
    },
    {
      name: "News state",
      value: "CPI window in 2h",
      since: "—",
      lane: "live",
      feeds: "Protection windows",
    },
    {
      name: "Regime (HMM)",
      value: "trending",
      since: "yesterday",
      lane: "shadow",
      feeds: "Nothing yet: shadow only",
    },
    {
      name: "Liquidity (crypto)",
      value: "thin weekend book",
      since: "Sat",
      lane: "shadow",
      feeds: "Nothing yet: shadow only",
    },
  ];
</script>

<div class="flex h-full flex-col">
  <ul class="min-h-0 flex-1 overflow-auto">
    {#each LABELERS as l (l.name)}
      <li class="flex items-center gap-3 border-b border-border/50 px-3 py-2">
        <Radar
          class={cn(
            "size-4 shrink-0",
            l.lane === "live" ? "text-primary" : "text-muted-foreground",
          )}
        />
        <div class="min-w-0 flex-1">
          <p class="text-sm">
            <span class="font-medium">{l.name}</span>
            <span class="text-muted-foreground text-xs">since {l.since}</span>
          </p>
          <p class="text-muted-foreground text-xs">Feeds: {l.feeds}</p>
        </div>
        <span class="rounded-md border px-2 py-0.5 text-xs">{l.value}</span>
        <span
          class={cn(
            "w-14 text-right text-xs",
            l.lane === "shadow" ? "text-muted-foreground" : "text-success",
          )}>{l.lane}</span
        >
      </li>
    {/each}
  </ul>
  <p class="text-muted-foreground border-t px-3 py-2 text-xs">
    Shadow labelers are watched, not obeyed, until you promote them. MIS is
    being redesigned; build new labelers in the Lab.
  </p>
</div>
