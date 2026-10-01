<script lang="ts">
  import Plus from "@lucide/svelte/icons/plus";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import AtSign from "@lucide/svelte/icons/at-sign";
  import { Button } from "$lib/components/ui/button";
  import { workbench } from "./workbench.svelte";

  let {
    placeholder = "Ask the copilot…",
    label = "Message",
  }: { placeholder?: string; label?: string } = $props();

  let draft = $state("");
  // Send goes through dispatchChat once a transport is bound; never faked.
  const canSend = $derived(workbench.connection === "connected");
  const reason = "Sending needs a connection to the QMX daemon.";
</script>

<form
  class="bg-card ring-foreground/10 focus-within:ring-ring/40 flex flex-col gap-1 rounded-2xl p-2 ring-1"
  onsubmit={(e) => e.preventDefault()}
>
  <label class="sr-only" for="composer-input">{label}</label>
  <textarea
    id="composer-input"
    bind:value={draft}
    rows="2"
    {placeholder}
    class="placeholder:text-muted-foreground max-h-48 min-h-12 resize-none bg-transparent px-2 py-1 text-sm outline-none"
  ></textarea>
  <div class="flex items-center gap-1">
    <Button variant="ghost" size="icon-sm" aria-label="Add content" disabled>
      <Plus />
    </Button>
    <Button
      variant="ghost"
      size="sm"
      class="text-muted-foreground"
      aria-label="Choose target"
      disabled
    >
      <AtSign /> No target
    </Button>
    <Button
      type="submit"
      size="icon-sm"
      class="ml-auto"
      aria-label="Send"
      disabled={!canSend || !draft.trim()}
    >
      <ArrowUp />
    </Button>
  </div>
  {#if !canSend}
    <p class="text-muted-foreground px-2 text-xs">{reason}</p>
  {/if}
</form>
