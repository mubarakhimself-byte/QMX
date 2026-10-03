<script lang="ts">
  /**
   * The main copilot (Copilot pass, operator 2026-10-03). Sessions on the
   * left, grouped by where they started, with what is running or waiting
   * on top; any session can be continued here, where the copilot reaches
   * all of QMX. The conversation shows its work: plan, sub-agents, tools,
   * changes made elsewhere, artifacts, questions and permission cards. On
   * the right, Activity shows every agent and background job. The composer
   * sets how much it may do and what it may touch.
   * Params: ?session= opens one, ?start=train|import|workflow starts a
   * guided walk, ?ask= drafts a message, ?focus=1 opens focus mode.
   */
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Minimize2 from "@lucide/svelte/icons/minimize-2";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import PanelRight from "@lucide/svelte/icons/panel-right";
  import * as Resizable from "$lib/components/ui/resizable";
  import { Button } from "$lib/components/ui/button";
  import Composer from "$lib/workbench/Composer.svelte";
  import GuidedStart from "$lib/workbench/GuidedStart.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { cn } from "$lib/utils";
  import Thread from "$lib/copilot/Thread.svelte";
  import SessionsSidebar from "$lib/copilot/SessionsSidebar.svelte";
  import WorkArea from "$lib/copilot/WorkArea.svelte";
  import HowDoI from "$lib/copilot/HowDoI.svelte";
  import { SESSIONS, THREADS, type Session } from "$lib/copilot/demo";

  const params = page.url.searchParams;
  const demo = workbench.demoMode;
  let focus = $state(params.get("focus") === "1");
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
  let sessions = $state<Session[]>(demo ? [...SESSIONS] : []);
  const askedSession = params.get("session");
  let active = $state<string | null>(
    startParam || params.get("ask")
      ? null
      : askedSession && SESSIONS.some((s) => s.id === askedSession)
        ? askedSession
        : demo
          ? "weekend"
          : null,
  );
  let seed = $state(params.get("ask") ?? "");
  let workTab = $state("activity");
  let artifact = $state<string | null>(null);

  const session = $derived(sessions.find((s) => s.id === active));
  const blocks = $derived(active ? (THREADS[active] ?? []) : []);
  // Questions and permission cards you have answered, per session.
  let resolved = $state<Record<string, number>>({});
  const waitingOn = $derived(
    blocks.filter((b) => b.kind === "ask" || b.kind === "permission").length -
      (resolved[active ?? ""] ?? 0),
  );
  const agentsHere = $derived(
    blocks.flatMap((b) => (b.kind === "agents" ? b.agents : [])),
  );
  const running = $derived(agentsHere.filter((a) => a.state === "running"));

  function open(id: string) {
    active = id;
    startKind = null;
  }
  function newSession() {
    const s: Session = {
      id: `n-${Date.now().toString(36)}`,
      title: "New session",
      origin: "Main",
      status: "done",
      age: "Now",
    };
    sessions = [s, ...sessions];
    active = s.id;
    startKind = null;
    seed = "";
  }
  function continueHere() {
    if (!session) return;
    sessions = sessions.map((s) =>
      s.id === session.id ? { ...s, origin: "Main" } : s,
    );
    workbench.notify(
      `"${session.title}" now lives in the main copilot, with everything it can reach.`,
    );
  }
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" />
      Demo sessions. Sample plans, agents, tools and results; nothing ran.
    </div>
  {/if}
  <header class="flex h-12 shrink-0 items-center gap-3 border-b px-3">
    <h1 class="text-base font-semibold">Copilot</h1>
    {#if session}
      <span class="text-muted-foreground min-w-0 truncate text-sm"
        >{session.title}</span
      >
      {#if session.status !== "done"}
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

  {#key `${focus}-${showWork}`}
    <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
      {#if !focus}
        <Resizable.Pane defaultSize={18} minSize={13} maxSize={28}>
          <SessionsSidebar
            {sessions}
            {active}
            onopen={open}
            onnew={newSession}
          />
        </Resizable.Pane>
        <Resizable.Handle />
      {/if}

      <Resizable.Pane
        defaultSize={focus ? 100 : showWork ? 52 : 82}
        minSize={30}
      >
        <section
          aria-label="Conversation"
          class="bg-panel flex h-full flex-col"
        >
          <div class="min-h-0 flex-1 overflow-auto">
            {#if startKind}
              <GuidedStart kind={startKind} />
            {:else if blocks.length}
              <Thread
                {blocks}
                onartifact={(id) => {
                  artifact = id;
                  workTab = "preview";
                  showWork = true;
                }}
                onagent={() => {
                  workTab = "activity";
                  showWork = true;
                }}
                onresolve={() => {
                  if (active) resolved[active] = (resolved[active] ?? 0) + 1;
                }}
                oncontinue={session?.origin !== "Main"
                  ? continueHere
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
            {#if waitingOn || running.length}
              <p
                class="text-muted-foreground mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs"
              >
                {#if running.length}<span class="flex items-center gap-1.5"
                    ><span class="bg-info remote-pulse size-1.5 rounded-full"
                    ></span>{running.length}
                    {running.length === 1 ? "agent" : "agents"} working on {[
                      ...new Set(running.map((a) => a.where)),
                    ].join(", ")}</span
                  >{/if}
                {#if waitingOn}<span class="text-warning"
                    >{waitingOn} waiting for you above</span
                  >{/if}
              </p>
            {/if}
            <Composer
              size={focus ? "lg" : "md"}
              {seed}
              refs={workbench.copilotRefs}
              onremoveref={(r) => workbench.removeRef(r)}
            />
          </div>
        </section>
      </Resizable.Pane>

      {#if !focus && showWork}
        <Resizable.Handle />
        <Resizable.Pane defaultSize={30} minSize={20}>
          <WorkArea bind:tab={workTab} bind:artifact session={active} />
        </Resizable.Pane>
      {/if}
    </Resizable.PaneGroup>
  {/key}
</div>
