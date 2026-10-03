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
  import Composer from "./Composer.svelte";
  import { resolve } from "$app/paths";
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
    starters = [],
    seed = "",
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
    /** A few things this copilot is good at, offered on an empty session. */
    starters?: string[];
    /** Text the surface drafts into the composer (e.g. from a "+ Scenario" menu). */
    seed?: string;
  } = $props();
  let draftSeed = $state("");
  $effect(() => {
    if (seed) draftSeed = seed;
  });

  // svelte-ignore state_referenced_locally
  let list = $state<Session[]>([...sessions]);
  let current = $state<string | null>(null);
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
        variant="ghost"
        size="icon-xs"
        aria-label={`${title} settings`}
        title="Model, tools and instructions for this copilot"
        href={`${resolve("/settings")}?tab=models`}><Settings2 /></Button
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
  <div class="flex min-h-0 flex-1 flex-col justify-end overflow-auto p-3">
    {#if active}
      <p class="text-muted-foreground text-sm">
        {active.title}: messages load from the daemon once it is connected.
      </p>
    {:else}
      {#if hint}<p class="text-muted-foreground mb-3 text-sm">{hint}</p>{/if}
      {#if starters.length}
        <ul class="flex flex-col gap-1.5" aria-label="Suggestions">
          {#each starters as st (st)}
            <li>
              <button
                type="button"
                class="hover:bg-muted hover:border-ring/40 w-full rounded-lg border px-3 py-2 text-left text-sm"
                onclick={() => (draftSeed = st)}>{st}</button
              >
            </li>
          {/each}
        </ul>
      {/if}
    {/if}
  </div>
  <div class="p-2">
    <Composer
      {placeholder}
      label={`${title} message`}
      {refs}
      {onremoveref}
      {context}
      seed={draftSeed}
    />
  </div>
</aside>
