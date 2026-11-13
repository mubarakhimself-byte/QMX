<script lang="ts">
  import { shell } from "./state.svelte";
  import Icon from "$lib/qmx/Icon.svelte";
  import { things } from "./things.svelte";
  import { kindName } from "./model";

  // One field that reaches every place, every action and the copilot.
  // Opened from the keyboard many times a day, so it never animates.
  let { primary = false }: { primary?: boolean } = $props();
  let q = $state("");
  let open = $state(false);
  let active = $state(0);
  let input: HTMLInputElement | undefined = $state();

  type Item = { icon: string; label: string; hint: string; run: () => void };
  const actions: [string, string, () => void][] = [
    ["plus", "New session with the copilot", () => shell.toggleDock(true)],
    ["workflow", "Build a workflow from a template", () => shell.go("workflows")],
    ["server", "Start a trading node on This PC", () => shell.go("trading")],
    ["key-round", "Connect an AI provider", () => shell.go("usage")],
  ];
  const icon: Record<string, string> = { unit: "candlestick", proposal: "inbox", session: "message-square", run: "loader", workflow: "workflow", node: "server", app: "puzzle" };
  const items = $derived.by(() => {
    const all: Item[] = [
      ...shell.places.map((p) => ({ icon: p.icon, label: p.name, hint: "Go to", run: () => shell.go(p.id) })),
      ...actions.map(([icon, label, run]) => ({ icon, label, hint: "Do", run })),
    ];
    // His things, by name: typing a unit's name opens its page.
    const s0 = q.trim().toLowerCase();
    if (s0) all.push(...things.all.filter((o) => !o.target).map((o) => ({ icon: icon[o.kind], label: o.name, hint: kindName[o.kind], run: () => shell.open({ id: o.id }) })));
    const s = q.trim().toLowerCase();
    const hits = (s ? all.filter((i) => i.label.toLowerCase().includes(s)) : all).slice(0, 40);
    if (s) hits.push({ icon: "sparkles", label: `Ask the copilot: ${q.trim()}`, hint: "Ask", run: () => shell.send(q.trim()) });
    return hits;
  });
  const pick = (i: Item) => {
    i.run();
    q = "";
    open = false;
    input?.blur();
  };
  const key = (e: KeyboardEvent) => {
    if (e.key === "ArrowDown") (e.preventDefault(), (active = Math.min(active + 1, items.length - 1)));
    else if (e.key === "ArrowUp") (e.preventDefault(), (active = Math.max(active - 1, 0)));
    else if (e.key === "Enter" && items[active]) pick(items[active]);
    else if (e.key === "Escape") ((open = false), input?.blur());
  };
  $effect(() => {
    const onkey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") (e.preventDefault(), input?.focus());
    };
    const onfind = () => input?.focus();
    window.addEventListener("keydown", onkey);
    window.addEventListener("qmx:find", onfind);
    return () => (window.removeEventListener("keydown", onkey), window.removeEventListener("qmx:find", onfind));
  });
</script>

<div class="relative {primary ? 'w-[min(44rem,100%)]' : 'w-80'}">
  <label class="well bg-panel flex items-center gap-2.5 px-3 {primary ? 'h-11' : 'h-9'}">
    <Icon name="search" class="text-muted-foreground size-4 shrink-0" />
    <input
      bind:this={input}
      bind:value={q}
      class="placeholder:text-muted-foreground min-w-0 flex-1 bg-transparent outline-none"
      placeholder={primary ? "Go anywhere, open anything, or ask" : "Search or ask"}
      aria-label="Search, go to a place, or ask the copilot"
      onfocus={() => ((open = true), (active = 0))}
      onblur={() => setTimeout(() => (open = false), 120)}
      oninput={() => (active = 0)}
      onkeydown={key}
    />
    <kbd class="text-muted-foreground num shrink-0 text-xs">Ctrl K</kbd>
  </label>
  {#if open}
    <ul class="bg-popover border-border absolute top-full right-0 left-0 z-50 mt-1.5 max-h-[26rem] overflow-y-auto rounded-lg border p-1.5 shadow-2xl" role="listbox">
      {#each items as it, i (i)}
        <li role="option" aria-selected={i === active}>
          <button
            class="flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-left {i === active ? 'bg-accent' : ''}"
            onmousedown={(e) => (e.preventDefault(), pick(it))}
            onmouseenter={() => (active = i)}
          >
            <Icon name={it.icon} class="text-muted-foreground size-4 shrink-0" />
            <span class="min-w-0 flex-1 truncate">{it.label}</span>
            <span class="text-muted-foreground shrink-0 text-sm">{it.hint}</span>
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>
