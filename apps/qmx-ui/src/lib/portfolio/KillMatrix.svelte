<script lang="ts">
  /**
   * Kill switch as a grid: pods down the side, servers across. Pick a row to
   * stop a pod everywhere, a column to stop a server, one square for one pod
   * on one server, or the corner for everything. Two strengths, gentlest
   * first. Each needs a second click to confirm.
   */
  import Server from "@lucide/svelte/icons/server";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { NODES, PODS, nodeById, podById } from "./demo";
  import {
    KILL_LABEL,
    cellFor,
    kill,
    scopeKey,
    type KillState,
  } from "./kill.svelte";

  let scope = $state<string>(scopeKey.all);
  let armed = $state<KillState | null>(null);
  $effect(() => {
    void scope;
    armed = null;
  });

  const STATE_TONE: Record<KillState, string> = {
    active: "text-success",
    "no-new": "text-warning",
    halted: "text-destructive",
  };
  const SIDE_TONE = { live: "var(--tone-live)", paper: "var(--tone-paper)" };

  const title = $derived.by(() => {
    const [kind, a, b] = scope.split(":");
    if (kind === "all") return "Everything: every pod on every server";
    if (kind === "node") {
      const n = nodeById(a)!;
      const here = PODS.filter((p) => cellFor(p, a).length).length;
      return `${n.name}: ${here} pods run here`;
    }
    if (kind === "pod") return `${podById(a)!.name}, on every server`;
    return `${podById(a)!.name} on ${nodeById(b)!.name}`;
  });

  const ACTIONS: {
    to: KillState;
    label: string;
    note: string;
    confirm: string;
    danger?: boolean;
  }[] = [
    {
      to: "no-new",
      label: "Stop new trades",
      note: "Open positions stay and can still exit",
      confirm: "Confirm: no new trades",
    },
    {
      to: "halted",
      label: "Close and halt",
      note: "Close every position, then stop the bots",
      confirm: "Confirm: close everything",
      danger: true,
    },
  ];

  function act(to: KillState, label: string) {
    if (armed !== to) {
      armed = to;
      return;
    }
    kill.set(scope, to);
    armed = null;
    workbench.notify(
      `${label} on ${title.split(":")[0]}. Demo only: the real switch goes to the trading node, is checked again the moment you click, and is journaled with your signature.`,
    );
  }
</script>

<div class="flex h-full flex-col">
  <p class="text-muted-foreground border-b px-3 py-2 text-xs">
    A row stops a pod everywhere, a column stops a server, a square stops one
    pod on one server, the corner stops everything.
  </p>
  <div class="min-h-0 flex-1 overflow-auto p-2">
    <div
      class="grid gap-1"
      style="grid-template-columns: minmax(8rem, 1fr) repeat({NODES.length}, minmax(7.5rem, 1fr))"
    >
      <button
        type="button"
        class={cn(
          "rounded-md border px-2 py-1.5 text-left text-sm font-medium",
          scope === scopeKey.all
            ? "border-primary bg-primary/12"
            : "hover:bg-muted",
        )}
        onclick={() => (scope = scopeKey.all)}
        >Everything
        <span
          class={cn(
            "block text-xs font-normal",
            STATE_TONE[kill.stateOf(scopeKey.all)],
          )}>{KILL_LABEL[kill.stateOf(scopeKey.all)]}</span
        ></button
      >
      {#each NODES as n (n.id)}
        {@const k = scopeKey.node(n.id)}
        <button
          type="button"
          class={cn(
            "rounded-md border px-2 py-1.5 text-left text-sm",
            scope === k ? "border-primary bg-primary/12" : "hover:bg-muted",
          )}
          onclick={() => (scope = k)}
        >
          <span class="flex items-center gap-1.5 font-medium"
            ><Server class="size-3.5" />{n.name}<span
              class={cn(
                "ml-auto size-1.5 rounded-full",
                n.status === "up" ? "bg-success" : "bg-warning",
              )}
              title={n.status}
            ></span></span
          >
          <span class={cn("block text-xs", STATE_TONE[kill.stateOf(k)])}
            >{KILL_LABEL[kill.stateOf(k)]}</span
          >
        </button>
      {/each}

      {#each PODS as p (p.id)}
        {@const pk = scopeKey.pod(p.id)}
        <button
          type="button"
          class={cn(
            "rounded-md border px-2 py-1.5 text-left text-sm",
            scope === pk ? "border-primary bg-primary/12" : "hover:bg-muted",
          )}
          onclick={() => (scope = pk)}
          ><span class="block truncate font-medium">{p.name}</span>
          <span class={cn("block text-xs", STATE_TONE[kill.stateOf(pk)])}
            >{KILL_LABEL[kill.stateOf(pk)]}</span
          ></button
        >
        {#each NODES as n (n.id)}
          {@const sides = cellFor(p, n.id)}
          {@const ck = scopeKey.cell(p.id, n.id)}
          {#if sides.length}
            {@const st = kill.effective(p.id, n.id)}
            <button
              type="button"
              class={cn(
                "rounded-md border px-2 py-1.5 text-left",
                scope === ck
                  ? "border-primary bg-primary/12"
                  : "bg-background/40 hover:bg-muted",
                st === "halted" && "opacity-60",
              )}
              onclick={() => (scope = ck)}
            >
              {#each sides as s (s.side)}
                <span
                  class="flex items-center gap-1.5 text-xs"
                  style="border-left: 2px solid {SIDE_TONE[
                    s.side
                  ]}; padding-left: 6px"
                  >{s.side === "live" ? "Live" : "Paper"}
                  <span class="text-muted-foreground"
                    >{s.bots} {s.bots === 1 ? "bot" : "bots"}</span
                  ></span
                >
              {/each}
              <span class={cn("mt-0.5 block text-xs", STATE_TONE[st])}
                >{KILL_LABEL[st]}</span
              >
            </button>
          {:else}
            <span
              class="text-muted-foreground/50 flex items-center justify-center rounded-md border border-dashed text-xs"
              >Not here</span
            >
          {/if}
        {/each}
      {/each}
    </div>
  </div>

  <div class="shrink-0 border-t px-3 py-2.5">
    <p class="text-sm font-medium">{title}</p>
    <p class={cn("text-xs", STATE_TONE[kill.stateOf(scope)])}>
      Now: {KILL_LABEL[kill.stateOf(scope)]}
    </p>
    <div class="mt-2 flex flex-wrap gap-2">
      {#each ACTIONS as a (a.to)}
        <Button
          size="sm"
          variant={armed === a.to
            ? "destructive"
            : a.danger
              ? "outline"
              : "secondary"}
          class={cn(a.danger && armed !== a.to && "text-destructive")}
          title={a.note}
          onclick={() => act(a.to, a.label)}
          >{armed === a.to ? a.confirm : a.label}</Button
        >
      {/each}
      {#if kill.stateOf(scope) !== "active"}
        <Button
          size="sm"
          variant="ghost"
          class="ml-auto"
          onclick={() => {
            kill.set(scope, "active");
            workbench.notify(
              `Resumed ${title.split(":")[0]}. Demo only; the real resume names its scope and is signed.`,
            );
          }}>Resume</Button
        >
      {/if}
    </div>
    {#if armed}
      <p class="text-muted-foreground mt-1.5 text-xs">
        {ACTIONS.find((a) => a.to === armed)?.note}. Click again to confirm.
      </p>
    {/if}
  </div>
</div>
