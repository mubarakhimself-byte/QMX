<script lang="ts">
  /** Coming up: macro events and crypto events that move prices, with which pods care. Sample items. */
  import { cn } from "$lib/utils";

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
  const DOT = {
    high: "bg-destructive",
    medium: "bg-warning",
    low: "bg-muted-foreground",
  };
</script>

<ul class="h-full overflow-auto p-1.5">
  {#each EVENTS as e (e.what)}
    <li class="flex items-start gap-3 rounded-md px-2 py-2">
      <span
        class={cn(
          "mt-1.5 size-2 shrink-0 rounded-full",
          DOT[e.impact as keyof typeof DOT],
        )}
      ></span>
      <span class="min-w-0 flex-1">
        <span class="block text-sm font-medium">{e.what}</span>
        <span class="text-muted-foreground block text-[13px]"
          >{e.when} · {e.kind} · {e.pods}</span
        >
      </span>
    </li>
  {/each}
</ul>
