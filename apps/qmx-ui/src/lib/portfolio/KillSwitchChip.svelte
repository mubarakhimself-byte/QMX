<script lang="ts">
  /**
   * The kill switch lives in the Portfolio header, always visible
   * (operator, 2026-10-03): the worst level across accounts at a glance;
   * open it for every account's level and your powers.
   */
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { ACCOUNTS, type Ksa } from "./demo";
  import { KSA_TONE } from "./bits";
  import ControlPanel from "./panels/ControlPanel.svelte";

  const ORDER: Ksa[] = ["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"];
  const trading = ACCOUNTS.filter((a) => a.role !== "watch");
  const worst = ORDER[Math.max(...trading.map((a) => ORDER.indexOf(a.ksa)))];
  const raised = trading.filter((a) => a.ksa !== "GREEN");
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger
    class={cn(
      "flex h-8 items-center gap-2 rounded-md border px-2.5 text-sm font-medium",
      worst !== "GREEN" && "border-warning/60 bg-warning/10",
    )}
    aria-label={`Kill switch: ${worst}`}
  >
    <ShieldAlert class="size-4" />
    <span class={cn("size-2.5 rounded-full", KSA_TONE[worst])}></span>
    {worst}
    {#if raised.length}<span class="text-muted-foreground text-xs font-normal"
        >{raised.map((a) => a.name).join(", ")}</span
      >{/if}
    <ChevronDown class="size-3.5" />
  </DropdownMenu.Trigger>
  <DropdownMenu.Content align="center" class="h-[30rem] w-[30rem] p-0">
    <ControlPanel />
  </DropdownMenu.Content>
</DropdownMenu.Root>
