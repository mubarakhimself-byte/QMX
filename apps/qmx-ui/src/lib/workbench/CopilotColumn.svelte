<script lang="ts">
  import X from "@lucide/svelte/icons/x";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import EmptyState from "./EmptyState.svelte";
  import Composer from "./Composer.svelte";

  /** Right-hand copilot column (OpenBB reference). History is per surface. */
  let {
    title = "Copilot",
    profile,
    hint,
    placeholder,
    onclose,
  }: {
    title?: string;
    profile?: string;
    hint?: string;
    placeholder?: string;
    onclose?: () => void;
  } = $props();
</script>

<aside aria-label={title} class="bg-panel flex h-full flex-col border-l">
  <header class="flex h-9 shrink-0 items-center gap-2 border-b pr-1 pl-3">
    <Sparkles class="text-muted-foreground size-3.5" />
    <span class="text-sm font-medium">{title}</span>
    {#if profile}<Badge variant="outline" class="h-4 px-1.5 text-[10px]"
        >{profile}</Badge
      >{/if}
    {#if onclose}
      <Button
        variant="ghost"
        size="icon-xs"
        class="ml-auto"
        aria-label="Close copilot"
        onclick={onclose}
      >
        <X />
      </Button>
    {/if}
  </header>
  <div class="min-h-0 flex-1 overflow-auto">
    <EmptyState class="h-full" title="No messages yet" description={hint} />
  </div>
  <div class="p-2"><Composer {placeholder} label={`${title} message`} /></div>
</aside>
