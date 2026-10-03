<script lang="ts">
  /**
   * Trading servers in the Portfolio header: health and best latency at a
   * glance; click one for its numbers and actions. The full panel is there
   * too for anyone who wants it as a tile.
   */
  import Server from "@lucide/svelte/icons/server";
  import Activity from "@lucide/svelte/icons/activity";
  import RotateCw from "@lucide/svelte/icons/rotate-cw";
  import PauseCircle from "@lucide/svelte/icons/circle-pause";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, NODES } from "./demo";

  const TONE = {
    up: "bg-success",
    degraded: "bg-warning",
    down: "bg-destructive",
  };
  const act = (what: string, node: string) =>
    workbench.notify(
      `${what} ${node}: needs the trading node. You'd confirm first; open positions stay protected.`,
    );
</script>

<div class="flex shrink-0 items-center gap-1" aria-label="Trading servers">
  {#each NODES as n (n.id)}
    {@const best = Math.min(...n.latency.map((l) => l.ms))}
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        class="hover:bg-muted data-[state=open]:bg-muted flex h-7 shrink-0 items-center gap-1.5 rounded-md border px-2 text-xs whitespace-nowrap"
        aria-label={`${n.name} server, ${n.status}`}
        title={`${n.name} · ${best} ms`}
      >
        <span
          class={cn(
            "size-1.5 rounded-full",
            TONE[n.status],
            n.status !== "up" && "remote-pulse",
          )}
        ></span>
        <Server class="text-muted-foreground size-3.5" /><span
          class="max-w-20 truncate">{n.name}</span
        >
        <span class="num text-muted-foreground hidden 2xl:inline"
          >{best} ms</span
        >
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="end" class="w-72">
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
            ><span class="text-muted-foreground block">Up</span><span
              class="text-sm">{n.uptime}</span
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
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  {/each}
</div>
