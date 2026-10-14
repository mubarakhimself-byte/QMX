<script lang="ts">
  /**
   * Portfolio (operator rulings 2026-10-02/03): pods, risk and sizing,
   * promotions and approvals, allocation, MIS, and live trading (the trading
   * servers folded in). A tiling board like the Lab, with its own copilot.
   * Showing live or paper is a view filter, never a control.
   */
  import { page } from "$app/state";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Plus from "@lucide/svelte/icons/plus";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Save from "@lucide/svelte/icons/save";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import LayoutTemplate from "@lucide/svelte/icons/layout-template";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Input } from "$lib/components/ui/input";
  import { cn } from "$lib/utils";
  import TileBoard from "$lib/workbench/tiles/TileBoard.svelte";
  import { addPane, pane, type TilePane } from "$lib/workbench/tiles/tiles";
  import CopilotColumn from "$lib/workbench/CopilotColumn.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { PORTFOLIO_PANELS } from "$lib/portfolio/catalog";
  import { portfolio } from "$lib/portfolio/portfolio.svelte";
  import { PORTFOLIO_CONTEXT } from "$lib/portfolio/copilot";
  import { MODE_BORDER } from "$lib/portfolio/bits";
  import TemplatesDialog from "$lib/portfolio/TemplatesDialog.svelte";
  import ServersStrip from "$lib/portfolio/ServersStrip.svelte";
  import KillSwitchChip from "$lib/portfolio/KillSwitchChip.svelte";

  const L = portfolio.layouts;
  const fromUrl = page.url.searchParams.get("layout");
  if (fromUrl && L.layouts.some((l) => l.id === fromUrl)) L.activeId = fromUrl;

  const catalog = Object.fromEntries(
    Object.entries(PORTFOLIO_PANELS).map(([id, p]) => [
      id,
      { title: p.title, icon: p.icon, note: p.note },
    ]),
  );
  const WORLDS = [
    { id: "all", label: "All" },
    { id: "live", label: "Live" },
    { id: "paper", label: "Paper" },
  ] as const;

  function borderFor(p: TilePane) {
    if (!PORTFOLIO_PANELS[p.panel]?.trading || portfolio.world === "all")
      return undefined;
    return portfolio.world === "live" ? MODE_BORDER.live : MODE_BORDER.paper;
  }
  function addPanel(id: string) {
    const l = L.active;
    L.update({
      ...l,
      root: addPane(l.root, pane(`${id}-${Date.now().toString(36)}`, id)),
    });
    workbench.notify(`${PORTFOLIO_PANELS[id].title} added to ${l.name}.`);
  }
  let saving = $state(false);
  let layoutName = $state("");
</script>

<div class="scrim flex h-full flex-col">
  {#if workbench.demoMode}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" /> Demo portfolio. Sample CFD and
      crypto accounts, pods and prices; no money is real.
    </div>
  {/if}
  <header class="flex h-12 shrink-0 items-center gap-3 border-b px-3">
    <h1 class="text-base font-semibold">Portfolio</h1>
    <div
      class="bg-muted/50 flex items-center gap-0.5 rounded-md p-0.5"
      role="radiogroup"
      aria-label="Showing"
    >
      {#each WORLDS as w (w.id)}
        <button
          type="button"
          role="radio"
          aria-checked={portfolio.world === w.id}
          class={cn(
            "flex h-6 items-center gap-1.5 rounded px-2.5 text-xs",
            portfolio.world === w.id
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
          onclick={() => (portfolio.world = w.id)}
        >
          {#if w.id !== "all"}<span
              class="size-1.5 rounded-full"
              style="background: var(--tone-{w.id})"
            ></span>{/if}{w.label}
        </button>
      {/each}
    </div>
    <KillSwitchChip />
    <nav class="flex items-center gap-0.5" aria-label="Layouts">
      {#each L.layouts as l (l.id)}
        <button
          type="button"
          class={cn(
            "h-7 rounded-md px-3 text-sm whitespace-nowrap",
            L.activeId === l.id
              ? "bg-muted text-foreground font-medium"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-current={L.activeId === l.id ? "page" : undefined}
          onclick={() => (L.activeId = l.id)}
          >{l.name}{#if L.isEdited(l.id)}<span
              class="text-muted-foreground"
              title="Changed from the default">*</span
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
              aria-label="Layout options"><ChevronDown /></Button
            >
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content>
          <DropdownMenu.Item
            onclick={() => {
              layoutName = `${L.active.name} (mine)`;
              saving = true;
            }}><Save />Save as a new layout</DropdownMenu.Item
          >
          {#if L.isBuiltin(L.activeId)}
            <DropdownMenu.Item
              disabled={!L.isEdited(L.activeId)}
              onclick={() => L.reset(L.activeId)}
              ><RotateCcw />Reset {L.active.name} to default</DropdownMenu.Item
            >
          {:else}
            <DropdownMenu.Item onclick={() => L.reset(L.activeId)}
              ><Trash2 />Delete {L.active.name}</DropdownMenu.Item
            >
          {/if}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </nav>
    <div class="ml-auto flex items-center gap-1.5">
      <ServersStrip />
      <span class="bg-border mx-1 h-5 w-px"></span>
      <Button
        variant="ghost"
        size="sm"
        onclick={() => (portfolio.templatesOpen = true)}
        title="Templates"
        ><LayoutTemplate /><span class="hidden 2xl:inline">Templates</span
        ></Button
      >
      <Button
        variant={L.editing ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={L.editing}
        onclick={() => (L.editing = !L.editing)}
        title={L.editing ? "Done" : "Edit layout"}
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
          {#each Object.entries(PORTFOLIO_PANELS) as [id, p] (id)}
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
            onclick={() => {
              portfolio.copilotOpen = true;
              workbench.notify(
                "Describe the panel you want; the Portfolio copilot builds it from your accounts and pods.",
              );
            }}><Sparkles />Build a new panel…</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
      <Button
        variant={portfolio.copilotOpen ? "secondary" : "ghost"}
        size="icon-sm"
        aria-label="Toggle Portfolio copilot"
        aria-pressed={portfolio.copilotOpen}
        onclick={() => (portfolio.copilotOpen = !portfolio.copilotOpen)}
        ><Sparkles /></Button
      >
    </div>
  </header>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={portfolio.copilotOpen ? 76 : 100} minSize={50}>
      <TileBoard
        class="p-1.5"
        layout={L.active}
        {catalog}
        editing={L.editing}
        onchange={(next) => L.update(next)}
        {borderFor}
      >
        {#snippet panel(p)}
          {@const View = PORTFOLIO_PANELS[p.panel].view}
          <View />
        {/snippet}
      </TileBoard>
    </Resizable.Pane>
    {#if portfolio.copilotOpen}
      <Resizable.Handle />
      <Resizable.Pane defaultSize={24} minSize={16} maxSize={40}>
        <CopilotColumn
          title="Portfolio copilot"
          profile="portfolio"
          hint="Knows every account, pod and bot on the road to live. It explains, watches and brings tested pods in from the Lab; you sign anything that touches money."
          placeholder="Bring the vol-target pod from the Lab onto Bybit…"
          onclose={() => (portfolio.copilotOpen = false)}
          refs={workbench.copilotRefs}
          onremoveref={(r) => workbench.removeRef(r)}
          context={PORTFOLIO_CONTEXT}
          origin="Portfolio"
          starters={[
            "Let the Bybit account take on Alt momentum and grow faster",
            "Why is SOL near its cap in Alt momentum?",
            "Bring the tested vol-target pod from the Lab onto paper",
            "Summarise ETH mean reversion's journal this week",
          ]}
        />
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>

<TemplatesDialog />

<Dialog.Root bind:open={saving}>
  <Dialog.Content class="sm:max-w-md">
    <form
      class="flex flex-col gap-4"
      onsubmit={(e) => {
        e.preventDefault();
        const l = L.saveAs(layoutName);
        saving = false;
        workbench.notify(`Saved layout: ${l.name}`);
      }}
    >
      <Dialog.Header>
        <Dialog.Title>Save this layout</Dialog.Title>
        <Dialog.Description
          >Keeps the tiles, their sizes, links and what is minimised.</Dialog.Description
        >
      </Dialog.Header>
      <Input bind:value={layoutName} maxlength={40} aria-label="Layout name" />
      <Dialog.Footer>
        <Button type="button" variant="ghost" onclick={() => (saving = false)}
          >Cancel</Button
        >
        <Button type="submit" disabled={!layoutName.trim()}>Save layout</Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
