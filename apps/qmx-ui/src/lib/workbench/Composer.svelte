<script lang="ts">
  import Paperclip from "@lucide/svelte/icons/paperclip";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import AtSign from "@lucide/svelte/icons/at-sign";
  import Wrench from "@lucide/svelte/icons/wrench";
  import WifiOff from "@lucide/svelte/icons/wifi-off";
  import X from "@lucide/svelte/icons/x";
  import LayoutPanelTop from "@lucide/svelte/icons/layout-panel-top";
  import { Button } from "$lib/components/ui/button";
  import { workbench } from "./workbench.svelte";

  let {
    placeholder = "Ask the copilot…",
    label = "Message",
    refs = [],
    onremoveref,
  }: {
    placeholder?: string;
    label?: string;
    /** Context chips added from widgets (message-only, not durable refs). */
    refs?: string[];
    onremoveref?: (ref: string) => void;
  } = $props();

  let draft = $state("");
  // Send goes through dispatchChat once a transport is bound; never faked.
  const online = $derived(workbench.connection === "connected");
  const chip =
    "text-muted-foreground hover:text-foreground hover:bg-muted flex h-6 items-center gap-1 rounded-sm px-1.5 text-xs disabled:pointer-events-none disabled:opacity-50";
</script>

<form
  class="bg-panel focus-within:border-ring/50 flex flex-col rounded-md border"
  onsubmit={(e) => e.preventDefault()}
>
  {#if refs.length}
    <ul class="flex flex-wrap gap-1 px-2 pt-2" aria-label="Context">
      {#each refs as ref (ref)}
        <li
          class="bg-muted flex h-6 items-center gap-1 rounded-sm pr-0.5 pl-1.5 text-xs"
        >
          <LayoutPanelTop class="text-muted-foreground size-3" />
          {ref}
          <button
            type="button"
            class="hover:bg-background/50 rounded-sm p-0.5"
            aria-label={`Remove ${ref}`}
            onclick={() => onremoveref?.(ref)}
          >
            <X class="size-3" />
          </button>
        </li>
      {/each}
    </ul>
  {/if}
  <label class="sr-only" for="composer-input">{label}</label>
  <textarea
    id="composer-input"
    bind:value={draft}
    rows="2"
    {placeholder}
    class="placeholder:text-muted-foreground max-h-48 min-h-10 resize-none bg-transparent px-3 pt-2.5 text-sm outline-none"
  ></textarea>
  <div class="flex items-center gap-0.5 px-1.5 pb-1.5">
    <button type="button" class={chip} disabled aria-label="Attach content">
      <Paperclip class="size-3.5" /> Attach
    </button>
    <button type="button" class={chip} disabled aria-label="Choose target">
      <AtSign class="size-3.5" /> Target
    </button>
    <button type="button" class={chip} disabled aria-label="Choose tools">
      <Wrench class="size-3.5" /> Tools
    </button>
    {#if !online}
      <span
        class="text-muted-foreground ml-auto flex items-center gap-1 text-[11px]"
        title="Sending needs a connection to the QMX daemon."
      >
        <WifiOff class="size-3" /> Offline
      </span>
    {/if}
    <Button
      type="submit"
      size="icon-xs"
      class={online ? "ml-auto" : "ml-1.5"}
      aria-label={online ? "Send" : "Send (offline)"}
      disabled={!online || !draft.trim()}
    >
      <ArrowUp />
    </Button>
  </div>
</form>
