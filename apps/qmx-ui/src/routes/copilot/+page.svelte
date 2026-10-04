<script lang="ts">
  /**
   * The copilot as a desk of errands (redesign, 2026-10-04). You hand it
   * errands that can run for days; the screen shows one at a time, told
   * plainly: what it is for, how far it has got, the conversation as
   * letters, and the one decision it needs from you where you type. Its
   * work (helpers, reports, changes, terminal, browser) opens in a drawer
   * only when you ask. Errands from the Lab and Portfolio copilots live in
   * the same list. DEMO: replies are scripted and say so.
   * Params: ?session=, ?start=train|import|workflow, ?ask=, ?focus=1.
   */
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import PanelLeft from "@lucide/svelte/icons/panel-left";
  import X from "@lucide/svelte/icons/x";
  import * as Resizable from "$lib/components/ui/resizable";
  import { Button } from "$lib/components/ui/button";
  import Composer from "$lib/workbench/Composer.svelte";
  import GuidedStart from "$lib/workbench/GuidedStart.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { addPane, pane } from "$lib/workbench/tiles/tiles";
  import Thread from "$lib/copilot/Thread.svelte";
  import ErrandHeader from "$lib/copilot/ErrandHeader.svelte";
  import SessionsSidebar from "$lib/copilot/SessionsSidebar.svelte";
  import WorkArea from "$lib/copilot/WorkArea.svelte";
  import HowDoI from "$lib/copilot/HowDoI.svelte";
  import PendingPanel from "$lib/copilot/PendingPanel.svelte";
  import { copilot } from "$lib/copilot/store.svelte";
  import { pinned } from "$lib/sdk/pinned.svelte";
  import { lab } from "$lib/lab/lab.svelte";

  const params = page.url.searchParams;
  const demo = workbench.demoMode;
  let focus = $state(params.get("focus") === "1");
  let showSessions = $state(true);
  let drawer = $state<string | null>(null);
  function popOut() {
    window.open(
      resolve("/copilot") + "?focus=1",
      "qmx-copilot",
      "popup,width=1280,height=900",
    );
  }

  type StartKind = "train" | "import" | "workflow";
  const startParam = params.get("start");
  let startKind = $state<StartKind | null>(
    startParam === "train" ||
      startParam === "import" ||
      startParam === "workflow"
      ? startParam
      : null,
  );
  const askedSession = params.get("session");
  let active = $state<string | null>(
    startParam || params.get("ask")
      ? null
      : askedSession && copilot.session(askedSession)
        ? askedSession
        : demo
          ? "weekend"
          : null,
  );
  let seed = $state(params.get("ask") ?? "");
  let artifact = $state<string | null>(null);
  let writing = $state(false);

  const session = $derived(copilot.session(active));
  const parent = $derived(
    session?.parent ? copilot.session(session.parent) : undefined,
  );
  const blocks = $derived(copilot.blocks(active));
  const pending = $derived(copilot.pending(active));
  const busy = $derived(!!(active && copilot.busy[active]));
  const waitingIds = $derived(
    copilot.sessions.filter((s) => copilot.pending(s.id)).map((s) => s.id),
  );

  function open(id: string) {
    active = id;
    startKind = null;
    writing = false;
  }
  function newErrand() {
    open(copilot.create("Main"));
    seed = "";
  }
  async function send(text: string, refs: string[]) {
    if (!active) active = copilot.create("Main");
    startKind = null;
    writing = false;
    await copilot.send(active, text, refs);
  }
  function openAgent(agentId: string) {
    const child = active ? `${active}/${agentId}` : null;
    if (child && copilot.session(child)) open(child);
    else drawer = "activity";
  }
  function onpanel(i: number, state: "kept" | "discarded" | "pinned") {
    if (!active) return;
    copilot.setPanel(active, i, state);
    const b = copilot.blocks(active)[i];
    if (state === "pinned" && b?.kind === "panel") {
      const tileId = `pinned-${Date.now().toString(36)}`;
      pinned.add(tileId, b.spec);
      const l = lab.active;
      lab.update({ ...l, root: addPane(l.root, pane(tileId, "pinned")) });
      workbench.notify(
        `"${b.spec.title}" is now a tile in the Lab's ${l.name} layout. No restart needed.`,
        "/lab",
        "Open the Lab",
      );
    }
  }
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo copilot. Replies are scripted and say so; nothing here ran.
    </div>
  {/if}
  <header class="flex h-12 shrink-0 items-center gap-2 border-b px-3">
    {#if !focus}
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label={showSessions ? "Hide errands" : "Show errands"}
        title={showSessions ? "Hide errands" : "Show errands"}
        aria-pressed={showSessions}
        onclick={() => (showSessions = !showSessions)}><PanelLeft /></Button
      >
    {/if}
    <h1 class="text-base font-semibold">Copilot</h1>
    <div class="ml-auto flex items-center gap-1">
      <Button
        variant={focus ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={focus}
        title={focus ? "Exit focus" : "Focus"}
        onclick={() => (focus = !focus)}
      >
        {#if focus}<Minimize2 />Exit focus{:else}<Maximize2 />Focus{/if}
      </Button>
      <Button variant="ghost" size="sm" title="New window" onclick={popOut}>
        <ExternalLink />New window
      </Button>
    </div>
  </header>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    {#if !focus && showSessions}
      <Resizable.Pane
        id="errands"
        order={1}
        defaultSize={20}
        minSize={15}
        maxSize={30}
      >
        <SessionsSidebar
          sessions={copilot.sessions}
          {active}
          {waitingIds}
          onopen={open}
          onnew={newErrand}
        />
      </Resizable.Pane>
      <Resizable.Handle />
    {/if}

    <Resizable.Pane id="errand" order={2} defaultSize={80} minSize={40}>
      <section aria-label="Errand" class="solid-backing flex h-full flex-col">
        <div class="min-h-0 flex-1 overflow-auto">
          {#if startKind}
            <GuidedStart kind={startKind} />
          {:else if session && blocks.length}
            <ErrandHeader
              {session}
              {blocks}
              {parent}
              {busy}
              waiting={!!pending}
              onopen={(tab) => (drawer = tab)}
              onback={parent ? () => open(parent.id) : undefined}
            />
            <Thread
              {blocks}
              pendingBelow
              answers={active ? (copilot.answers[active] ?? {}) : {}}
              onanswer={(i, v) => active && copilot.answer(active, i, v)}
              onopenagent={openAgent}
              {onpanel}
              onartifact={(id) => {
                artifact = id;
                drawer = "preview";
              }}
              onagent={() => (drawer = "activity")}
              oncontinue={session.origin !== "Main"
                ? () => active && copilot.absorb(active)
                : undefined}
            />
          {:else}
            <HowDoI
              onstart={(k) => (startKind = k)}
              onask={(t) => (seed = t)}
              onopen={open}
            />
          {/if}
        </div>
        <div class="mx-auto w-full max-w-[46rem] px-8 pb-6">
          {#if pending && !writing && active}
            <PendingPanel
              block={pending.block}
              onanswer={(v) =>
                active && copilot.answer(active, pending.index, v)}
              onwrite={() => (writing = true)}
            />
          {:else}
            <Composer
              size="lg"
              {seed}
              {busy}
              refs={workbench.copilotRefs}
              onremoveref={(r) => workbench.removeRef(r)}
              onsend={send}
            />
          {/if}
        </div>
      </section>
    </Resizable.Pane>

    {#if !focus && drawer}
      <Resizable.Handle />
      <Resizable.Pane id="drawer" order={3} defaultSize={32} minSize={22}>
        <div class="relative h-full">
          <Button
            size="icon-sm"
            variant="ghost"
            class="absolute top-1.5 right-1.5 z-10"
            aria-label="Close the drawer"
            onclick={() => (drawer = null)}><X /></Button
          >
          <WorkArea
            bind:tab={() => drawer ?? "activity", (v) => (drawer = v)}
            bind:artifact
            session={active}
            onopenagent={(sessionId) => open(sessionId)}
          />
        </div>
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>
