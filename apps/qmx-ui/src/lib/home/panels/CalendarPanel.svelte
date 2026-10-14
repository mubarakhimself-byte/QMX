<script lang="ts">
  /** Coming up: macro events and crypto events that move prices, with which pods care. Sample items. */
  import { cn } from "$lib/utils";
  import { panelSize } from "$lib/workbench/tiles/panel-size";

  const size = panelSize();

  const EVENTS = [
    {
      when: "Today 14:30",
      what: "US jobs report",
      kind: "Macro",
      impact: "high",
      pods: "All pods: news guard on",
    },
    {
      when: "Tomorrow",
      what: "SOL token unlock (2.1M)",
      kind: "Crypto",
      impact: "medium",
      pods: "Alt momentum",
    },
    {
      when: "Wed 18:00",
      what: "FOMC rate decision",
      kind: "Macro",
      impact: "high",
      pods: "All pods: news guard on",
    },
    {
      when: "Thu",
      what: "ETH network upgrade vote",
      kind: "Crypto",
      impact: "low",
      pods: "BTC & ETH core",
    },
    {
      when: "Sat",
      what: "Weekend: thin order books",
      kind: "Market",
      impact: "medium",
      pods: "Weekend throttle",
    },
  ];
  let high = $state(false);
  const shown = $derived(
    high ? EVENTS.filter((e) => e.impact === "high") : EVENTS,
  );
  const DOT = {
    high: "bg-destructive",
    medium: "bg-warning",
    low: "bg-muted-foreground",
  };
</script>

{#if size.mode === "compact"}
  <div class="p-panel gap-row flex h-full flex-col overflow-hidden">
    <p class="text-muted-foreground text-xs">Next · {EVENTS[0].when}</p>
    <p class="text-base font-medium">{EVENTS[0].what}</p>
    <ul class="mt-group flex flex-col gap-0.5 text-sm">
      {#each EVENTS.slice(1) as e (e.what)}
        <li class="flex min-w-0 items-center gap-2" title={e.when}>
          <span
            class={cn(
              "size-1.5 shrink-0 rounded-full",
              DOT[e.impact as keyof typeof DOT],
            )}
          ></span>
          <span class="truncate">{e.what}</span>
        </li>
      {/each}
    </ul>
  </div>
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-10 shrink-0 items-center">
      <div
        class="bg-muted flex rounded-md p-0.5 text-xs"
        role="radiogroup"
        aria-label="Show"
      >
        {#each [false, true] as h (h)}
          <button
            type="button"
            role="radio"
            aria-checked={high === h}
            class={cn(
              "h-6 rounded px-2.5",
              high === h
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
            onclick={() => (high = h)}>{h ? "High impact" : "All"}</button
          >
        {/each}
      </div>
    </div>
    <ul class="px-panel pb-panel min-h-0 flex-1 overflow-auto">
      {#each shown as e (e.what)}
        <li class="py-row flex items-start gap-3">
          <span
            class={cn(
              "mt-2 size-2 shrink-0 rounded-full",
              DOT[e.impact as keyof typeof DOT],
            )}
          ></span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm">{e.what}</span>
            <span class="text-muted-foreground block truncate text-xs"
              >{e.when}{size.mode === "expanded"
                ? ` · ${e.kind} · ${e.pods}`
                : ` · ${e.pods}`}</span
            >
          </span>
        </li>
      {/each}
    </ul>
  </div>
{/if}
