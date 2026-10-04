<script lang="ts">
  /**
   * The main copilot (Copilot pass 2, 2026-10-04), modelled on T3 Code,
   * bb and DeepSeek Harness rather than invented: sessions on the left
   * (folding on their own), one shared session store with the Lab and
   * Portfolio copilots, sub-agents as child threads with a bar back to the
   * parent, questions and approvals that take over the message box, panels
   * the copilot builds as descriptions (keep, throw away or pin to the Lab),
   * and a right panel with Activity, Diff, Terminal, Browser and Preview.
   * DEMO: replies are scripted and labelled; the daemon streams real ones.
   * Params: ?session=, ?start=train|import|workflow, ?ask=, ?focus=1.
   */
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import PanelRight from "@lucide/svelte/icons/panel-right";
  import PanelLeft from "@lucide/svelte/icons/panel-left";
  import CornerUpLeft from "@lucide/svelte/icons/corner-up-left";
  import LoaderCircle from "@lucide/svelte/icons/loader-circle";
  import * as Resizable from "$lib/components/ui/resizable";
  import { Button } from "$lib/components/ui/button";
  import Composer from "$lib/workbench/Composer.svelte";
  import GuidedStart from "$lib/workbench/GuidedStart.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { addPane, pane } from "$lib/workbench/tiles/tiles";
  import { cn } from "$lib/utils";
  import Thread from "$lib/copilot/Thread.svelte";
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
  let showWork = $state(true);
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
  let workTab = $state("activity");
  let artifact = $state<string | null>(null);
  let writing = $state(false);

  const session = $derived(copilot.session(active));
  const parent = $derived(
    session?.parent ? copilot.session(session.parent) : undefined,
  );
  const blocks = $derived(copilot.blocks(active));
  const pending = $derived(copilot.pending(active));
  const busy = $derived(!!(active && copilot.busy[active]));
  const running = $derived(
    blocks
      .flatMap((b) => (b.kind === "agents" ? b.agents : []))
      .filter((a) => a.state === "running"),
  );

  function open(id: string) {
    active = id;
    startKind = null;
    writing = false;
  }
  function newSession() {
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
    else {
      workTab = "activity";
      showWork = true;
    }
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
        aria-label={showSessions ? "Hide sessions" : "Show sessions"}
        title={showSessions ? "Hide sessions" : "Show sessions"}
        aria-pressed={showSessions}
        onclick={() => (showSessions = !showSessions)}><PanelLeft /></Button
      >
    {/if}
    <h1 class="text-base font-semibold">Copilot</h1>
    {#if session}
      <span class="text-muted-foreground min-w-0 truncate text-sm"
        >{session.title}</span
      >
      {#if busy}
        <span
          class="bg-info/15 text-info flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs"
          ><LoaderCircle class="size-3 animate-spin" />Replying</span
        >
      {:else if session.status !== "done"}
        <span
          class={cn(
            "shrink-0 rounded-full px-2 py-0.5 text-xs",
            session.status === "running"
              ? "bg-info/15 text-info"
              : "bg-warning/15 text-warning",
          )}
          >{session.status === "running" ? "Running" : "Waiting for you"} · {session.age}</span
        >
      {/if}
    {/if}
    <div class="ml-auto flex items-center gap-1">
      <Button
        variant={focus ? "secondary" : "ghost"}
        size="sm"
        aria-pressed={focus}
        title={focus ? "Exit focus" : "Focus"}
        onclick={() => (focus = !focus)}
      >
        {#if focus}<Minimize2 /><span class="hidden xl:inline">Exit focus</span
          >{:else}<Maximize2 /><span class="hidden xl:inline">Focus</span>{/if}
      </Button>
      <Button variant="ghost" size="sm" title="New window" onclick={popOut}>
        <ExternalLink /><span class="hidden xl:inline">New window</span>
      </Button>
      {#if !focus}
        <Button
          variant={showWork ? "secondary" : "ghost"}
          size="icon-sm"
          aria-label="Activity and work area"
          title="Activity and work area"
          aria-pressed={showWork}
          onclick={() => (showWork = !showWork)}><PanelRight /></Button
        >
      {/if}
    </div>
  </header>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    {#if !focus && showSessions}
      <Resizable.Pane
        id="sessions"
        order={1}
        defaultSize={18}
        minSize={13}
        maxSize={28}
      >
        <SessionsSidebar
          sessions={copilot.sessions}
          {active}
          onopen={open}
          onnew={newSession}
        />
      </Resizable.Pane>
      <Resizable.Handle />
    {/if}

    <Resizable.Pane id="thread" order={2} defaultSize={52} minSize={30}>
      <section aria-label="Conversation" class="bg-panel flex h-full flex-col">
        {#if parent}
          <div
            class="bg-muted/40 flex shrink-0 items-center gap-2 border-b px-4 py-2 text-sm"
          >
            <span class="text-muted-foreground">Sub-agent of</span>
            <span class="truncate font-medium">{parent.title}</span>
            <span class="text-muted-foreground hidden md:inline"
              >· gets only its task, not the whole conversation</span
            >
            <Button
              size="sm"
              variant="outline"
              class="ml-auto"
              onclick={() => open(parent.id)}><CornerUpLeft />Back</Button
            >
          </div>
        {/if}
        <div class="min-h-0 flex-1 overflow-auto">
          {#if startKind}
            <GuidedStart kind={startKind} />
          {:else if blocks.length}
            <Thread
              {blocks}
              answers={active ? (copilot.answers[active] ?? {}) : {}}
              onanswer={(i, v) => active && copilot.answer(active, i, v)}
              onopenagent={openAgent}
              {onpanel}
              onartifact={(id) => {
                artifact = id;
                workTab = "preview";
                showWork = true;
              }}
              onagent={() => {
                workTab = "activity";
                showWork = true;
              }}
              oncontinue={session && session.origin !== "Main"
                ? () => active && copilot.absorb(active)
                : undefined}
            />
          {:else}
            <HowDoI
              onstart={(k) => (startKind = k)}
              onask={(t) => (seed = t)}
            />
          {/if}
        </div>
        <div class="mx-auto w-full max-w-4xl px-6 pb-5">
          {#if running.length && !pending}
            <p
              class="text-muted-foreground mb-2 flex items-center gap-1.5 text-[13px]"
            >
              <span class="bg-info remote-pulse size-1.5 rounded-full"></span>
              {running.length}
              {running.length === 1 ? "agent" : "agents"} working on {[
                ...new Set(running.map((a) => a.where)),
              ].join(", ")}
            </p>
          {/if}
          {#if pending && !writing && active}
            <PendingPanel
              block={pending.block}
              onanswer={(v) =>
                active && copilot.answer(active, pending.index, v)}
              onwrite={() => (writing = true)}
            />
          {:else}
            <Composer
              size={focus ? "lg" : "md"}
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

    {#if !focus && showWork}
      <Resizable.Handle />
      <Resizable.Pane id="work" order={3} defaultSize={30} minSize={20}>
        <WorkArea
          bind:tab={workTab}
          bind:artifact
          session={active}
          onopenagent={(sessionId) => open(sessionId)}
        />
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>
