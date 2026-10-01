<script lang="ts">
  import "@xyflow/svelte/dist/style.css";
  import {
    SvelteFlow,
    Background,
    Controls,
    MiniMap,
    MarkerType,
    type Node,
    type Edge,
  } from "@xyflow/svelte";
  import Save from "@lucide/svelte/icons/save";
  import CircleCheck from "@lucide/svelte/icons/circle-check";
  import Upload from "@lucide/svelte/icons/upload";
  import Play from "@lucide/svelte/icons/play";
  import Plus from "@lucide/svelte/icons/plus";
  import Search from "@lucide/svelte/icons/search";
  import MousePointerClick from "@lucide/svelte/icons/mouse-pointer-click";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Code from "@lucide/svelte/icons/code";
  import TriangleAlert from "@lucide/svelte/icons/triangle-alert";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tabs from "$lib/components/ui/tabs";
  import * as Tooltip from "$lib/components/ui/tooltip";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { Input } from "$lib/components/ui/input";
  import EmptyState from "$lib/workbench/EmptyState.svelte";
  import Composer from "$lib/workbench/Composer.svelte";
  import CodeEditor from "$lib/qmx/CodeEditor.svelte";
  import RunConsole from "$lib/qmx/RunConsole.svelte";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import StepNode from "$lib/demo/StepNode.svelte";
  import {
    DEMO_STEPS,
    PALETTE,
    demoNodes,
    demoEdges,
    type StepData,
  } from "$lib/demo/workflow";
  import { cn } from "$lib/utils";

  // Authoring (UI AUTHORING-AND-ML, J-UI-03): graph, inspector and code for
  // one draft. Graph layout is client-only; the draft id and revisions are
  // daemon-issued; drafts never run (only published versions do).
  const demo = workbench.demoMode;
  let nodes = $state.raw<Node[]>(demo ? demoNodes() : []);
  let edges = $state.raw<Edge[]>(demo ? demoEdges() : []);
  const nodeTypes = { step: StepNode };
  let selectedId = $state<string | null>(null);
  let side = $state<string>("inspect");
  let bottom = $state<string>("code");
  let paletteQuery = $state("");
  let dirty = $state(false);
  /** Local, unsaved code edits per step. */
  let codeEdits = $state<Record<string, string>>({});

  const selected = $derived(DEMO_STEPS.find((s) => s.id === selectedId));
  const selectedNode = $derived(nodes.find((n) => n.id === selectedId));
  const code = $derived(
    selectedId
      ? (codeEdits[selectedId] ??
          selected?.code ??
          "# New step: write its code here\n")
      : "",
  );

  const STEPS_LIFECYCLE = [
    {
      label: "Save draft",
      icon: Save,
      why: "Saving needs the daemon to issue a draft id.",
    },
    {
      label: "Validate",
      icon: CircleCheck,
      why: "Validation runs on a saved draft.",
    },
    {
      label: "Publish",
      icon: Upload,
      why: "Publishing turns a saved draft into a runnable version.",
    },
    {
      label: "Run",
      icon: Play,
      why: "Only published versions run. Drafts never run.",
    },
  ];

  function addStep(kind: StepData["kind"], label: string, detail: string) {
    const id = `new-${nodes.length + 1}`;
    nodes = [
      ...nodes,
      {
        id,
        type: "step",
        position: {
          x: 260 + (nodes.length % 4) * 40,
          y: 300 + (nodes.length % 3) * 30,
        },
        data: { kind, label, detail, status: "stale" } satisfies StepData,
      },
    ];
    selectedId = id;
    dirty = true;
  }

  const PROBLEMS = [
    {
      level: "warn",
      where: "Labels",
      text: "Losses outnumber wins at 2R / 1R (41% vs 38%).",
    },
    {
      level: "info",
      where: "Backtest",
      text: "Uses the default spread preset; consider the stress-spread preset too.",
    },
  ];
  const RUN_LOG = [
    "published version v6 · fp1:9c41…e2a0",
    "qmb walk-forward eurusd-h1-gbm --folds 12 --embargo 24",
    "fold  1/12 sharpe 1.21 · fold  2/12 sharpe 0.94 · …",
    "fold 12/12 sharpe 1.58",
    "CT-32 written · confirmation · ledger line 441",
  ];
</script>

<div class="flex h-full flex-col">
  {#if demo}
    <div
      class="bg-warning/15 flex h-7 shrink-0 items-center gap-2 px-3 text-xs"
    >
      <FlaskConical class="text-warning size-3.5" /> Demo workflow. A sample graph,
      not a saved draft; it cannot run.
    </div>
  {/if}
  <header class="flex h-11 shrink-0 items-center gap-3 border-b px-3">
    <span class="text-sm font-semibold">Authoring</span>
    <span class="text-sm">{demo ? "EURUSD H1 model" : "Untitled workflow"}</span
    >
    <div class="num flex items-center text-xs" aria-label="Versions">
      <span
        class="border-primary text-primary rounded-l-full border px-2.5 py-0.5"
        >draft v7{dirty ? " · unsaved" : ""}</span
      >
      <span class="text-muted-foreground border border-l-0 px-2.5 py-0.5"
        >published v6</span
      >
      <span
        class="text-success border-success/40 rounded-r-full border border-l-0 px-2.5 py-0.5"
        >v6 on paper</span
      >
    </div>
    <div class="ml-auto flex items-center gap-1.5">
      {#each STEPS_LIFECYCLE as s (s.label)}
        <Tooltip.Root>
          <Tooltip.Trigger>
            {#snippet child({ props })}
              <Button
                {...props}
                size="sm"
                variant={s.label === "Run" ? "default" : "outline"}
                aria-disabled="true"
                class="aria-disabled:pointer-events-auto aria-disabled:cursor-not-allowed aria-disabled:opacity-50"
                onclick={(e) => e.preventDefault()}
              >
                <s.icon />{s.label}
              </Button>
            {/snippet}
          </Tooltip.Trigger>
          <Tooltip.Content>{s.why}</Tooltip.Content>
        </Tooltip.Root>
      {/each}
    </div>
  </header>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={16} minSize={12} maxSize={26}>
      <aside
        aria-label="Steps"
        class="bg-panel flex h-full flex-col gap-2 overflow-auto p-2.5"
      >
        <div class="relative">
          <Search
            class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2"
          />
          <Input
            bind:value={paletteQuery}
            placeholder="Find a step"
            aria-label="Find a step"
            class="h-8 pl-8"
          />
        </div>
        {#each PALETTE as g (g.group)}
          {@const items = g.items.filter(
            (i) =>
              !paletteQuery ||
              i.label.toLowerCase().includes(paletteQuery.toLowerCase()),
          )}
          {#if items.length}
            <p class="panel-label px-1 pt-2">{g.group}</p>
            {#each items as it (it.label)}
              <button
                type="button"
                class="hover:bg-muted flex items-start gap-2 rounded-md px-2 py-1.5 text-left"
                onclick={() => addStep(g.group, it.label, it.detail)}
              >
                <Plus class="text-muted-foreground mt-0.5 size-3.5 shrink-0" />
                <span
                  ><span class="block text-sm">{it.label}</span><span
                    class="text-muted-foreground block text-xs"
                    >{it.detail}</span
                  ></span
                >
              </button>
            {/each}
          {/if}
        {/each}
        <p class="text-muted-foreground mt-auto px-1 pt-3 text-xs">
          The real list comes from the operations your installed apps publish.
        </p>
      </aside>
    </Resizable.Pane>
    <Resizable.Handle />

    <Resizable.Pane defaultSize={58} minSize={35}>
      <Resizable.PaneGroup direction="vertical">
        <Resizable.Pane defaultSize={66} minSize={30}>
          <div class="relative h-full" aria-label="Workflow graph">
            <SvelteFlow
              bind:nodes
              bind:edges
              {nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.15, maxZoom: 1.1 }}
              defaultEdgeOptions={{
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                  width: 16,
                  height: 16,
                },
              }}
              onnodeclick={({ node }) => {
                selectedId = node.id;
                side = "inspect";
              }}
              onpaneclick={() => (selectedId = null)}
              colorMode={workbench.theme === "paper" ? "light" : "dark"}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={22} />
              <Controls position="bottom-left" />
              <MiniMap
                width={160}
                height={100}
                bgColor="var(--panel)"
                maskColor="color-mix(in oklab, var(--background) 55%, transparent)"
                nodeColor="var(--muted-foreground)"
                position="bottom-right"
                pannable
                zoomable
                ariaLabel="Workflow overview"
              />
            </SvelteFlow>
            <div
              class="surface pointer-events-none absolute top-3 left-3 rounded-md px-2.5 py-1 text-xs"
            >
              Node editor · {nodes.length} steps · {edges.length} links
            </div>
            {#if nodes.length === 0}
              <div
                class="pointer-events-none absolute inset-0 flex items-center justify-center"
              >
                <EmptyState
                  icon={Plus}
                  title="Empty workflow"
                  description="Add steps from the list on the left, or ask the copilot to draft one."
                />
              </div>
            {/if}
          </div>
        </Resizable.Pane>
        <Resizable.Handle />
        <Resizable.Pane defaultSize={34} minSize={12}>
          <Tabs.Root
            bind:value={bottom}
            class="bg-panel flex h-full flex-col gap-0"
          >
            <div class="flex h-9 shrink-0 items-center gap-2 border-b px-2">
              <Tabs.List variant="line">
                <Tabs.Trigger value="code"><Code />Code</Tabs.Trigger>
                <Tabs.Trigger value="run"><Play />Run</Tabs.Trigger>
                <Tabs.Trigger value="problems"
                  ><TriangleAlert />Problems
                  <span class="num text-xs opacity-70">{PROBLEMS.length}</span
                  ></Tabs.Trigger
                >
              </Tabs.List>
              {#if bottom === "code" && selectedNode}
                <span class="text-muted-foreground ml-auto truncate text-xs"
                  >{(selectedNode.data as StepData).label} · draft v7</span
                >
              {/if}
            </div>
            <Tabs.Content value="code" class="min-h-0 flex-1">
              {#if selectedId}
                <CodeEditor
                  value={code}
                  label={`Code for ${(selectedNode?.data as StepData | undefined)?.label ?? "step"}`}
                  onchange={(v) => {
                    codeEdits[selectedId!] = v;
                    dirty = true;
                  }}
                />
              {:else}
                <EmptyState
                  class="h-full"
                  icon={MousePointerClick}
                  title="Select a step to see its code"
                />
              {/if}
            </Tabs.Content>
            <Tabs.Content value="run" class="min-h-0 flex-1 p-2">
              <RunConsole
                command="qmb walk-forward eurusd-h1-gbm (published v6)"
                lines={RUN_LOG}
                status="done"
              />
            </Tabs.Content>
            <Tabs.Content value="problems" class="min-h-0 flex-1 overflow-auto">
              <ul>
                {#each PROBLEMS as p (p.text)}
                  <li class="flex items-start gap-2 border-b px-3 py-2 text-sm">
                    <TriangleAlert
                      class={cn(
                        "mt-0.5 size-4 shrink-0",
                        p.level === "warn"
                          ? "text-warning"
                          : "text-muted-foreground",
                      )}
                    />
                    <span class="font-medium">{p.where}</span>
                    <span class="text-muted-foreground">{p.text}</span>
                  </li>
                {/each}
              </ul>
            </Tabs.Content>
          </Tabs.Root>
        </Resizable.Pane>
      </Resizable.PaneGroup>
    </Resizable.Pane>
    <Resizable.Handle />

    <Resizable.Pane defaultSize={26} minSize={18} maxSize={40}>
      <Tabs.Root bind:value={side} class="bg-panel flex h-full flex-col gap-0">
        <div class="flex h-9 shrink-0 items-center border-b px-2">
          <Tabs.List variant="line">
            <Tabs.Trigger value="inspect">Inspector</Tabs.Trigger>
            <Tabs.Trigger value="copilot">Copilot</Tabs.Trigger>
          </Tabs.List>
        </div>
        <Tabs.Content value="inspect" class="min-h-0 flex-1 overflow-auto">
          {#if selectedNode}
            {@const d = selectedNode.data as StepData}
            <div class="flex flex-col gap-3 p-3">
              <div>
                <p class="panel-label">{d.kind}</p>
                <p class="text-base font-semibold">{d.label}</p>
                <p class="text-muted-foreground text-sm">{d.detail}</p>
              </div>
              {#if selected}
                <div class="flex flex-col gap-2">
                  {#each selected.settings as [k, v] (k)}
                    <label class="flex flex-col gap-1 text-xs">
                      <span class="text-muted-foreground">{k}</span>
                      <Input
                        class="h-8"
                        value={v}
                        oninput={() => (dirty = true)}
                      />
                    </label>
                  {/each}
                </div>
              {/if}
              <Button
                variant="outline"
                size="sm"
                onclick={() => (bottom = "code")}><Code /> Edit code</Button
              >
              <div class="well rounded-md p-2.5 text-xs">
                <p class="font-medium">Last run (published v6)</p>
                <p class="text-muted-foreground">
                  {d.status === "warn"
                    ? "Finished with a warning; see Problems."
                    : d.status === "stale"
                      ? "Not run since this step was added."
                      : "Finished cleanly."}
                </p>
              </div>
            </div>
          {:else}
            <EmptyState
              class="h-full"
              icon={MousePointerClick}
              title="Nothing selected"
              description="Select a step to see its settings, code and last results."
            />
          {/if}
        </Tabs.Content>
        <Tabs.Content value="copilot" class="flex min-h-0 flex-1 flex-col">
          <div class="min-h-0 flex-1"></div>
          <div class="p-2.5">
            <Composer
              placeholder="Describe a change to this workflow…"
              refs={workbench.copilotRefs}
              onremoveref={(r) => workbench.removeRef(r)}
            />
          </div>
        </Tabs.Content>
      </Tabs.Root>
    </Resizable.Pane>
  </Resizable.PaneGroup>
</div>

<style>
  :global(.svelte-flow) {
    --xy-background-color: transparent;
    --xy-background-pattern-color: color-mix(
      in oklab,
      var(--muted-foreground) 35%,
      transparent
    );
    --xy-controls-button-background-color: var(--card);
    --xy-controls-button-color: var(--foreground);
    --xy-controls-button-border-color: var(--border);
    --xy-controls-box-shadow: 0 6px 18px rgb(0 0 0 / 0.3);
    --xy-edge-stroke: color-mix(in oklab, var(--foreground) 45%, transparent);
    --xy-edge-stroke-selected: var(--primary);
    --xy-edge-stroke-width: 1.6;
    --xy-handle-background-color: var(--primary);
    --xy-handle-border-color: var(--background);
    --xy-minimap-background-color: var(--panel);
    --xy-minimap-mask-background-color: color-mix(
      in oklab,
      var(--background) 60%,
      transparent
    );
    --xy-minimap-node-background-color: var(--muted-foreground);
  }
  :global(.svelte-flow__node-step) {
    background: transparent;
    border: 0;
    padding: 0;
  }
  :global(.svelte-flow__handle) {
    width: 9px;
    height: 9px;
  }
</style>
