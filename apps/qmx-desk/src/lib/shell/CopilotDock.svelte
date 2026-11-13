<script lang="ts">
  import { shell } from "./state.svelte";
  import Icon from "$lib/qmx/Icon.svelte";
  import IconButton from "$lib/qmx/IconButton.svelte";

  // The copilot beside any place. Panels you send land here as context.
  let draft = $state("");
  let said = $state<string[]>([]);
  const ask = () => {
    if (!draft.trim()) return;
    said.push(draft.trim());
    draft = "";
  };
</script>

<aside class="border-border flex w-[clamp(18rem,28%,24rem)] shrink-0 flex-col border-l" aria-label="Copilot">
  <header class="flex h-12 shrink-0 items-center gap-2 pr-1.5 pl-3">
    <Icon name="sparkles" />
    <h2 class="flex-1 font-medium">Copilot</h2>
    <IconButton icon="expand" label="Open your sessions" size="size-7" onclick={() => shell.go("sessions")} />
    <IconButton icon="x" label="Close the copilot" size="size-7" onclick={() => shell.toggleDock(false)} />
  </header>
  <div class="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-3 py-2">
    {#if said.length === 0}
      <div class="text-muted-foreground my-auto text-center">
        <p class="text-foreground display text-xl font-semibold">Ask for anything in {shell.current.name}</p>
        <p class="mt-1.5 text-sm text-pretty">It sees the place you are in and whatever you send it.</p>
      </div>
    {/if}
    {#each said as s, i (i)}
      <p class="bg-accent ml-8 self-end rounded-lg px-3 py-2 [overflow-wrap:anywhere]">{s}</p>
      <p class="text-muted-foreground flex items-center gap-2 text-sm">
        <span class="dot text-run size-1.5"></span> Demo: no model is connected in this design build.
      </p>
    {/each}
  </div>
  <div class="p-3">
    {#if shell.sent.length}
      <div class="mb-2 flex flex-wrap gap-1.5">
        {#each shell.sent as s (s)}
          <span class="well bg-panel flex max-w-full items-center gap-1 py-1 pr-1 pl-2 text-sm">
            <span class="truncate" title={s}>{s}</span>
            <button class="grid size-5 shrink-0 place-items-center rounded opacity-60 hover:opacity-100" aria-label="Remove {s}" onclick={() => shell.unsend(s)}>
              <Icon name="x" class="size-3" />
            </button>
          </span>
        {/each}
      </div>
    {/if}
    <form class="well bg-panel flex flex-col gap-2 p-2" onsubmit={(e) => (e.preventDefault(), ask())}>
      <textarea
        bind:value={draft}
        rows="2"
        placeholder="Say what you want done"
        class="placeholder:text-muted-foreground w-full resize-none bg-transparent px-1 outline-none"
        onkeydown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), ask())}
      ></textarea>
      <div class="flex items-center gap-2">
        <button type="button" class="press h-7 gap-1.5 px-2 text-sm"><Icon name="sparkles" class="size-3.5" />Opus 5.5<Icon name="chevron-down" class="size-3" /></button>
        <span class="text-muted-foreground flex items-center gap-1.5 text-sm"><Icon name="laptop" class="size-3.5" />This PC</span>
        <span class="flex-1"></span>
        <button class="bg-primary text-primary-foreground grid size-8 place-items-center rounded-md transition-transform duration-150 active:scale-[0.97]" aria-label="Send">
          <Icon name="arrow-up" />
        </button>
      </div>
    </form>
  </div>
</aside>
