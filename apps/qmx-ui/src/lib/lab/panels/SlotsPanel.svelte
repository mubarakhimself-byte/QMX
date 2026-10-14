<script lang="ts">
  /**
   * Where models plug in. Four default slots, and the operator can add more.
   * Only "entry signal" exists in the docs today (inside the bot's code,
   * DEC-0172); sizing, regime and throttle are owned elsewhere now (the pod,
   * the servers' labelers, the kill switch) and are marked new scope.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Plug from "@lucide/svelte/icons/plug";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { lab } from "../lab.svelte";
  import { ASSETS, SLOTS } from "../demo";

  const size = panelSize();
  const models = ASSETS.filter((a) => a.kind === "model");
  let filled = $state<Record<string, string | null>>(
    Object.fromEntries(SLOTS.map((s) => [s.id, s.model])),
  );
</script>

{#snippet picker(id: string, label: string)}
  <DropdownMenu.Root>
    <DropdownMenu.Trigger>
      {#snippet child({ props })}
        <button
          {...props}
          type="button"
          class="hover:border-ring flex h-8 w-full min-w-0 items-center rounded-md border border-dashed px-2 text-left text-sm"
          aria-label={`Model in ${label}`}
        >
          <span class="truncate"
            >{#if filled[id]}{filled[id]}{:else}<span
                class="text-muted-foreground">Default rules</span
              >{/if}</span
          >
        </button>
      {/snippet}
    </DropdownMenu.Trigger>
    <DropdownMenu.Content class="w-56">
      <DropdownMenu.Item onclick={() => (filled[id] = null)}
        >Default rules (no model)</DropdownMenu.Item
      >
      <DropdownMenu.Separator />
      {#each models as m (m.id)}
        <DropdownMenu.Item onclick={() => (filled[id] = m.name)}
          >{m.name}</DropdownMenu.Item
        >
      {/each}
      <DropdownMenu.Separator />
      <DropdownMenu.Item
        onclick={() => workbench.notify("Importing a model needs the daemon.")}
        >Import a model…</DropdownMenu.Item
      >
    </DropdownMenu.Content>
  </DropdownMenu.Root>
{/snippet}

{#if size.mode === "compact"}
  <div class="p-panel gap-row flex h-full flex-col">
    <p class="num text-2xl font-semibold">
      {Object.values(filled).filter(Boolean).length} / {SLOTS.length}
    </p>
    <p class="text-muted-foreground text-xs">slots with a model</p>
    <ul class="mt-auto flex flex-col text-xs">
      {#each SLOTS as s (s.id)}
        <li class="flex min-w-0 items-center gap-2">
          <span
            class="size-1.5 shrink-0 rounded-full {filled[s.id]
              ? 'bg-success'
              : 'bg-muted-foreground/50'}"
          ></span>
          <span class="truncate">{s.label}</span>
        </li>
      {/each}
    </ul>
  </div>
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2 text-xs">
      <span class="text-muted-foreground"
        >{Object.values(filled).filter(Boolean).length} of {SLOTS.length} with a model</span
      >
      <InfoTip
        label="Explain model slots"
        text="A slot is a decision inside a bot that a trained model can make, such as when to enter or how big to trade. Leave it on Default rules and the bot decides the usual way. Put a model in and the bot becomes a new version that has to be tested again before it trades."
      />
      <Button
        size="sm"
        variant="ghost"
        class="ml-auto h-7"
        onclick={() => lab.ask("Add a model slot to the bot that decides ")}
        ><Plus />Slot</Button
      >
    </div>
    <ul class="min-h-0 flex-1 overflow-auto">
      {#each SLOTS as s (s.id)}
        <li
          class="px-panel py-row grid grid-cols-[minmax(0,1fr)_minmax(0,14rem)] items-center gap-3 border-t"
        >
          <span class="flex min-w-0 items-center gap-2">
            <Plug class="text-muted-foreground size-4 shrink-0" />
            <span class="min-w-0">
              <span class="block truncate text-sm">{s.label}</span>
              {#if size.mode === "expanded"}<span
                  class="text-muted-foreground block truncate text-xs"
                  >{s.owner}{s.scope === "new" ? " · new" : ""}</span
                >{/if}
            </span>
          </span>
          {@render picker(s.id, s.label)}
        </li>
      {/each}
    </ul>
  </div>
{/if}
