<script lang="ts">
  /**
   * The kill switch lives in the Portfolio header, always visible
   * (operator, 2026-10-03). The chip shows the worst exchange-account level
   * and how many pods or servers you have stopped. Open it to stop by pod
   * and server (the grid), or to see each exchange account's level.
   */
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { ACCOUNTS, type Ksa } from "./demo";
  import { KSA_TONE } from "./bits";
  import { kill } from "./kill.svelte";
  import KillMatrix from "./KillMatrix.svelte";
  import ControlPanel from "./panels/ControlPanel.svelte";

  const ORDER: Ksa[] = ["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"];
  const trading = ACCOUNTS.filter((a) => a.role !== "watch");
  const worst = ORDER[Math.max(...trading.map((a) => ORDER.indexOf(a.ksa)))];
  const raised = trading.filter((a) => a.ksa !== "GREEN");
  const TABS = [
    { id: "grid", label: "Pods and servers" },
    { id: "accounts", label: "Exchange accounts" },
  ] as const;
  let tab = $state<(typeof TABS)[number]["id"]>("grid");
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger
    class={cn(
      "flex h-8 items-center gap-2 rounded-md border px-2.5 text-sm font-medium",
      kill.worst === "halted"
        ? "border-destructive/60 bg-destructive/10"
        : (worst !== "GREEN" || kill.raised) &&
            "border-warning/60 bg-warning/10",
    )}
    aria-label={`Kill switch: ${worst}${kill.raised ? `, ${kill.raised} stopped` : ""}`}
  >
    <ShieldAlert class="size-4" />
    <span class={cn("size-2.5 rounded-full", KSA_TONE[worst])}></span>
    {worst}
    {#if raised.length}<span
        class="text-muted-foreground hidden max-w-28 truncate text-xs font-normal 2xl:inline"
        >{raised.map((a) => a.name).join(", ")}</span
      >{/if}
    {#if kill.raised}<span
        class={cn(
          "rounded px-1.5 text-xs whitespace-nowrap",
          kill.worst === "halted"
            ? "bg-destructive/15 text-destructive"
            : "bg-warning/15 text-warning",
        )}
        title="Pods or servers you have stopped">{kill.raised} stopped</span
      >{/if}
    <ChevronDown class="size-3.5" />
  </DropdownMenu.Trigger>
  <DropdownMenu.Content
    align="center"
    class="flex h-[32rem] w-[min(44rem,calc(100vw-2rem))] flex-col p-0"
  >
    <div class="flex h-10 shrink-0 items-center gap-1 border-b px-2">
      {#each TABS as t (t.id)}
        <button
          type="button"
          class={cn(
            "h-7 rounded-md px-2.5 text-sm",
            tab === t.id
              ? "bg-muted font-medium"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-pressed={tab === t.id}
          onclick={() => (tab = t.id)}>{t.label}</button
        >
      {/each}
    </div>
    <div class="min-h-0 flex-1">
      {#if tab === "grid"}<KillMatrix />{:else}<ControlPanel />{/if}
    </div>
  </DropdownMenu.Content>
</DropdownMenu.Root>
