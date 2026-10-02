<script lang="ts">
  /**
   * Right-hand copilot column for a surface (the Lab, a mini app). Each has
   * its own sessions with history (switch, start new), its own settings
   * (instructions, default model) and its own tools, targets and attach
   * sources via `context`. History is stored by the daemon once wired.
   */
  import X from "@lucide/svelte/icons/x";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Plus from "@lucide/svelte/icons/plus";
  import History from "@lucide/svelte/icons/history";
  import Settings2 from "@lucide/svelte/icons/settings-2";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import EmptyState from "./EmptyState.svelte";
  import Composer from "./Composer.svelte";
  import { MODELS, workbench } from "./workbench.svelte";
  import type { CopilotContext } from "./copilot-context";

  type Session = { id: string; title: string; when: string };

  let {
    title = "Copilot",
    profile,
    hint,
    placeholder,
    onclose,
    refs = [],
    onremoveref,
    context,
    sessions = [],
  }: {
    title?: string;
    profile?: string;
    hint?: string;
    placeholder?: string;
    onclose?: () => void;
    refs?: string[];
    onremoveref?: (ref: string) => void;
    context?: CopilotContext;
    sessions?: Session[];
  } = $props();

  // svelte-ignore state_referenced_locally
  let list = $state<Session[]>([...sessions]);
  let current = $state<string | null>(null);
  let showSettings = $state(false);
  let instructions = $state("");
  let modelId = $state(workbench.modelDefaults.app ?? "sonnet");
  const active = $derived(list.find((s) => s.id === current));

  function newSession() {
    const s = {
      id: `n-${Date.now().toString(36)}`,
      title: "New session",
      when: "Now",
    };
    list = [s, ...list];
    current = s.id;
  }
</script>

<aside aria-label={title} class="bg-panel flex h-full flex-col border-l">
  <header class="flex h-9 shrink-0 items-center gap-1 border-b pr-1 pl-3">
    <Sparkles class="text-muted-foreground size-3.5 shrink-0" />
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        class="hover:bg-muted flex h-7 min-w-0 items-center gap-1 rounded-md px-1.5 text-sm font-medium"
        aria-label="Sessions"
      >
        <span class="truncate">{active?.title ?? title}</span>
        <ChevronDown class="size-3.5 shrink-0" />
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="start" class="w-72">
        <DropdownMenu.Item onclick={newSession}
          ><Plus />New session</DropdownMenu.Item
        >
        <DropdownMenu.Separator />
        <DropdownMenu.Label class="text-muted-foreground text-xs font-normal"
          >History</DropdownMenu.Label
        >
        {#each list as s (s.id)}
          <DropdownMenu.Item onclick={() => (current = s.id)}>
            <History />
            <span class="min-w-0 flex-1 truncate">{s.title}</span>
            <span class="text-muted-foreground text-xs">{s.when}</span>
          </DropdownMenu.Item>
        {:else}
          <DropdownMenu.Label class="text-muted-foreground text-xs font-normal"
            >No earlier sessions</DropdownMenu.Label
          >
        {/each}
      </DropdownMenu.Content>
    </DropdownMenu.Root>
    {#if profile}<Badge
        variant="outline"
        class="h-4 shrink-0 px-1.5 text-[10px]">{profile}</Badge
      >{/if}
    <div class="ml-auto flex shrink-0 items-center">
      <Button
        variant="ghost"
        size="icon-xs"
        aria-label="New session"
        onclick={newSession}><Plus /></Button
      >
      <Button
        variant={showSettings ? "secondary" : "ghost"}
        size="icon-xs"
        aria-label={`${title} settings`}
        aria-pressed={showSettings}
        onclick={() => (showSettings = !showSettings)}><Settings2 /></Button
      >
      {#if onclose}
        <Button
          variant="ghost"
          size="icon-xs"
          aria-label="Close copilot"
          onclick={onclose}><X /></Button
        >
      {/if}
    </div>
  </header>
  {#if showSettings}
    <div class="flex shrink-0 flex-col gap-2 border-b p-3 text-sm">
      <label class="flex flex-col gap-1">
        <span class="text-muted-foreground text-xs"
          >Standing instructions for this copilot</span
        >
        <textarea
          bind:value={instructions}
          rows={3}
          class="bg-background/40 rounded-md border px-2 py-1.5 text-sm"
          placeholder="Prefer walk-forward over single backtests."
        ></textarea>
      </label>
      <label class="flex items-center justify-between gap-2">
        <span class="text-muted-foreground text-xs">Default model</span>
        <select
          bind:value={modelId}
          class="bg-background/40 h-8 rounded-md border px-2 text-sm"
        >
          {#each MODELS as m (m.id)}<option value={m.id}>{m.label}</option
            >{/each}
        </select>
      </label>
      <p class="text-muted-foreground text-xs">
        Saved per copilot once the daemon is connected.
      </p>
    </div>
  {/if}
  <div class="min-h-0 flex-1 overflow-auto">
    <EmptyState
      class="h-full"
      title={active ? active.title : "No messages yet"}
      description={active
        ? "This session's messages load from the daemon once it is connected."
        : hint}
    />
  </div>
  <div class="p-2">
    <Composer
      {placeholder}
      label={`${title} message`}
      {refs}
      {onremoveref}
      {context}
    />
  </div>
</aside>
