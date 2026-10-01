<script lang="ts">
  /**
   * The frame every mini app renders in: header with pack-declared views,
   * edit layout, copilot toggle; a 12-column widget grid built from a
   * WidgetBoard; expand/return; add widget; optional app copilot (only
   * when the pack declares a copilot profile). Unknown widgets render a
   * typed "not supported" frame instead of breaking the app.
   */
  import type { Snippet } from "svelte";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Check from "@lucide/svelte/icons/check";
  import Plus from "@lucide/svelte/icons/plus";
  import PanelRight from "@lucide/svelte/icons/panel-right";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tabs from "$lib/components/ui/tabs";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import WidgetFrame from "./WidgetFrame.svelte";
  import CopilotColumn from "./CopilotColumn.svelte";
  import { SPAN, type WidgetBoard } from "./board.svelte";
  import { workbench } from "./workbench.svelte";
  import { cn } from "$lib/utils";

  let {
    board,
    name,
    badge,
    demoNote,
    tone,
    copilot,
    known,
    headerExtra,
    strip,
    sidebar,
    widget,
  }: {
    board: WidgetBoard;
    name: string;
    badge?: string;
    demoNote?: string;
    /** Trading surfaces: whole-frame border by mode. */
    tone?: "paper" | "live";
    /** Present only when the pack declares a copilot profile. */
    copilot?: { hint: string; placeholder: string };
    /** Widget ids this app version can render; others show "not supported". */
    known?: (id: string) => boolean;
    headerExtra?: Snippet;
    /** Full-width strip under the header (e.g. a price ticker). */
    strip?: Snippet;
    sidebar?: Snippet;
    widget: Snippet<[string]>;
  } = $props();

  let copilotOpen = $state(true);
</script>

{#snippet frame(id: string, cls: string)}
  {@const w = board.spec(id)}
  {#if known && !known(id)}
    <WidgetFrame
      title={w?.title ?? id}
      state="unavailable"
      reason="This widget type isn't supported by this version of the app."
      class={cls}
      onclose={board.editing ? () => board.close(id) : undefined}
    />
  {:else}
    <WidgetFrame
      title={w?.title ?? id}
      class={cn(
        cls,
        board.editing && "outline-ring/50 outline-1 outline-dashed",
      )}
      minimized={board.minimized.has(id)}
      expanded={board.expanded === id}
      onmessage={() => board.mention(name, id)}
      onminimize={board.expanded === id ? undefined : () => board.toggleMin(id)}
      onexpand={() => board.toggleExpand(id)}
      onclose={board.editing ? () => board.close(id) : undefined}
    >
      {@render widget(id)}
    </WidgetFrame>
  {/if}
{/snippet}

<div
  class={cn("flex h-full flex-col", tone && "border-2")}
  style={tone ? `border-color: var(--tone-${tone})` : undefined}
>
  {#if demoNote}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      {demoNote}
    </div>
  {/if}

  <header class="bg-panel flex h-11 shrink-0 items-center gap-3 border-b px-3">
    <span class="text-sm font-semibold">{name}</span>
    {#if badge}<Badge variant="outline" class="h-4 px-1.5 text-[10px]"
        >{badge}</Badge
      >{/if}
    {#if tone}
      <Badge
        class="h-5 px-2 text-[11px] font-semibold"
        style="background: var(--tone-{tone}); color: #0b0b0b"
        >{tone === "live" ? "LIVE" : "PAPER"}</Badge
      >
    {/if}
    {#if board.views.length > 1}
      <Tabs.Root value={board.view} onValueChange={(v) => board.setView(v)}>
        <Tabs.List variant="line">
          {#each board.views as v (v)}<Tabs.Trigger value={v}>{v}</Tabs.Trigger
            >{/each}
        </Tabs.List>
      </Tabs.Root>
    {/if}
    {#if headerExtra}{@render headerExtra()}{/if}
    <div class="ml-auto flex items-center gap-1">
      <Button
        variant={board.editing ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={board.editing}
        onclick={() => (board.editing = !board.editing)}
      >
        {#if board.editing}<Check /> Done{:else}<Pencil /> Edit layout{/if}
      </Button>
      {#if copilot}
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Toggle app copilot"
          aria-pressed={copilotOpen}
          onclick={() => (copilotOpen = !copilotOpen)}><PanelRight /></Button
        >
      {/if}
    </div>
  </header>

  {#if strip}{@render strip()}{/if}

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    {#if sidebar}
      <Resizable.Pane defaultSize={20} minSize={14} maxSize={32}>
        <aside class="bg-panel h-full overflow-auto border-r">
          {@render sidebar()}
        </aside>
      </Resizable.Pane>
      <Resizable.Handle />
    {/if}
    <Resizable.Pane defaultSize={copilot ? 76 : 100} minSize={45}>
      <div class="scrim relative h-full overflow-auto p-3">
        {#if board.expanded}
          {@render frame(board.expanded, "h-full")}
        {:else}
          <div class="grid min-h-full grid-flow-row-dense auto-rows-[minmax(15rem,1fr)] grid-cols-12 gap-3">
            {#each board.shown as w (w.id)}
              {@render frame(
                w.id,
                cn(
                  SPAN[w.size ?? "md"],
                  w.tall && !board.minimized.has(w.id) && "row-span-2",
                  board.minimized.has(w.id) && "h-fit",
                ),
              )}
            {/each}
          </div>
          {#if board.editing && board.addable.length}
            <div class="sticky bottom-0 mt-3 flex justify-end">
              <DropdownMenu.Root>
                <DropdownMenu.Trigger>
                  {#snippet child({ props })}
                    <Button {...props} size="sm"><Plus /> Add widget</Button>
                  {/snippet}
                </DropdownMenu.Trigger>
                <DropdownMenu.Content align="end">
                  {#each board.addable as w (w.id)}
                    <DropdownMenu.Item onclick={() => board.add(w.id)}
                      >{w.title}</DropdownMenu.Item
                    >
                  {/each}
                </DropdownMenu.Content>
              </DropdownMenu.Root>
            </div>
          {/if}
        {/if}
      </div>
    </Resizable.Pane>
    {#if copilot && copilotOpen}
      <Resizable.Handle />
      <Resizable.Pane defaultSize={24} minSize={18} maxSize={40}>
        <CopilotColumn
          title="App copilot"
          profile="app-use"
          hint={copilot.hint}
          placeholder={copilot.placeholder}
          refs={workbench.copilotRefs}
          onremoveref={(r) => workbench.removeRef(r)}
          onclose={() => (copilotOpen = false)}
        />
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>
