<script lang="ts">
  /**
   * Home (rethink, 2026-10-04). A greeting, an editable ticker, a bell for
   * everything that needs you, and the same tile board as the Lab and
   * Portfolio: built-in tabs (Today, Markets, Research) plus tabs you save
   * yourself. Panels link to the screen each thing lives on.
   */
  import Bell from "@lucide/svelte/icons/bell";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Plus from "@lucide/svelte/icons/plus";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import * as Dialog from "$lib/components/ui/dialog";
  import TickerTape from "$lib/qmx/TickerTape.svelte";
  import TileBoard from "$lib/workbench/tiles/TileBoard.svelte";
  import { addPane, pane } from "$lib/workbench/tiles/tiles";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { cn } from "$lib/utils";
  import { COINS, fmtPx, home } from "$lib/home/home.svelte";
  import { HOME_PANELS } from "$lib/home/catalog";
  import { needs } from "$lib/home/needs";

  const L = home.layouts;
  const demo = workbench.demoMode;
  const hour = new Date().getHours();
  const hello =
    hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const today = new Date().toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
  const waiting = $derived(needs());
  const ticker = $derived(
    home.ticker
      .map((s) => COINS.find((c) => c.sym === s))
      .filter((c) => !!c)
      .map((c) => ({ sym: c.sym, px: fmtPx(c.px), chg: c.chg })),
  );
  const catalog = Object.fromEntries(
    Object.entries(HOME_PANELS).map(([id, p]) => [
      id,
      { title: p.title, icon: p.icon, note: p.note },
    ]),
  );

  function addPanel(id: string) {
    const l = L.active;
    L.update({
      ...l,
      root: addPane(l.root, pane(`${id}-${Date.now().toString(36)}`, id)),
    });
    workbench.notify(`${HOME_PANELS[id].title} added to ${l.name}.`);
  }
  let naming = $state(false);
  let tabName = $state("");
  function saveTab(e: SubmitEvent) {
    e.preventDefault();
    const t = L.saveAs(tabName);
    naming = false;
    workbench.notify(`New tab: ${t.name}`);
  }
  function toggleCoin(sym: string) {
    home.setTicker(
      home.ticker.includes(sym)
        ? home.ticker.filter((s) => s !== sym)
        : [...home.ticker, sym],
    );
  }
  /* eslint-disable svelte/no-navigation-without-resolve */
  function go(url: string) {
    goto(url);
  }
  /* eslint-enable svelte/no-navigation-without-resolve */
  function askCopilot(text: string) {
    go(`${resolve("/copilot")}?ask=${encodeURIComponent(text)}`);
  }
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo Home. Items come from the other screens' samples, so every link opens the
      real place.
    </div>
  {/if}
  <header class="flex h-14 shrink-0 items-center gap-3 border-b px-4">
    <div class="min-w-0">
      <h1 class="truncate text-lg leading-tight font-semibold">{hello}</h1>
      <p class="text-muted-foreground text-[13px]">{today}</p>
    </div>
    <nav class="ml-4 flex items-center gap-0.5" aria-label="Tabs">
      {#each L.layouts as l (l.id)}
        <button
          type="button"
          class={cn(
            "h-8 rounded-md px-3 text-sm whitespace-nowrap",
            L.activeId === l.id
              ? "bg-muted text-foreground font-medium"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-current={L.activeId === l.id ? "page" : undefined}
          onclick={() => (L.activeId = l.id)}
          >{l.name}{#if L.isEdited(l.id)}<span class="text-muted-foreground"
              >*</span
            >{/if}</button
        >
      {/each}
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button
              {...props}
              variant="ghost"
              size="icon-sm"
              aria-label="Tab options"><ChevronDown /></Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content>
          <DropdownMenu.Item
            onclick={() => {
              tabName = `${L.active.name} (mine)`;
              naming = true;
            }}><Plus />Save as a new tab</DropdownMenu.Item
          >
          <DropdownMenu.Item
            onclick={() => askCopilot("Make me a new Home tab that shows ")}
            ><Sparkles />Ask the copilot for a tab</DropdownMenu.Item
          >
          {#if L.isBuiltin(L.activeId)}
            <DropdownMenu.Item
              disabled={!L.isEdited(L.activeId)}
              onclick={() => L.reset(L.activeId)}
              ><RotateCcw />Reset {L.active.name}</DropdownMenu.Item
            >
          {:else}
            <DropdownMenu.Item onclick={() => L.reset(L.activeId)}
              ><Trash2 />Delete {L.active.name}</DropdownMenu.Item
            >
          {/if}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </nav>
    <div class="ml-auto flex items-center gap-1">
      <DropdownMenu.Root>
        <DropdownMenu.Trigger
          class="hover:bg-muted data-[state=open]:bg-muted relative flex size-9 items-center justify-center rounded-md"
          aria-label={`${waiting.length} things need you`}
          title="What needs you"
        >
          <Bell class="size-5" />
          {#if waiting.length}<span
              class="bg-destructive num absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[11px] text-white"
              >{waiting.length}</span
            >{/if}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-96">
          <DropdownMenu.Label>Needs you</DropdownMenu.Label>
          {#each waiting as n (n.id)}
            <DropdownMenu.Item
              onclick={() =>
                go(`${resolve(n.path as "/")}${n.query ? `?${n.query}` : ""}`)}
            >
              <span class="flex flex-col">
                <span>{n.title}</span>
                <span class="text-muted-foreground text-xs"
                  >{n.kind} · {n.why}</span
                >
              </span>
            </DropdownMenu.Item>
          {:else}
            <DropdownMenu.Label class="text-muted-foreground font-normal"
              >Nothing needs you.</DropdownMenu.Label
            >
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
      <Button
        variant={L.editing ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={L.editing}
        title={L.editing ? "Done" : "Edit layout"}
        onclick={() => (L.editing = !L.editing)}
        ><Pencil /><span class="hidden 2xl:inline"
          >{L.editing ? "Done" : "Edit layout"}</span
        ></Button
      >
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="ghost" size="sm" title="Add a panel"
              ><Plus /><span class="hidden 2xl:inline">Panel</span></Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-64">
          {#each Object.entries(HOME_PANELS).filter(([id]) => id !== "pinned") as [id, p] (id)}
            <DropdownMenu.Item onclick={() => addPanel(id)}>
              <p.icon />
              <span class="flex flex-col"
                ><span>{p.title}</span><span
                  class="text-muted-foreground text-xs">{p.note}</span
                ></span
              >
            </DropdownMenu.Item>
          {/each}
          <DropdownMenu.Separator />
          <DropdownMenu.Item
            onclick={() => askCopilot("Build me a Home panel that shows ")}
            ><Sparkles />Build a new panel with the copilot</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </div>
  </header>

  <div class="flex shrink-0 items-center">
    <div class="min-w-0 flex-1"><TickerTape items={ticker} /></div>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        class="bg-panel hover:bg-muted flex h-8 shrink-0 items-center gap-1 border-b border-l px-2 text-xs"
        aria-label="Choose what the ticker shows"
        title="Choose what the ticker shows"
        ><SlidersHorizontal class="size-3.5" /></DropdownMenu.Trigger
      >
      <DropdownMenu.Content align="end" class="w-56">
        <DropdownMenu.Label>Ticker</DropdownMenu.Label>
        {#each COINS as c (c.sym)}
          <DropdownMenu.CheckboxItem
            checked={home.ticker.includes(c.sym)}
            onCheckedChange={() => toggleCoin(c.sym)}
            closeOnSelect={false}>{c.sym}</DropdownMenu.CheckboxItem
          >
        {/each}
        <DropdownMenu.Separator />
        <DropdownMenu.Item
          onclick={() => askCopilot("Change my Home ticker to show ")}
          ><Sparkles />Ask the copilot</DropdownMenu.Item
        >
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </div>

  <div class="scrim min-h-0 flex-1">
    <TileBoard
      class="p-1.5"
      layout={L.active}
      {catalog}
      editing={L.editing}
      onchange={(next) => L.update(next)}
    >
      {#snippet panel(p)}
        {@const View = HOME_PANELS[p.panel].view}
        <View tile={p.id} />
      {/snippet}
    </TileBoard>
  </div>
</div>

<Dialog.Root bind:open={naming}>
  <Dialog.Content class="sm:max-w-md">
    <form class="flex flex-col gap-4" onsubmit={saveTab}>
      <Dialog.Header>
        <Dialog.Title>Save as a new tab</Dialog.Title>
        <Dialog.Description
          >Keeps these panels and their sizes as your own Home tab.</Dialog.Description
        >
      </Dialog.Header>
      <Input bind:value={tabName} maxlength={40} aria-label="Tab name" />
      <Dialog.Footer>
        <Button type="button" variant="ghost" onclick={() => (naming = false)}
          >Cancel</Button
        >
        <Button type="submit" disabled={!tabName.trim()}>Save tab</Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
