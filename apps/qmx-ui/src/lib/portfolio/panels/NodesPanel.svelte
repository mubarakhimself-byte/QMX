<script lang="ts">
  /**
   * Trading servers you can act on: test latency to each exchange (runs a
   * demo probe here), restart, drain (finish open work, take nothing new),
   * move accounts to another server, open its log. Destructive actions ask
   * first and need the trading node.
   */
  import Server from "@lucide/svelte/icons/server";
  import Plus from "@lucide/svelte/icons/plus";
  import Activity from "@lucide/svelte/icons/activity";
  import RotateCw from "@lucide/svelte/icons/rotate-cw";
  import PauseCircle from "@lucide/svelte/icons/circle-pause";
  import ArrowRightLeft from "@lucide/svelte/icons/arrow-right-left";
  import ScrollText from "@lucide/svelte/icons/scroll-text";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, NODES } from "../demo";

  const TONE = {
    up: "bg-success",
    degraded: "bg-warning",
    down: "bg-destructive",
  };
  let probing = $state<string | null>(null);
  let probes = $state<Record<string, number[]>>({});
  function probe(id: string, base: number[]) {
    probing = id;
    setTimeout(() => {
      probes[id] = base.map((ms) =>
        Math.round(ms * (0.8 + Math.random() * 0.5)),
      );
      probing = null;
    }, 900);
  }
  const act = (what: string, node: string) =>
    workbench.notify(
      `${what} ${node}: needs the trading node. You'd confirm first; open positions stay protected.`,
    );
</script>

<div class="flex h-full flex-col">
  <ul class="min-h-0 flex-1 overflow-auto">
    {#each NODES as n (n.id)}
      <li class="border-b border-border/50 px-3 py-2.5">
        <div class="flex items-center gap-2">
          <Server class="text-muted-foreground size-4" />
          <span class="font-medium">{n.name}</span>
          <span class="text-muted-foreground text-xs">{n.where}</span>
          <span
            class={cn(
              "ml-auto size-2 rounded-full",
              TONE[n.status],
              n.status !== "up" && "remote-pulse",
            )}
          ></span>
          <span class="text-xs">{n.status}</span>
        </div>
        <div
          class="mt-2 grid grid-cols-[repeat(auto-fill,minmax(7rem,1fr))] gap-1.5"
        >
          {#each n.latency as l, i (l.venue)}
            {@const ms = probes[n.id]?.[i] ?? l.ms}
            <span class="bg-muted/40 rounded-md px-2 py-1 text-xs">
              <span class="text-muted-foreground block">{l.venue}</span>
              <span class={cn("num text-base", ms > 100 ? "text-warning" : "")}
                >{ms} ms</span
              >
            </span>
          {/each}
          <span class="bg-muted/40 rounded-md px-2 py-1 text-xs">
            <span class="text-muted-foreground block">CPU · up</span>
            <span class={cn("num text-base", n.cpu > 65 ? "text-warning" : "")}
              >{n.cpu}%</span
            >
            <span class="text-muted-foreground"> · {n.uptime}</span>
          </span>
        </div>
        <p class="text-muted-foreground mt-1.5 text-xs">
          Carries {ACCOUNTS.filter((a) => a.node === n.id)
            .map((a) => a.name)
            .join(", ") || "nothing"}
        </p>
        <div class="mt-2 flex flex-wrap gap-1">
          <Button
            size="sm"
            variant="outline"
            class="h-7"
            disabled={probing === n.id}
            onclick={() =>
              probe(
                n.id,
                n.latency.map((l) => l.ms),
              )}
          >
            <Activity
              class={cn(probing === n.id && "animate-pulse")}
            />{probing === n.id ? "Testing…" : "Test latency"}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            class="h-7"
            onclick={() => act("Restart", n.name)}><RotateCw />Restart</Button
          >
          <Button
            size="sm"
            variant="ghost"
            class="h-7"
            onclick={() => act("Drain", n.name)}><PauseCircle />Drain</Button
          >
          <Button
            size="sm"
            variant="ghost"
            class="h-7"
            onclick={() => act("Move accounts off", n.name)}
            ><ArrowRightLeft />Move accounts</Button
          >
          <Button
            size="sm"
            variant="ghost"
            class="h-7"
            onclick={() => act("Open the log of", n.name)}
            ><ScrollText />Log</Button
          >
        </div>
      </li>
    {/each}
  </ul>
  <button
    type="button"
    class="text-muted-foreground hover:text-foreground flex h-9 shrink-0 items-center gap-1.5 border-t px-3 text-xs"
    onclick={() =>
      workbench.notify(
        "A new trading server is set up from Settings → Compute: pick a provider and region near your exchange.",
      )}><Plus class="size-3.5" />Add a trading server</button
  >
</div>
