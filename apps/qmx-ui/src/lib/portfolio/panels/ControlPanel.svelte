<script lang="ts">
  /**
   * Kill switch and your powers. Levels only rise on their own; coming back
   * down is your Resume, naming the scope. Every power is checked again
   * against live state when you click, and journaled with your signature.
   * Shows what was requested apart from what the trading server enforces.
   */
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS } from "../demo";
  import { KSA_EFFECT, KSA_TONE } from "../bits";

  const LEVELS = ["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"] as const;
  let scope = $state("by-spot");
  const acct = $derived(ACCOUNTS.find((a) => a.id === scope)!);
  const POWERS = [
    {
      id: "resume",
      label: "Resume",
      note: "Bring this scope back down a level",
    },
    { id: "escalate", label: "Escalate", note: "Raise the level by hand" },
    {
      id: "flatten",
      label: "Flatten",
      note: "Close every position in this scope",
      danger: true,
    },
    {
      id: "paper",
      label: "Move to paper",
      note: "Route this account's pods to their demo pair",
    },
    {
      id: "reset",
      label: "Reset paper",
      note: "New paper balance, old one kept on record",
    },
    {
      id: "unknown",
      label: "Resolve unknown",
      note: "Attest what the broker really holds",
    },
  ];
  function power(p: (typeof POWERS)[number]) {
    workbench.notify(
      `${p.label} on ${acct.name}: needs the trading server. You'd sign it, it's rechecked at the moment you click, then journaled.`,
    );
  }
</script>

<div class="flex h-full flex-col overflow-auto">
  <div class="flex h-9 shrink-0 items-center gap-2 border-b px-3 text-xs">
    <span class="text-muted-foreground">Scope</span>
    <select bind:value={scope} class="h-7 rounded-md border px-2 text-xs">
      <option value="global">Everything</option>
      {#each ACCOUNTS.filter((a) => a.role !== "watch") as a (a.id)}<option
          value={a.id}>{a.name}</option
        >{/each}
    </select>
  </div>
  <ol class="grid gap-0.5 px-2 py-2">
    {#each LEVELS as l (l)}
      <li
        class={cn(
          "flex items-center gap-3 rounded-md px-2 py-1.5",
          (scope === "global" ? "GREEN" : acct.ksa) === l && "bg-muted",
        )}
      >
        <span class={cn("size-2.5 rounded-full", KSA_TONE[l])}></span>
        <span class="num w-16 text-sm font-semibold">{l}</span>
        <span class="text-muted-foreground text-sm">{KSA_EFFECT[l]}</span>
        {#if (scope === "global" ? "GREEN" : acct.ksa) === l}<span
            class="ml-auto text-xs">now</span
          >{/if}
      </li>
    {/each}
  </ol>
  {#if scope !== "global" && acct.ksa !== "GREEN"}
    <div class="bg-warning/10 mx-2 rounded-md px-3 py-2 text-xs">
      <p>
        <span class="font-medium">Requested:</span> YELLOW by the volatility guard
        at 11:42.
      </p>
      <p>
        <span class="font-medium">Enforced:</span> YELLOW on the Tokyo server since
        11:42:03 (source: server, received 11:42:04).
      </p>
    </div>
  {/if}
  <div class="grid grid-cols-2 gap-1.5 p-2">
    {#each POWERS as p (p.id)}
      <Button
        size="sm"
        variant={p.danger ? "destructive" : "outline"}
        class="h-auto flex-col items-start gap-0 py-1.5 text-left"
        onclick={() => power(p)}
      >
        <span class="flex items-center gap-1.5"
          >{#if p.danger}<ShieldAlert class="size-3.5" />{/if}{p.label}</span
        >
        <span class="text-xs font-normal opacity-75">{p.note}</span>
      </Button>
    {/each}
  </div>
  <p class="text-muted-foreground mt-auto border-t px-3 py-2 text-xs">
    Agents and the copilot never use these. You can build your own kill switch
    as a workflow in the Lab and attach it to a pod.
  </p>
</div>
