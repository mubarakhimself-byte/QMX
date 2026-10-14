<script lang="ts">
  /**
   * Where models plug in. Four default slots, and the operator can add more.
   * Only "entry signal" exists in the docs today (inside the bot's code,
   * DEC-0172); sizing, regime and throttle are owned elsewhere now (the pod,
   * the servers' labelers, the kill switch) and are marked new scope.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Plug from "@lucide/svelte/icons/plug";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ASSETS, SLOTS } from "../demo";

  const models = ASSETS.filter((a) => a.kind === "model");
  let filled = $state<Record<string, string | null>>(
    Object.fromEntries(SLOTS.map((s) => [s.id, s.model])),
  );
</script>

<div class="flex h-full flex-col">
  <div class="min-h-0 flex-1 overflow-auto p-3">
    <ul
      class="grid gap-2 [grid-template-columns:repeat(auto-fill,minmax(14rem,1fr))]"
    >
      {#each SLOTS as s (s.id)}
        <li class="rounded-lg border p-3">
          <div class="flex items-center gap-2">
            <Plug class="text-muted-foreground size-4" />
            <span class="text-sm font-medium">{s.label}</span>
            {#if s.scope === "new"}<Badge
                variant="outline"
                class="ml-auto text-xs">New scope</Badge
              >{/if}
          </div>
          <p class="text-muted-foreground mt-1 text-xs">{s.owner}</p>
          <DropdownMenu.Root>
            <DropdownMenu.Trigger>
              {#snippet child({ props })}
                <button
                  {...props}
                  type="button"
                  class="hover:border-ring mt-2 flex h-8 w-full items-center rounded-md border border-dashed px-2 text-left text-sm"
                >
                  {#if filled[s.id]}{filled[s.id]}{:else}<span
                      class="text-muted-foreground"
                      >Default rules (no model)</span
                    >{/if}
                </button>
              {/snippet}
            </DropdownMenu.Trigger>
            <DropdownMenu.Content class="w-56">
              <DropdownMenu.Item onclick={() => (filled[s.id] = null)}
                >Default rules (no model)</DropdownMenu.Item
              >
              <DropdownMenu.Separator />
              {#each models as m (m.id)}
                <DropdownMenu.Item onclick={() => (filled[s.id] = m.name)}
                  >{m.name}</DropdownMenu.Item
                >
              {/each}
              <DropdownMenu.Separator />
              <DropdownMenu.Item
                onclick={() =>
                  workbench.notify("Importing a model needs the daemon.")}
                >Import a model…</DropdownMenu.Item
              >
            </DropdownMenu.Content>
          </DropdownMenu.Root>
        </li>
      {/each}
      <li>
        <Button
          variant="outline"
          class="h-full min-h-24 w-full border-dashed"
          onclick={() =>
            workbench.notify(
              "Name the new slot and what it feeds; the Lab copilot can scaffold it.",
            )}><Plus />Add a slot</Button
        >
      </li>
    </ul>
  </div>
  <p class="text-muted-foreground border-t px-3 py-2 text-xs">
    A model in a slot changes the bot. Plugging one in makes a new bot version
    that needs fresh evidence.
  </p>
</div>
