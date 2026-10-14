<script lang="ts">
  /**
   * Trading servers in the Portfolio header: health and best latency at a
   * glance; click one for its numbers and actions. On wide screens each
   * server has its own chip; narrower, one "Servers" chip holds them all so
   * the header never spills. The full panel is there too as a tile.
   */
  import Server from "@lucide/svelte/icons/server";
  import Activity from "@lucide/svelte/icons/activity";
  import RotateCw from "@lucide/svelte/icons/rotate-cw";
  import PauseCircle from "@lucide/svelte/icons/circle-pause";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, NODES, type Node } from "./demo";

  const TONE = {
    up: "bg-success",
    degraded: "bg-warning",
    down: "bg-destructive",
  };
  const act = (what: string, node: string) =>
    workbench.notify(
      `${what} ${node}: needs the trading server. You'd confirm first; open positions stay protected.`,
    );
  const best = (n: Node) => Math.min(...n.latency.map((l) => l.ms));
  const chip =
    "hover:bg-muted data-[state=open]:bg-muted flex h-7 shrink-0 items-center gap-1.5 rounded-md border px-2 text-xs whitespace-nowrap";
</script>

{#snippet dot(n: Node)}
  <span
    class={cn(
      "size-1.5 rounded-full",
      TONE[n.status],
      n.status !== "up" && "remote-pulse",
    )}
  ></span>
{/snippet}

{#snippet details(n: Node)}
  <DropdownMenu.Label>{n.name} · {n.where}</DropdownMenu.Label>
  <div class="grid grid-cols-2 gap-1 px-2 pb-2 text-xs">
    {#each n.latency as l (l.venue)}
      <span class="bg-muted/50 rounded px-2 py-1"
        ><span class="text-muted-foreground block">{l.venue}</span><span
          class="num text-sm">{l.ms} ms</span
        ></span
      >
    {/each}
    <span class="bg-muted/50 rounded px-2 py-1"
      ><span class="text-muted-foreground block">CPU</span><span
        class="num text-sm">{n.cpu}%</span
      ></span
    >
    <span class="bg-muted/50 rounded px-2 py-1"
      ><span class="text-muted-foreground block">Up</span><span class="text-sm"
        >{n.uptime}</span
      ></span
    >
  </div>
  <p class="text-muted-foreground px-2 pb-2 text-xs">
    Carries {ACCOUNTS.filter((a) => a.node === n.id)
      .map((a) => a.name)
      .join(", ")}
  </p>
  <DropdownMenu.Separator />
  <DropdownMenu.Item onclick={() => act("Test latency on", n.name)}
    ><Activity />Test latency</DropdownMenu.Item
  >
  <DropdownMenu.Item onclick={() => act("Restart", n.name)}
    ><RotateCw />Restart</DropdownMenu.Item
  >
  <DropdownMenu.Item onclick={() => act("Drain", n.name)}
    ><PauseCircle />Drain: finish open work, take nothing new</DropdownMenu.Item
  >
{/snippet}

<div
  class="hidden shrink-0 items-center gap-1 min-[1800px]:flex"
  aria-label="Trading servers"
>
  {#each NODES as n (n.id)}
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        class={chip}
        aria-label={`${n.name} server, ${n.status}`}
        title={`${n.name} · ${best(n)} ms`}
      >
        {@render dot(n)}
        <Server class="text-muted-foreground size-3.5" /><span
          class="max-w-20 truncate">{n.name}</span
        >
        <span class="num text-muted-foreground">{best(n)} ms</span>
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="end" class="w-72">
        {@render details(n)}
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  {/each}
</div>

<DropdownMenu.Root>
  <DropdownMenu.Trigger
    class={cn(chip, "min-[1800px]:hidden")}
    aria-label={`Trading servers: ${NODES.map((n) => `${n.name} ${n.status}`).join(", ")}`}
    title="Trading servers"
  >
    <Server class="text-muted-foreground size-3.5" />Servers
    <span class="flex items-center gap-1">
      {#each NODES as n (n.id)}{@render dot(n)}{/each}
    </span>
  </DropdownMenu.Trigger>
  <DropdownMenu.Content align="end" class="w-60">
    <DropdownMenu.Label>Trading servers</DropdownMenu.Label>
    {#each NODES as n (n.id)}
      <DropdownMenu.Sub>
        <DropdownMenu.SubTrigger>
          {@render dot(n)}
          <span class="flex-1">{n.name}</span>
          <span class="num text-muted-foreground text-xs">{best(n)} ms</span>
        </DropdownMenu.SubTrigger>
        <DropdownMenu.SubContent class="w-72">
          {@render details(n)}
        </DropdownMenu.SubContent>
      </DropdownMenu.Sub>
    {/each}
  </DropdownMenu.Content>
</DropdownMenu.Root>
