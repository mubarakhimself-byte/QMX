<script lang="ts">
  /** The machines that trade: where they are, latency to their broker, health, and which accounts they carry. */
  import Server from "@lucide/svelte/icons/server";
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, NODES } from "../demo";

  const TONE = {
    up: "bg-success",
    degraded: "bg-warning",
    down: "bg-destructive",
  };
</script>

<div class="flex h-full flex-col">
  <ul class="min-h-0 flex-1 overflow-auto">
    {#each NODES as n (n.id)}
      <li class="border-b border-border/50 px-3 py-2">
        <div class="flex items-center gap-2 text-sm">
          <Server class="text-muted-foreground size-4" />
          <span class="font-medium">{n.name}</span>
          <span
            class="rounded px-1.5 text-[11px]"
            style="background: color-mix(in oklab, {n.mode === 'live'
              ? 'var(--tone-live)'
              : 'var(--tone-paper)'} 22%, transparent)">{n.mode}</span
          >
          <span
            class={cn(
              "ml-auto size-2 rounded-full",
              TONE[n.status],
              n.status !== "up" && "remote-pulse",
            )}
          ></span>
          <span class="text-muted-foreground text-xs">{n.status}</span>
        </div>
        <p class="text-muted-foreground mt-0.5 text-xs">
          {n.where} · {n.latency}
        </p>
        <p class="mt-0.5 text-xs">
          {ACCOUNTS.filter((a) => a.node === n.id)
            .map((a) => a.name)
            .join(", ") || "No accounts"}
        </p>
        {#if n.status === "degraded"}<p class="text-warning mt-0.5 text-xs">
            Heartbeat late twice in 10 minutes; orders still flowing.
          </p>{/if}
      </li>
    {/each}
  </ul>
  <button
    type="button"
    class="text-muted-foreground hover:text-foreground flex h-9 shrink-0 items-center gap-1.5 border-t px-3 text-xs"
    onclick={() =>
      workbench.notify(
        "Adding a trading server sets up a new node; manage machines in Settings → Compute.",
      )}><Plus class="size-3.5" />Add a trading server</button
  >
</div>
