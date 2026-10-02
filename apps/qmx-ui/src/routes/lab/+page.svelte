<script lang="ts">
  /**
   * The Lab (operator ruling 2026-10-02): Authoring, Backtest lab and ML Studio
   * in one permanent section. A tiling board with saved layouts (Build, Test,
   * Train, Compare, and your own), linked tiles, a dock for minimised tiles,
   * and a Lab copilot. Docs still call this destination Authoring (DEC-0470);
   * the rename is flagged for Codex.
   */
  import { page } from "$app/state";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Play from "@lucide/svelte/icons/play";
  import Plus from "@lucide/svelte/icons/plus";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Save from "@lucide/svelte/icons/save";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Input } from "$lib/components/ui/input";
  import { cn } from "$lib/utils";
  import TileBoard from "$lib/workbench/tiles/TileBoard.svelte";
  import { addPane, pane } from "$lib/workbench/tiles/tiles";
  import CopilotColumn from "$lib/workbench/CopilotColumn.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PANELS } from "$lib/lab/catalog";
  import { lab } from "$lib/lab/lab.svelte";
  import { ASSETS, ENVIRONMENTS } from "$lib/lab/demo";
  import EnvChip from "$lib/lab/EnvChip.svelte";
  import { LAB_CONTEXT, LAB_SESSIONS } from "$lib/lab/copilot";

  const fromUrl = page.url.searchParams.get("layout");
  if (fromUrl && lab.layouts.some((l) => l.id === fromUrl))
    lab.activeId = fromUrl;

  const SUBJECTS = ASSETS.filter((a) =>
    ["bot", "template", "model"].includes(a.kind),
  );
  let subject = $state(SUBJECTS.find((s) => s.id === "bot-gbm")!);
  let runOn = $state("local");

  const catalog = Object.fromEntries(
    Object.entries(LAB_PANELS).map(([id, p]) => [
      id,
      { title: p.title, icon: p.icon, note: p.note },
    ]),
  );

  function addPanel(id: string) {
    const l = lab.active;
    const tileId = `${id}-${Date.now().toString(36)}`;
    lab.update({ ...l, root: addPane(l.root, pane(tileId, id)) });
    workbench.notify(`${LAB_PANELS[id].title} added to ${l.name}.`);
  }
  let saving = $state(false);
  let layoutName = $state("");
  function openSave() {
    layoutName = `${lab.active.name} (mine)`;
    saving = true;
  }
  function saveLayout(e: SubmitEvent) {
    e.preventDefault();
    const l = lab.saveAs(layoutName);
    saving = false;
    workbench.notify(`Saved layout: ${l.name}`);
  }
  function run() {
    const env = ENVIRONMENTS.find((e) => e.id === runOn)!;
    workbench.notify(
      `Running needs the daemon. It would run the published version of ${subject.name} on ${env.name}.`,
    );
  }
</script>

<div class="scrim flex h-full flex-col">
  {#if workbench.demoMode}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" /> Demo Lab. Sample runs, models
      and machines; nothing here ran.
    </div>
  {/if}
  <header class="flex h-12 shrink-0 items-center gap-3 border-b px-3">
    <h1 class="text-base font-semibold">Lab</h1>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="ghost" size="sm" class="gap-1.5">
            <span class="text-muted-foreground text-xs">Working on</span>
            {subject.name}<ChevronDown class="size-3.5" />
          </Button>
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content class="w-64">
        {#each SUBJECTS as s (s.id)}
          <DropdownMenu.Item onclick={() => (subject = s)}>
            <span class="flex flex-col">
              <span>{s.name}</span>
              <span class="text-muted-foreground text-xs">{s.meta}</span>
            </span>
          </DropdownMenu.Item>
        {/each}
        <DropdownMenu.Separator />
        <DropdownMenu.Item
          onclick={() =>
            workbench.notify(
              "Start from a hypothesis, a template, code or an import. The Lab copilot can draft it.",
            )}><Plus />Start something new</DropdownMenu.Item
        >
      </DropdownMenu.Content>
    </DropdownMenu.Root>

    <nav class="flex items-center gap-0.5" aria-label="Layouts">
      {#each lab.layouts as l (l.id)}
        <button
          type="button"
          class={cn(
            "h-7 rounded-md px-3 text-sm",
            lab.activeId === l.id
              ? "bg-muted text-foreground font-medium"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-current={lab.activeId === l.id ? "page" : undefined}
          onclick={() => (lab.activeId = l.id)}
          >{l.name}{#if lab.isEdited(l.id)}<span
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
          <DropdownMenu.Item onclick={openSave}
            ><Save />Save as a new layout</DropdownMenu.Item
          >
          {#if lab.isBuiltin(lab.activeId)}
            <DropdownMenu.Item
              disabled={!lab.isEdited(lab.activeId)}
              onclick={() => lab.reset(lab.activeId)}
              ><RotateCcw />Reset {lab.active.name} to default</DropdownMenu.Item
            >
          {:else}
            <DropdownMenu.Item onclick={() => lab.reset(lab.activeId)}
              ><Trash2 />Delete {lab.active.name}</DropdownMenu.Item
            >
          {/if}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </nav>

    <div class="ml-auto flex items-center gap-1.5">
      <Button
        variant={lab.editing ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={lab.editing}
        onclick={() => (lab.editing = !lab.editing)}
        ><Pencil />{lab.editing ? "Done" : "Edit layout"}</Button
      >
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="ghost" size="sm"><Plus />Panel</Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-64">
          {#each Object.entries(LAB_PANELS) as [id, p] (id)}
            <DropdownMenu.Item onclick={() => addPanel(id)}>
              <p.icon />
              <span class="flex flex-col">
                <span>{p.title}</span>
                <span class="text-muted-foreground text-xs">{p.note}</span>
              </span>
            </DropdownMenu.Item>
          {/each}
          <DropdownMenu.Separator />
          <DropdownMenu.Item
            onclick={() => {
              lab.copilotOpen = true;
              workbench.notify(
                "Describe the panel you want; the Lab copilot builds it from your data.",
              );
            }}><Sparkles />Build a new panel…</DropdownMenu.Item
          >
        </DropdownMenu.Content>
      </DropdownMenu.Root>
      <span class="bg-border mx-1 h-5 w-px"></span>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button
              {...props}
              variant="outline"
              size="sm"
              class="gap-1.5"
              aria-label="Choose where runs go"
            >
              <EnvChip env={runOn} /><ChevronDown class="size-3.5" />
            </Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-72">
          <DropdownMenu.Label>Run on</DropdownMenu.Label>
          {#each ENVIRONMENTS as e (e.id)}
            <DropdownMenu.Item
              disabled={e.status === "offline"}
              onclick={() => (runOn = e.id)}
            >
              <span class="flex w-full flex-col">
                <span class="flex items-center justify-between gap-2"
                  >{e.name}<span class="num text-muted-foreground text-xs"
                    >{e.slots[0]}/{e.slots[1]} slots</span
                  ></span
                >
                <span class="text-muted-foreground text-xs"
                  >{e.where} · {e.status === "offline"
                    ? "offline"
                    : e.evidence
                      ? "can produce evidence"
                      : "exploration only"}</span
                >
              </span>
            </DropdownMenu.Item>
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>
      <Button size="sm" onclick={run}><Play />Run</Button>
      <Button
        variant={lab.copilotOpen ? "secondary" : "ghost"}
        size="icon-sm"
        aria-label="Toggle Lab copilot"
        aria-pressed={lab.copilotOpen}
        onclick={() => (lab.copilotOpen = !lab.copilotOpen)}
        ><Sparkles /></Button
      >
    </div>
  </header>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={lab.copilotOpen ? 76 : 100} minSize={50}>
      <TileBoard
        class="p-1.5"
        layout={lab.active}
        {catalog}
        editing={lab.editing}
        onchange={(next) => lab.update(next)}
      >
        {#snippet panel(p)}
          {@const View = LAB_PANELS[p.panel].view}
          <View link={p.link} />
        {/snippet}
      </TileBoard>
    </Resizable.Pane>
    {#if lab.copilotOpen}
      <Resizable.Handle />
      <Resizable.Pane defaultSize={24} minSize={16} maxSize={40}>
        <CopilotColumn
          title="Lab copilot"
          profile="lab"
          hint={`Knows ${subject.name}, the open layout and every run. Ask it to build a step, a panel, a test or a sweep.`}
          placeholder="Sweep this across the majors on H1 and H4…"
          onclose={() => (lab.copilotOpen = false)}
          refs={workbench.copilotRefs}
          onremoveref={(r) => workbench.removeRef(r)}
          context={LAB_CONTEXT}
          sessions={LAB_SESSIONS}
        />
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>

<Dialog.Root bind:open={saving}>
  <Dialog.Content class="sm:max-w-md">
    <form class="flex flex-col gap-4" onsubmit={saveLayout}>
      <Dialog.Header>
        <Dialog.Title>Save this layout</Dialog.Title>
        <Dialog.Description
          >Keeps the tiles, their sizes, links and what is minimised. It appears
          next to Build, Test, Train and Compare.</Dialog.Description
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
