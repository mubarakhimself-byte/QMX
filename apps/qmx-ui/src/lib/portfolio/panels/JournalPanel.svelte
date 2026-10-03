<script lang="ts">
  /** The selected bot's trading journal: trades with their R, events that changed its behaviour, and your notes. */
  import ArrowLeftRight from "@lucide/svelte/icons/arrow-left-right";
  import Zap from "@lucide/svelte/icons/zap";
  import StickyNote from "@lucide/svelte/icons/sticky-note";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { CANDIDATES, JOURNAL, type JournalNote } from "../demo";
  import { portfolio } from "../portfolio.svelte";

  const c = $derived(
    CANDIDATES.find((x) => x.entity.id === portfolio.candidate) ??
      CANDIDATES[0],
  );
  let mine = $state<Record<string, JournalNote[]>>({});
  const notes = $derived([
    ...(mine[c.entity.id] ?? []),
    ...(JOURNAL[c.entity.id] ?? []),
  ]);
  let draft = $state("");
  const ICON = { trade: ArrowLeftRight, event: Zap, note: StickyNote };
  function add(e: SubmitEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    mine[c.entity.id] = [
      { time: "Now", kind: "note", text: `You: ${draft.trim()}` },
      ...(mine[c.entity.id] ?? []),
    ];
    draft = "";
  }
</script>

<div class="flex h-full flex-col">
  <ul class="min-h-0 flex-1 overflow-auto">
    {#each notes as n, i (i)}
      {@const Icon = ICON[n.kind]}
      <li class="flex gap-3 border-b border-border/50 px-4 py-2.5">
        <Icon
          class={cn(
            "mt-0.5 size-4 shrink-0",
            n.kind === "event" ? "text-warning" : "text-muted-foreground",
          )}
        />
        <div class="min-w-0 flex-1">
          <p class="text-sm">{n.text}</p>
          <p class="text-muted-foreground text-xs">{n.time}</p>
        </div>
        {#if n.r !== undefined}<span
            class={cn(
              "num self-center text-sm",
              n.r >= 0 ? "text-success" : "text-destructive",
            )}>{n.r > 0 ? "+" : ""}{n.r} R</span
          >{/if}
      </li>
    {:else}
      <li class="text-muted-foreground px-4 py-8 text-center text-sm">
        No journal entries yet for {c.entity.name}.
      </li>
    {/each}
  </ul>
  <form class="flex gap-2 border-t p-2" onsubmit={add}>
    <input
      bind:value={draft}
      placeholder={`Note on ${c.entity.name}…`}
      aria-label="Journal note"
      class="bg-background/40 h-8 flex-1 rounded-md border px-2.5 text-sm"
    />
    <Button type="submit" size="sm" disabled={!draft.trim()}>Add note</Button>
  </form>
</div>
