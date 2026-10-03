<script lang="ts">
  /**
   * Agents working on the Lab's subject and their sub-agents (QMA: Quant →
   * Agent → Subagent), each with its state and where it runs. Collapsing a
   * swarm keeps a count. Agents never place orders or size trades.
   */
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Bot from "@lucide/svelte/icons/bot";
  import { cn } from "$lib/utils";
  import EnvChip from "../EnvChip.svelte";
  import StatusDot from "../StatusDot.svelte";
  import { AGENTS } from "../demo";
  import { lab } from "../lab.svelte";
  const shown = $derived(
    lab.machine
      ? AGENTS.map((a) => ({
          ...a,
          children: (a.children ?? []).filter((c) => c.env === lab.machine),
        })).filter((a) => a.env === lab.machine || a.children.length)
      : AGENTS,
  );

  let open = $state<string[]>(AGENTS.map((a) => a.id));
  const toggle = (id: string) =>
    (open = open.includes(id) ? open.filter((o) => o !== id) : [...open, id]);
</script>

<div class="flex h-full flex-col">
  <ul class="min-h-0 flex-1 overflow-auto py-1">
    {#each shown as a (a.id)}
      {@const kids = a.children ?? []}
      <li>
        <div class="hover:bg-muted/40 flex items-start gap-2 px-3 py-2">
          <button
            type="button"
            class="hover:bg-muted mt-0.5 rounded"
            aria-expanded={open.includes(a.id)}
            aria-label={`${open.includes(a.id) ? "Collapse" : "Expand"} ${a.name}'s sub-agents`}
            onclick={() => toggle(a.id)}
          >
            <ChevronRight
              class={cn(
                "size-4 transition-transform",
                open.includes(a.id) && "rotate-90",
              )}
            />
          </button>
          <Bot class="text-muted-foreground mt-0.5 size-4 shrink-0" />
          <div class="min-w-0 flex-1">
            <p class="text-sm">
              <span class="font-medium">{a.name}</span>
              <span class="text-muted-foreground text-xs">{a.role}</span>
            </p>
            <p class="text-muted-foreground truncate text-xs">{a.task}</p>
          </div>
          <div class="flex shrink-0 flex-col items-end gap-1">
            <StatusDot status={a.status} />
            <EnvChip env={a.env} status={a.status} compact />
          </div>
        </div>
        {#if open.includes(a.id)}
          <ul class="border-border/60 ml-6 border-l">
            {#each kids as s (s.id)}
              <li class="flex items-center gap-2 py-1.5 pr-3 pl-4">
                <span class="min-w-0 flex-1">
                  <span class="text-sm">{s.name}</span>
                  <span class="text-muted-foreground block truncate text-xs"
                    >{s.task}</span
                  >
                </span>
                <StatusDot status={s.status} />
                <EnvChip env={s.env} status={s.status} compact />
              </li>
            {/each}
          </ul>
        {:else if kids.length}
          <p class="text-muted-foreground ml-12 pb-1 text-xs">
            {kids.length} sub-agents · {kids.filter(
              (k) => k.status === "running",
            ).length} running
          </p>
        {/if}
      </li>
    {/each}
  </ul>
  <p class="text-muted-foreground border-t px-3 py-2 text-xs">
    Unknown means contact was lost; it is not a failure. Agents never place
    orders or size trades.
  </p>
</div>
